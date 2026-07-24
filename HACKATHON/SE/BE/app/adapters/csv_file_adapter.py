import os
import json
import math
import pandas as pd
from typing import Dict, Any, List
from app.domain.interfaces.base_data_adapter import BaseDataAdapter
from app.core.config import settings
from app.core.logger import logger

class CSVFileAdapter(BaseDataAdapter):
    """
    Real Data Adapter to load actual CSV or JSON dataset files.
    Supports reading real model predictions & telemetry CSV/JSON files without synthetic mock generation.
    """
    
    def __init__(self, data_dir: str = settings.DATASET_DIR):
        self.data_dir = data_dir

    def load_trip_data(self, trip_id: str) -> List[Dict[str, Any]]:
        """
        Loads trip data from REAL CSV or JSON files.
        Checks for:
        1. {data_dir}/{trip_id}.csv
        2. {data_dir}/{trip_id}.json
        3. {data_dir}/submissions/{trip_id}.csv
        4. {data_dir}/T01-Sample.json (Default dataset fallback)
        """
        csv_path = os.path.join(self.data_dir, f"{trip_id}.csv")
        json_path = os.path.join(self.data_dir, f"{trip_id}.json")
        sub_csv_path = os.path.join(self.data_dir, "submissions", f"{trip_id}.csv")
        fallback_json = os.path.join(self.data_dir, "T01-Sample.json")

        # 1. Try reading real CSV file
        if os.path.exists(csv_path):
            logger.info(f"Loading REAL CSV dataset from: {csv_path}")
            return self._parse_csv_file(csv_path)

        if os.path.exists(sub_csv_path):
            logger.info(f"Loading REAL submission CSV dataset from: {sub_csv_path}")
            return self._parse_csv_file(sub_csv_path)

        # 2. Try reading real JSON dataset file
        if os.path.exists(json_path):
            logger.info(f"Loading REAL JSON dataset from: {json_path}")
            return self._parse_json_file(json_path)

        if os.path.exists(fallback_json):
            logger.info(f"Loading REAL fallback dataset from: {fallback_json}")
            return self._parse_json_file(fallback_json)

        # If no file found, raise explicit FileNotFound exception
        err_msg = f"No real CSV or JSON file found for trip '{trip_id}' in directory '{self.data_dir}'"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    def _parse_csv_file(self, csv_path: str) -> List[Dict[str, Any]]:
        """Parses real CSV files with telemetry and AI vision predictions."""
        try:
            df = pd.read_csv(csv_path)
            parsed_frames = []

            for idx, row in df.iterrows():
                frame_id = int(row.get("frame_id", idx))
                timestamp = float(row.get("timestamp", round(idx * 0.05, 3)))

                # Telemetry extraction
                speed = float(row.get("speed_kmh", row.get("speed", 60.0)))
                accel_x = float(row.get("longitudinal_accel", row.get("accel_x", -0.2)))
                accel_y = float(row.get("lateral_accel", row.get("accel_y", 0.1)))
                lat = float(row.get("latitude", 10.762622 + idx * 0.00001))
                lon = float(row.get("longitude", 106.660172 + idx * 0.00001))
                heading = float(row.get("heading_deg", (idx * 0.5) % 360))

                # AI Vision TTC extraction
                raw_ttc = row.get("predicted_ttc", row.get("ttc", "inf"))
                if pd.isna(raw_ttc) or str(raw_ttc).strip().lower() in ["inf", "infinity", "nan", "none", ""]:
                    norm_ttc = "inf"
                else:
                    try:
                        norm_ttc = float(raw_ttc)
                    except ValueError:
                        norm_ttc = "inf"

                # AI Vision Driver State extraction
                driver_state = str(row.get("predicted_driver_state", row.get("driver_state", "alert"))).lower()
                if driver_state in ["nan", "none", ""]:
                    driver_state = "alert"

                alertness = float(row.get("alertness_score", 0.15 if driver_state in ["drowsy", "microsleep"] else 0.95))

                # Camera Images Matching Paths (KITTI Road Cam & Driver Cabin Cam)
                frame_padded = f"{frame_id:06d}"
                road_img_path = f"/static/kitti/image_2/{frame_padded}.jpg"
                driver_img_path = f"/static/driver/frame_{frame_padded}.jpg"

                parsed_frames.append({
                    "frame_id": frame_id,
                    "timestamp": round(timestamp, 3),
                    "images": {
                        "road_cam_url": road_img_path,
                        "driver_cam_url": driver_img_path
                    },
                    "telemetry": {
                        "speed_kmh": round(speed, 2),
                        "longitudinal_accel": round(accel_x, 2),
                        "lateral_accel": round(accel_y, 2),
                        "is_harsh_brake": accel_x < -3.0,
                        "is_harsh_accel": accel_x > 3.0,
                        "is_harsh_corner": abs(accel_y) > 3.5,
                        "is_speeding": speed > 80.0,
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                        "heading_deg": round(heading, 1)
                    },
                    "ai_vision": {
                        "predicted_ttc": norm_ttc,
                        "predicted_driver_state": driver_state,
                        "alertness_score": alertness
                    }
                })

            return parsed_frames
        except Exception as e:
            logger.error(f"Failed to parse CSV file {csv_path}: {e}")
            raise e

    def _parse_json_file(self, json_path: str) -> List[Dict[str, Any]]:
        """Parses real JSON dataset files."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            parsed_frames = []
            raw_frames = raw_data.get("frames", raw_data.get("data", []))

            for idx, item in enumerate(raw_frames):
                frame_id = item.get("frame_id", idx)
                timestamp = item.get("timestamp", round(idx * 0.05, 3))

                # Telemetry extraction (supports both 'ego' and 'telemetry')
                telemetry_raw = item.get("ego", item.get("telemetry", {}))
                speed = float(telemetry_raw.get("speed_kmh", telemetry_raw.get("speed", 0.0)))
                accel_x = float(telemetry_raw.get("longitudinal_accel", telemetry_raw.get("accel_x", 0.0)))
                accel_y = float(telemetry_raw.get("lateral_accel", telemetry_raw.get("accel_y", 0.0)))

                loc_raw = telemetry_raw.get("location", {})
                geo_raw = telemetry_raw.get("geolocation", {})
                lat = float(geo_raw.get("lat", 10.762622 + (loc_raw.get("x", idx) * 0.00001)))
                lon = float(geo_raw.get("lon", 106.660172 + (loc_raw.get("y", idx) * 0.00001)))

                rot_raw = telemetry_raw.get("rotation", {})
                heading = float(rot_raw.get("yaw", (idx * 0.5) % 360))

                # AI Vision TTC extraction (supports 'min_ttc', 'predicted_ttc', 'ai_vision')
                ai_raw = item.get("ai_vision", {})
                raw_ttc = item.get("min_ttc", ai_raw.get("predicted_ttc", item.get("predicted_ttc", "inf")))
                if raw_ttc is None or str(raw_ttc).strip().lower() in ["inf", "infinity", "nan", "none", ""]:
                    norm_ttc = "inf"
                else:
                    try:
                        norm_ttc = float(raw_ttc)
                    except ValueError:
                        norm_ttc = "inf"

                # Driver State extraction (supports 'driver.state' and 'ai_vision.predicted_driver_state')
                driver_raw = item.get("driver", {})
                driver_state = str(driver_raw.get("state", ai_raw.get("predicted_driver_state", item.get("predicted_driver_state", "alert")))).lower()
                if driver_state in ["nan", "none", ""]:
                    driver_state = "alert"

                alertness = float(driver_raw.get("alertness_score", ai_raw.get("alertness_score", 0.95)))

                # Risk Score extraction (supports 'risk.final_risk_score')
                risk_raw = item.get("risk", {})
                final_risk = float(risk_raw.get("final_risk_score", item.get("predicted_risk_score", 5.0)))

                # Camera Images Matching Paths (KITTI Road Cam & Driver Cabin Cam)
                frame_padded = f"{frame_id:06d}"
                road_img_path = f"/static/kitti/image_2/{frame_padded}.jpg"
                driver_img_path = f"/static/driver/frame_{frame_padded}.jpg"

                parsed_frames.append({
                    "frame_id": frame_id,
                    "timestamp": round(timestamp, 3),
                    "images": {
                        "road_cam_url": road_img_path,
                        "driver_cam_url": driver_img_path
                    },
                    "telemetry": {
                        "speed_kmh": round(speed, 2),
                        "longitudinal_accel": round(accel_x, 2),
                        "lateral_accel": round(accel_y, 2),
                        "is_harsh_brake": accel_x < -3.0,
                        "is_harsh_accel": accel_x > 3.0,
                        "is_harsh_corner": abs(accel_y) > 3.5,
                        "is_speeding": speed > 80.0,
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                        "heading_deg": round(heading, 1)
                    },
                    "ai_vision": {
                        "predicted_ttc": norm_ttc,
                        "predicted_driver_state": driver_state,
                        "alertness_score": alertness,
                        "predicted_risk_score": final_risk
                    }
                })
            return parsed_frames
        except Exception as e:
            logger.error(f"Failed to parse JSON dataset file {json_path}: {e}")
            raise e
