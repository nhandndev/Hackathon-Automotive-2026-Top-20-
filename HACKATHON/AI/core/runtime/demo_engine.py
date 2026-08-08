import sys
import copy
import time
import json
import logging
import winsound
import threading
import concurrent.futures
from pathlib import Path
import numpy as np
import yaml

from core.challenge1_road.predict_ttc import RoadTTCPredictor
from core.challenge2_driver.predict_state import DriverStatePredictor
from core.challenge3_fusion.risk_engine import (
    FleetSafeDrivingScorer,
    G_MS2,
    HARSH_ACCEL_G,
    HARSH_BRAKE_G,
    HARSH_LATERAL_G,
    NEAR_MISS_TTC_SEC,
    SPEEDING_TOLERANCE_KMH,
)
from core.decision_engine import DecisionEngine, DecisionPolicy, DecisionSnapshot
from integrations.se_client import SEApiClient
from core.runtime.adaptive_scheduler import (
    AdaptiveRuntimePolicy,
    HardwareProfile,
    AdaptiveInferenceScheduler,
    probe_torch_gpu
)
from core.challenge2_driver.model_contract import load_driver_artifact, validate_driver_artifact

logger = logging.getLogger("demo_engine")

class DemoInferenceEngine:
    def __init__(
        self,
        *,
        driver_model_path: Path,
        road_config_path: Path,
        driver_config_path: Path,
        decision_config_path: Path,
        runtime_config_path: Path,
        runtime_mode: str = "auto",
        road_interval_ms: int = 150,
        driver_interval_ms: int = 75,
        target_fps: float = 20.0,
        se_endpoint: str = None,
        driver_profile = None,
    ):
        self.driver_model_path = Path(driver_model_path).resolve()
        self.road_config_path = Path(road_config_path).resolve()
        self.driver_config_path = Path(driver_config_path).resolve()
        self.decision_config_path = Path(decision_config_path).resolve()
        self.runtime_config_path = Path(runtime_config_path).resolve()
        
        self.runtime_mode = runtime_mode
        self.road_interval_ms = road_interval_ms
        self.driver_interval_ms = driver_interval_ms
        self.target_fps = target_fps
        self.se_endpoint = se_endpoint
        self.driver_profile = driver_profile
        
        # Load and validate driver model contract
        artifact = load_driver_artifact(self.driver_model_path)
        validate_driver_artifact(artifact)
        
        # Probe hardware once
        self.hw = probe_torch_gpu()
        
        # Load configs
        self.road_cfg = yaml.safe_load(self.road_config_path.read_text(encoding="utf-8")) or {}
        self.driver_cfg = yaml.safe_load(self.driver_config_path.read_text(encoding="utf-8")) or {}
        self.rt_cfg = yaml.safe_load(self.runtime_config_path.read_text(encoding="utf-8")) if self.runtime_config_path.is_file() else {}
        self.decision_policy = DecisionPolicy.load(self.decision_config_path)
        
        # Set up cpu threads if needed
        det_cfg = self.road_cfg.get("detector", {})
        if det_cfg.get("device") in (None, "cpu"):
            try:
                import torch
                if not torch.cuda.is_available():
                    torch.set_num_threads(int(det_cfg.get("cpu_threads", 4)))
            except Exception:
                pass
        if self.hw.cuda_available and det_cfg.get("half", "auto") != False:
            det_cfg["half"] = True
            
        # Instantiate persistent predictors
        # Note: Road predictor needs calibration, we initialize it with valid mock parameters first (Section 69)
        mock_calibration = {
            "K_left": [[700.0, 0.0, 320.0], [0.0, 700.0, 240.0], [0.0, 0.0, 1.0]],
            "baseline_m": 0.54,
            "image_width": 640
        }
        self.road = RoadTTCPredictor(mock_calibration, self.road_cfg)
        
        self.driver = DriverStatePredictor(
            self.driver_model_path, self.driver_config_path, driver_profile=self.driver_profile
        )
        
        # Policy & Scheduler
        self.policy = AdaptiveRuntimePolicy(
            target_fps=self.target_fps,
            road_min_interval_ms=self.rt_cfg.get("road", {}).get("min_interval_ms", 50),
            road_max_interval_ms=self.rt_cfg.get("road", {}).get("max_interval_ms", 250),
            driver_min_interval_ms=self.rt_cfg.get("driver", {}).get("min_interval_ms", 50),
            driver_max_interval_ms=self.rt_cfg.get("driver", {}).get("max_interval_ms", 150),
        )
        self.scheduler = AdaptiveInferenceScheduler(self.policy, self.hw)
        self._apply_runtime_mode_intervals()
        
        # SE API Client
        import os
        self.client = SEApiClient(
            self.se_endpoint, 
            api_key=os.getenv("FPTU_SE_API_KEY"), 
            bearer_token=os.getenv("FPTU_SE_BEARER_TOKEN")
        ) if self.se_endpoint else None
        
        # Thread executors
        self.road_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.driver_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # State placeholders
        self.trip_id = None
        self.speed_limit = None
        self.fleet = None
        self.decision = None
        
        self.road_future = None
        self.driver_future = None
        
        self.cached_ttc = float("inf")
        self.cached_road_debug = {}
        self.cached_driver_out = self._get_default_driver_output()
        
        self.road_confirmed = False
        self.driver_confirmed = False
        self.last_snapshot = None
        self.live_started_ns = None
        self.last_present_time = None
        
    def _apply_runtime_mode_intervals(self):
        if self.runtime_mode == "fixed":
            self.scheduler.road.interval_ms = self.road_interval_ms
            self.scheduler.driver.interval_ms = self.driver_interval_ms
        elif self.runtime_mode == "full":
            self.scheduler.road.interval_ms = 0
            self.scheduler.driver.interval_ms = 0
        else:
            self.scheduler.road.interval_ms = 150
            self.scheduler.driver.interval_ms = 75

    def _get_default_driver_output(self):
        return {
            "state": "alert", "confidence": 0.0, "prediction_source": "startup",
            "quality_status": "warming_up", "face_detected": False, "left_eye_valid": False,
            "right_eye_valid": False, "monitoring_available": False, "alertness_score": 1.0,
            "eye_state": "unknown", "mouth_state": "unknown", "head_pose": "unknown",
            "rule_state": "unknown", "valid_window_ratio": 0.0, "features": {},
            "driver_state": "alert", "state_confidence": 0.0, "rule_driver_state": "unknown",
            "attention_state": "unknown", "fatigue_level": "unknown", "eye_event": "none",
            "mouth_event": "none", "head_state": "unknown", "observation": {}
        }

    def start_trip(self, trip_id: str, calibration: dict, metadata: dict, speed_limit_kmh: float = None, trip_dir: Path = None):
        self.trip_id = trip_id
        
        # Reset predictors and scorer
        # Update calibration parameters dynamically (Section 69)
        self.road.fx = float(calibration["K_left"][0][0])
        self.road.baseline = float(calibration["baseline_m"])
        self.road.image_width = int(calibration.get("image_width", 640))
        
        self.road.depth.fx = self.road.fx
        self.road.depth.baseline = self.road.baseline
        self.road.engine.fx = self.road.fx
        self.road.engine.image_width = self.road.image_width
        
        if trip_dir is not None:
            self.road.set_trip_dir(trip_dir)
            
        self.road.reset()
        
        # Reset driver predictors
        self.driver.reset()
        
        self.speed_limit = float(speed_limit_kmh) if speed_limit_kmh is not None else float(metadata.get("speed_limit_kmh", 80.0))
        self.fleet = FleetSafeDrivingScorer(self.speed_limit)
        
        self.decision = DecisionEngine(self.decision_policy, model_versions={"challenge2": self.driver_model_path.name})
        
        # Reset futures
        self.road_future = None
        self.driver_future = None
        
        self.cached_ttc = float("inf")
        self.cached_road_debug = {}
        self.cached_driver_out = self._get_default_driver_output()
        self.road_confirmed = False
        self.driver_confirmed = False
        self.last_snapshot = None
        
        self._apply_runtime_mode_intervals()
        
        if self.client:
            self.client.register_trips([{"trip_id": self.trip_id, "metadata": metadata}])
            
        self.live_started_ns = time.perf_counter_ns()
        self.last_present_time = time.perf_counter()
        
    def warmup_benchmark(self, dataset, frames_count: int = 8):
        """Warmup benchmarks before official replay starts"""
        warm_road_latencies = []
        warm_driver_latencies = []
        if self.runtime_mode == "auto":
            frames_iterator = dataset.iter_frames()
            for _ in range(frames_count):
                try:
                    frame = next(frames_iterator)
                    t0 = time.perf_counter()
                    self.road.predict_frame(
                        frame.frame_id, frame.timestamp, 
                        dataset.load_left(frame.frame_id), dataset.load_right(frame.frame_id), 
                        frame.speed_kmh
                    )
                    warm_road_latencies.append((time.perf_counter()-t0)*1000)
                    
                    t0 = time.perf_counter()
                    self.driver.predict_frame(
                        frame.frame_id, int(frame.timestamp*1000), 
                        dataset.load_driver(frame.frame_id)
                    )
                    warm_driver_latencies.append((time.perf_counter()-t0)*1000)
                except StopIteration:
                    break
            
            if warm_road_latencies and warm_driver_latencies:
                self.road.reset()
                self.driver.reset()
                # Choose initial cadence
                self.scheduler.choose_initial_cadence(
                    float(np.percentile(warm_road_latencies[2:], 95) if len(warm_road_latencies) > 2 else warm_road_latencies[-1]),
                    float(np.percentile(warm_driver_latencies[2:], 95) if len(warm_driver_latencies) > 2 else warm_driver_latencies[-1])
                )
                logger.info(f"[Startup] Warmup Done. C1: {self.scheduler.road.interval_ms}ms, C2: {self.scheduler.driver.interval_ms}ms")

    def process_display_frame(
        self,
        *,
        frame_id: int,
        timestamp: float,
        speed_kmh: float,
        longitudinal_accel: float,
        lateral_accel: float,
        cabin_frame: np.ndarray,
        left_frame: np.ndarray = None,
        right_frame: np.ndarray = None,
        live_timestamp_ms: int = None
    ) -> dict:
        now_s = time.perf_counter()
        frame_duration_ms = (now_s - self.last_present_time) * 1000.0
        self.last_present_time = now_s
        self.scheduler.on_display_frame(frame_duration_ms)
        
        if live_timestamp_ms is None:
            live_timestamp_ms = (time.perf_counter_ns() - self.live_started_ns) // 1_000_000
            
        # Check Road Future
        if self.road_future is not None and self.road_future.done():
            try:
                self.cached_ttc, self.cached_road_debug, _, latency = self.road_future.result()
                self.road_confirmed = True
                self.scheduler.on_road_complete(live_timestamp_ms, latency)
            except Exception as exc:
                logger.warning(f"Road inference warning: {exc}")
            finally:
                self.road_future = None
                
        # Submit Road Future
        should_submit_c1 = False
        if self.road_future is None and left_frame is not None and right_frame is not None:
            if self.runtime_mode == "full":
                should_submit_c1 = True
            else:
                should_submit_c1 = self.scheduler.should_submit_road(live_timestamp_ms)
                
        if should_submit_c1:
            r_left = left_frame.copy()
            r_right = right_frame.copy()
            def infer_road(f=frame_id, t=timestamp, s=speed_kmh, l=r_left, r=r_right):
                start = time.perf_counter()
                val = self.road.predict_frame(f, t, l, r, s)
                return val, copy.deepcopy(self.road.last_debug), f, (time.perf_counter()-start)*1000
            self.road_future = self.road_executor.submit(infer_road)
            self.scheduler.on_road_submit(live_timestamp_ms)
            
        # Check Driver Future
        if self.driver_future is not None and self.driver_future.done():
            try:
                self.cached_driver_out, _, _, latency = self.driver_future.result()
                self.driver_confirmed = True
                self.scheduler.on_driver_complete(live_timestamp_ms, latency)
            except Exception as exc:
                logger.warning(f"Driver inference warning: {exc}")
            finally:
                self.driver_future = None
                
        # Submit Driver Future
        should_submit_c2 = False
        if self.driver_future is None and cabin_frame is not None:
            if self.runtime_mode == "full":
                should_submit_c2 = True
            else:
                should_submit_c2 = self.scheduler.should_submit_driver(live_timestamp_ms)
                
        if should_submit_c2:
            c_ai = cabin_frame.copy()
            def infer_driver(f=frame_id, t=live_timestamp_ms, c=c_ai):
                start = time.perf_counter()
                val = self.driver.predict_frame(f, t, c)
                return val, f, t, (time.perf_counter()-start)*1000
            self.driver_future = self.driver_executor.submit(infer_driver)
            self.scheduler.on_driver_submit(live_timestamp_ms)
            
        # Dynamic YuNet interval
        yunet_target_ms = self.rt_cfg.get("face_detector", {}).get("target_period_ms", 500)
        desired_frames = max(1, round(yunet_target_ms / max(1, self.scheduler.driver.interval_ms)))
        self.driver.set_face_detector_interval_frames(desired_frames)
        
        # Adaptive Control update
        if self.runtime_mode == "auto":
            self.scheduler.apply_event_aware_boost(self.cached_ttc, self.cached_driver_out["state"])
            self.scheduler.update_control(live_timestamp_ms)
            
        # Fleet Scorer
        fleet_out = self.fleet.update(self.cached_ttc, speed_kmh, longitudinal_accel, lateral_accel)
        harsh_brake = longitudinal_accel < -HARSH_BRAKE_G * G_MS2
        harsh_accel = longitudinal_accel > HARSH_ACCEL_G * G_MS2
        harsh_corner = abs(lateral_accel) > HARSH_LATERAL_G * G_MS2
        speeding = speed_kmh > self.speed_limit + SPEEDING_TOLERANCE_KMH
        tailgating = np.isfinite(self.cached_ttc) and self.cached_ttc < 3.0
        
        # Build Snapshot
        features = self.cached_driver_out.get("features", {})
        self.last_snapshot = DecisionSnapshot(
            trip_id=self.trip_id, driver_id=self.driver_profile.driver_id if self.driver_profile else None,
            frame_id=frame_id, timestamp_ms=live_timestamp_ms,
            speed_kmh=speed_kmh, speed_limit_kmh=self.speed_limit, longitudinal_accel=longitudinal_accel,
            lateral_accel=lateral_accel, predicted_ttc_sec=self.cached_ttc, ttc_confirmed=self.road_confirmed,
            road_quality_status="valid" if self.road_confirmed else "warming_up",
            driver_state=str(self.cached_driver_out["state"]), driver_confidence=float(self.cached_driver_out["confidence"]),
            alertness_score=float(self.cached_driver_out["alertness_score"]), driver_quality_status=str(self.cached_driver_out["quality_status"]),
            face_detected=bool(self.cached_driver_out.get("face_detected", False)), left_eye_valid=bool(self.cached_driver_out.get("left_eye_valid", False)),
            right_eye_valid=bool(self.cached_driver_out.get("right_eye_valid", False)),
            monitoring_available=bool(self.cached_driver_out.get("monitoring_available", False)),
            valid_window_ratio=float(self.cached_driver_out.get("valid_window_ratio", 0.0)),
            continuous_eye_closure_ms=int(features.get("continuous_eye_closure_ms", 0) or 0),
            perclos_30s=float(features.get("perclos_30s", 0.0) or 0.0),
            off_road_duration_ms=int(features.get("off_road_duration_ms", 0) or 0),
            mouth_state=str(self.cached_driver_out.get("mouth_state", "normal")),
            mouth_open_duration_ms=int(features.get("mouth_open_duration_ms", 0) or 0),
            c3_risk_score=fleet_out.risk_score, c3_safe_score=fleet_out.safe_driving_score,
            c3_penalty_points=fleet_out.penalty_points,
            harsh_brake=bool(harsh_brake),
            harsh_accel=bool(harsh_accel),
            harsh_corner=bool(harsh_corner),
            speeding=bool(speeding),
            tailgating=bool(tailgating),
            harsh_brake_count=fleet_out.harsh_brake_count,
            harsh_accel_count=fleet_out.harsh_accel_count,
            harsh_corner_count=fleet_out.harsh_corner_count,
            near_miss_count=fleet_out.near_miss_count,
            speeding_pct_time=fleet_out.speeding_pct_time,
            tailgating_pct_time=0.0,
            avg_headway_sec=float(self.cached_ttc) if np.isfinite(self.cached_ttc) else 0.0,
        )
        
        # Decision Engine update
        events_fired = self.decision.update(self.last_snapshot)
        for ev in events_fired:
            threading.Thread(target=winsound.Beep, args=(1000, 500), daemon=True).start()
            if self.client:
                self.client.send(ev)
                
        return {
            "cached_ttc": self.cached_ttc,
            "cached_road_debug": self.cached_road_debug,
            "cached_driver_out": self.cached_driver_out,
            "fleet_out": fleet_out,
            "last_snapshot": self.last_snapshot,
            "events_fired": events_fired,
            "road_confirmed": self.road_confirmed,
            "live_timestamp_ms": live_timestamp_ms
        }
        
    def end_trip(self, event_stream=None) -> list:
        # Resolve pending futures
        if self.road_future is not None:
            try:
                self.road_future.result(timeout=1.0)
            except Exception:
                pass
            self.road_future = None
            
        if self.driver_future is not None:
            try:
                self.driver_future.result(timeout=1.0)
            except Exception:
                pass
            self.driver_future = None
            
        # Resolve final events
        events = []
        if self.decision and self.last_snapshot:
            events = self.decision.resolve_all(self.last_snapshot)
            for ev in events:
                if self.client:
                    self.client.send(ev)
                if event_stream:
                    event_stream.write(json.dumps(ev.transport_dict(), ensure_ascii=False) + "\n")
                    
        if self.client and self.trip_id:
            self.client.complete_trip(self.trip_id)
            
        return events
        
    def close(self):
        self.road_executor.shutdown(wait=True, cancel_futures=True)
        self.driver_executor.shutdown(wait=True, cancel_futures=True)
        if self.client:
            self.client.close()
        self.driver.close()
