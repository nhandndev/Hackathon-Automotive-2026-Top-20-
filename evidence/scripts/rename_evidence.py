import os
import sys
import argparse
from datetime import datetime

def rename_evidence(file_path, evidence_id, short_description, commit_or_build="latest"):
    """
    Renames a file according to the evidence spec format:
    E-XX_yyyy-mm-dd_commit-or-build_short-description.ext
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
        
    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    ext = os.path.splitext(base_name)[1]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    clean_desc = short_description.replace(" ", "-").lower()
    
    import re
    if re.search(r'[:*?"<>|]', clean_desc):
        print("Error: Short description contains invalid filename characters.")
        return False
        
    new_name = f"{evidence_id}_{date_str}_{commit_or_build}_{clean_desc}{ext}"
    new_path = os.path.join(dir_name, new_name)
    
    try:
        os.rename(file_path, new_path)
        print(f"Successfully renamed:\n  From: {base_name}\n  To:   {new_name}")
        return True
    except Exception as e:
        print(f"Error renaming file: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename evidence file to standard format.")
    parser.add_argument("file_path", help="Path to the file to rename")
    parser.add_argument("evidence_id", help="Evidence ID (e.g., E-01)")
    parser.add_argument("description", help="Short description (use quotes if it contains spaces)")
    parser.add_argument("--commit", default="latest", help="Commit hash or build identifier (default: latest)")
    
    args = parser.parse_args()
    rename_evidence(args.file_path, args.evidence_id, args.description, args.commit)
