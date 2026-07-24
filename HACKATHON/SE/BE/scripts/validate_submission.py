import os
import glob
import pandas as pd

def validate_submission_files(submission_dir: str):
    print("=" * 60)
    print("  SUBMISSION CSV VALIDATION REPORT — BTC CRITERIA CHECK")
    print("=" * 60)

    csv_files = glob.glob(os.path.join(submission_dir, "*.csv"))
    if not csv_files:
        print(f"❌ ERROR: No CSV files found in {submission_dir}")
        return False

    expected_cols = ["frame_id", "timestamp", "predicted_ttc", "predicted_driver_state", "predicted_risk_score"]
    valid_states = {"alert", "drowsy", "yawning", "distracted", "microsleep"}

    total_files = len(csv_files)
    passed_files = 0

    for csv_file in sorted(csv_files):
        fname = os.path.basename(csv_file)
        try:
            df = pd.read_csv(csv_file)
            
            # Check 1: Row count
            if len(df) != 1800:
                print(f"❌ [{fname}] Failed: Expected 1800 rows, got {len(df)}")
                continue

            # Check 2: Column names and order
            if list(df.columns) != expected_cols:
                print(f"❌ [{fname}] Failed: Columns mismatch. Got {list(df.columns)}")
                continue

            # Check 3: Missing NaN values
            if df.isna().sum().sum() > 0:
                print(f"❌ [{fname}] Failed: Contains NaN values")
                continue

            # Check 4: Valid driver state enum
            invalid_states = set(df["predicted_driver_state"].str.lower()) - valid_states
            if invalid_states:
                print(f"❌ [{fname}] Failed: Invalid driver states found {invalid_states}")
                continue

            # Check 5: Risk score bounds (0.0 to 100.0)
            risk_min = df["predicted_risk_score"].min()
            risk_max = df["predicted_risk_score"].max()
            if risk_min < 0.0 or risk_max > 100.0:
                print(f"❌ [{fname}] Failed: Risk score out of bounds [{risk_min}, {risk_max}]")
                continue

            print(f"✅ [{fname}] PASSED: 1800x5 | 0 NaNs | States OK | Risk Range [{risk_min}, {risk_max}]")
            passed_files += 1

        except Exception as e:
            print(f"❌ [{fname}] Exception: {e}")

    print("-" * 60)
    print(f"TOTAL RESULT: {passed_files}/{total_files} files passed 100% BTC criteria.")
    print("=" * 60)
    return passed_files == total_files

if __name__ == "__main__":
    sub_dir = os.path.join(os.path.dirname(__file__), "..", "..", "submissions")
    validate_submission_files(sub_dir)
