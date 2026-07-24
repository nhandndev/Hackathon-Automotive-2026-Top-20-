"""
Frame-to-Image Synchronization & Alignment Validator.
Verifies 1-to-1 matching between CSV/JSON dataset rows and KITTI/Driver image files.
"""

import os
import sys
import json
import pandas as pd

def verify_alignment(dataset_dir: str, trip_id: str = "T01-Sample"):
    print("=" * 75)
    print(f"  🔍 KIỂM TRA ĐỒNG BỘ 1-1 GIỮA DỮ LIỆU FRAME VÀ ẢNH CAMERA: [{trip_id}]")
    print("=" * 75)

    kitti_dir = os.path.join(dataset_dir, "kitti", "image_2")
    driver_dir = os.path.join(dataset_dir, "driver")

    # 1. Check directory existence
    if not os.path.exists(kitti_dir):
        print(f"❌ Thư mục kitti/image_2 không tồn tại tại: {kitti_dir}")
        return False
    if not os.path.exists(driver_dir):
        print(f"❌ Thư mục driver không tồn tại tại: {driver_dir}")
        return False

    kitti_files = set(os.listdir(kitti_dir))
    driver_files = set(os.listdir(driver_dir))

    print(f"📸 Tìm thấy {len(kitti_files)} ảnh trong kitti/image_2/")
    print(f"👤 Tìm thấy {len(driver_files)} ảnh trong driver/\n")

    # 2. Read dataset frames
    json_path = os.path.join(dataset_dir, f"{trip_id}.json")
    csv_path = os.path.join(dataset_dir, "submissions", f"{trip_id}.csv")

    total_frames = 0
    frame_ids = []

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            frames = data.get("frames", data.get("data", []))
            total_frames = len(frames)
            frame_ids = [f.get("frame_id", idx) for idx, f in enumerate(frames)]
        print(f"📄 Nạp thành công file JSON {trip_id}.json ({total_frames} dòng/frames)")
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        total_frames = len(df)
        frame_ids = df["frame_id"].tolist()
        print(f"📄 Nạp thành công file CSV {trip_id}.csv ({total_frames} dòng/frames)")
    else:
        print(f"⚠️ Không tìm thấy file JSON hoặc CSV của {trip_id}")
        return False

    # 3. Check 1-to-1 matching for every frame
    missing_kitti = []
    missing_driver = []

    for fid in frame_ids:
        padded = f"{fid:06d}"
        kitti_name = f"{padded}.jpg"
        driver_name = f"frame_{padded}.jpg"

        if kitti_name not in kitti_files:
            missing_kitti.append(kitti_name)
        if driver_name not in driver_files:
            missing_driver.append(driver_name)

    # 4. Report Alignment Results
    print("-" * 75)
    if not missing_kitti and not missing_driver:
        print(f"✅ ĐỒNG BỘ NGUYÊN BẢN 100%! Cả {total_frames} frames đều có ảnh khớp 1-1 hoàn hảo:")
        print(f"   • KITTI Front Road Cam: {total_frames}/{total_frames} ảnh khớp chính xác.")
        print(f"   • Driver Cabin Cam:     {total_frames}/{total_frames} ảnh khớp chính xác.")
        print("=" * 75)
        return True
    else:
        print(f"⚠️ CẢNH BÁO LỆCH ẢNH:")
        if missing_kitti:
            print(f"   • Thiếu {len(missing_kitti)} ảnh KITTI (Ví dụ: {missing_kitti[:3]})")
        if missing_driver:
            print(f"   • Thiếu {len(missing_driver)} ảnh Driver (Ví dụ: {missing_driver[:3]})")
        print("=" * 75)
        return False

if __name__ == "__main__":
    dataset_path = "/Users/lilnhan/Downloads/Practice_Dataset/T01-Sample"
    verify_alignment(dataset_path, "T01-Sample")
