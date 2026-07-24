import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "FPTU DMS Vision Backend Engine"
    API_V1_STR: str = "/api"
    WS_V1_STR: str = "/ws"
    
    # CORS Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # FPS Replay Settings
    STREAM_FPS: int = 20
    FRAME_INTERVAL_SEC: float = 0.05  # dt = 50ms for 20 FPS
    
    # Dataset Paths
    DATASET_DIR: str = os.getenv("DATASET_DIR", "/Users/lilnhan/Downloads/Practice_Dataset/T01-Sample")
    OUTPUT_SUBMISSION_DIR: str = os.getenv("OUTPUT_SUBMISSION_DIR", "/Users/lilnhan/Downloads/Practice_Dataset/T01-Sample/submissions")

settings = Settings()

