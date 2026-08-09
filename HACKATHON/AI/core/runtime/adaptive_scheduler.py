import collections
import logging
import time
from dataclasses import dataclass, field
from collections import deque
from typing import Optional, Any
import numpy as np

@dataclass(frozen=True)
class HardwareProfile:
    cpu_logical_cores: int
    cpu_physical_cores: Optional[int]
    cuda_available: bool
    gpu_name: Optional[str]
    gpu_total_vram_mb: Optional[int]
    ort_cuda_available: bool

def probe_torch_gpu() -> HardwareProfile:
    import psutil
    logical = psutil.cpu_count(logical=True)
    physical = psutil.cpu_count(logical=False)
    
    cuda_available = False
    gpu_name = None
    vram = None
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            props = torch.cuda.get_device_properties(0)
            gpu_name = props.name
            vram = props.total_memory // (1024 * 1024)
    except Exception:
        pass
        
    ort_cuda = False
    try:
        import onnxruntime as ort
        if "CUDAExecutionProvider" in ort.get_available_providers():
            ort_cuda = True
    except Exception:
        pass
        
    return HardwareProfile(
        cpu_logical_cores=logical or 4,
        cpu_physical_cores=physical,
        cuda_available=cuda_available,
        gpu_name=gpu_name,
        gpu_total_vram_mb=vram,
        ort_cuda_available=ort_cuda,
    )

@dataclass
class TaskRuntimeStats:
    name: str
    last_submit_ms: float = -1.0
    last_complete_ms: float = -1.0
    interval_ms: float = 100.0
    in_flight: bool = False
    submitted: int = 0
    completed: int = 0
    dropped_due_busy: int = 0
    latency_ms: deque = field(default_factory=lambda: deque(maxlen=120))
    
    @property
    def p50_latency(self) -> float:
        if not self.latency_ms: return 0.0
        return float(np.percentile(self.latency_ms, 50))
        
    @property
    def p95_latency(self) -> float:
        if not self.latency_ms: return 0.0
        return float(np.percentile(self.latency_ms, 95))

@dataclass
class AdaptiveRuntimePolicy:
    target_fps: float = 20.0
    target_gpu_util: float = 0.82
    control_period_ms: int = 1000
    
    overload_min_display_fps: float = 19.0
    overload_max_frame_p95_ms: float = 55.0
    overload_consecutive_windows: int = 2
    
    headroom_min_display_fps: float = 19.7
    headroom_max_frame_p95_ms: float = 50.0
    headroom_consecutive_windows: int = 3
    
    road_min_interval_ms: int = 50
    road_max_interval_ms: int = 250
    road_step_ms: int = 25
    
    driver_min_interval_ms: int = 50
    driver_max_interval_ms: int = 150
    driver_step_ms: int = 25

class AdaptiveInferenceScheduler:
    def __init__(self, policy: AdaptiveRuntimePolicy, hardware: HardwareProfile):
        self.policy = policy
        self.hardware = hardware
        self.road = TaskRuntimeStats(name="road")
        self.driver = TaskRuntimeStats(name="driver")
        
        self.frame_durations_ms = deque(maxlen=60)
        self.last_control_ms = 0.0
        
        self.overload_counter = 0
        self.headroom_counter = 0

    def choose_initial_cadence(self, road_p95_ms: float, driver_p95_ms: float) -> None:
        best_cost = float('inf')
        best_r = self.policy.road_max_interval_ms
        best_d = self.policy.driver_max_interval_ms
        
        road_candidates = range(self.policy.road_min_interval_ms, self.policy.road_max_interval_ms + 1, self.policy.road_step_ms)
        driver_candidates = range(self.policy.driver_min_interval_ms, self.policy.driver_max_interval_ms + 1, self.policy.driver_step_ms)
        
        for r in road_candidates:
            for d in driver_candidates:
                est_load = (road_p95_ms / r) + (driver_p95_ms / d)
                if est_load <= 0.72:
                    cost = (1.0 * r / self.policy.road_max_interval_ms) + (1.5 * d / self.policy.driver_max_interval_ms)
                    if cost < best_cost:
                        best_cost = cost
                        best_r = r
                        best_d = d
                        
        self.road.interval_ms = float(best_r)
        self.driver.interval_ms = float(best_d)
        logging.info(f"[Scheduler] Initial cadence -> C1: {best_r}ms, C2: {best_d}ms (cost: {best_cost:.2f})")

    def reset_trip_state(self) -> None:
        """Reset per-trip clocks/counters while preserving chosen intervals."""
        road_interval = self.road.interval_ms
        driver_interval = self.driver.interval_ms
        self.road = TaskRuntimeStats(name="road", interval_ms=road_interval)
        self.driver = TaskRuntimeStats(name="driver", interval_ms=driver_interval)
        self.frame_durations_ms.clear()
        self.last_control_ms = 0.0
        self.overload_counter = 0
        self.headroom_counter = 0

    def should_submit_road(self, now_ms: float) -> bool:
        if self.road.in_flight:
            return False
        age = now_ms - self.road.last_complete_ms
        if age >= self.road.interval_ms:
            return True
        return False

    def should_submit_driver(self, now_ms: float) -> bool:
        if self.driver.in_flight:
            return False
        age = now_ms - self.driver.last_complete_ms
        if age >= self.driver.interval_ms:
            return True
        return False

    def on_road_submit(self, now_ms: float) -> None:
        self.road.last_submit_ms = now_ms
        self.road.in_flight = True
        self.road.submitted += 1

    def on_road_complete(self, now_ms: float, latency_ms: float) -> None:
        self.road.last_complete_ms = now_ms
        self.road.in_flight = False
        self.road.completed += 1
        self.road.latency_ms.append(latency_ms)

    def on_driver_submit(self, now_ms: float) -> None:
        self.driver.last_submit_ms = now_ms
        self.driver.in_flight = True
        self.driver.submitted += 1

    def on_driver_complete(self, now_ms: float, latency_ms: float) -> None:
        self.driver.last_complete_ms = now_ms
        self.driver.in_flight = False
        self.driver.completed += 1
        self.driver.latency_ms.append(latency_ms)

    def on_display_frame(self, frame_duration_ms: float) -> None:
        if frame_duration_ms > 0:
            self.frame_durations_ms.append(frame_duration_ms)

    def get_display_fps(self) -> float:
        if not self.frame_durations_ms:
            return self.policy.target_fps
        return 1000.0 / float(np.median(self.frame_durations_ms))

    def get_frame_p95_ms(self) -> float:
        if not self.frame_durations_ms:
            return 1000.0 / self.policy.target_fps
        return float(np.percentile(self.frame_durations_ms, 95))

    def apply_event_aware_boost(self, ttc: float, driver_state: str) -> None:
        if ttc < 3.0:
            self.road.interval_ms = max(self.policy.road_min_interval_ms, self.road.interval_ms - self.policy.road_step_ms)
        if driver_state in {"drowsy", "microsleep", "distracted"}:
            self.driver.interval_ms = max(self.policy.driver_min_interval_ms, self.driver.interval_ms - self.policy.driver_step_ms)

    def update_control(self, now_ms: float) -> None:
        if now_ms - self.last_control_ms < self.policy.control_period_ms:
            return
            
        self.last_control_ms = now_ms
        fps = self.get_display_fps()
        p95 = self.get_frame_p95_ms()
        
        is_overload = (fps < self.policy.overload_min_display_fps) or (p95 > self.policy.overload_max_frame_p95_ms)
        is_headroom = (fps >= self.policy.headroom_min_display_fps) and (p95 <= self.policy.headroom_max_frame_p95_ms)

        if is_overload:
            self.overload_counter += 1
            self.headroom_counter = 0
            if self.overload_counter >= self.policy.overload_consecutive_windows:
                r_pressure = self.road.p95_latency / max(1, self.road.interval_ms)
                d_pressure = self.driver.p95_latency / max(1, self.driver.interval_ms)
                
                if r_pressure > d_pressure:
                    self.road.interval_ms = min(self.policy.road_max_interval_ms, self.road.interval_ms + self.policy.road_step_ms)
                else:
                    self.driver.interval_ms = min(self.policy.driver_max_interval_ms, self.driver.interval_ms + self.policy.driver_step_ms)
                self.overload_counter = 0
        elif is_headroom:
            self.headroom_counter += 1
            self.overload_counter = 0
            if self.headroom_counter >= self.policy.headroom_consecutive_windows:
                # favor driver reduction over road reduction
                if self.driver.interval_ms > self.policy.driver_min_interval_ms:
                    self.driver.interval_ms -= self.policy.driver_step_ms
                elif self.road.interval_ms > self.policy.road_min_interval_ms:
                    self.road.interval_ms -= self.policy.road_step_ms
                self.headroom_counter = 0
        else:
            self.overload_counter = 0
            self.headroom_counter = 0

    def snapshot(self) -> dict:
        return {
            "fps": self.get_display_fps(),
            "frame_p95": self.get_frame_p95_ms(),
            "road": {
                "interval_ms": self.road.interval_ms,
                "p50_ms": self.road.p50_latency,
                "p95_ms": self.road.p95_latency,
                "in_flight": self.road.in_flight
            },
            "driver": {
                "interval_ms": self.driver.interval_ms,
                "p50_ms": self.driver.p50_latency,
                "p95_ms": self.driver.p95_latency,
                "in_flight": self.driver.in_flight
            }
        }
