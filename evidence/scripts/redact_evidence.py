import os
import sys
import re
import argparse

# Basic patterns for redacting sensitive info
PATTERNS = {
    'API_KEY': r'(?i)(api[_-]?key[\s:=]+)(["\']?[a-zA-Z0-9_\-]{20,}["\']?)',
    'TOKEN': r'(?i)(token[\s:=]+)(["\']?eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+["\']?|["\']?[a-zA-Z0-9_\-]{20,}["\']?)',
    'PASSWORD': r'(?i)(password|passwd|pwd)[\s:=]+(["\']?[^"\',\s]+["\']?)',
    'SECRET': r'(?i)(secret)[\s:=]+(["\']?[^"\',\s]+["\']?)',
    'EMAIL': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
}

def redact_file(file_path, dry_run=False):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        replacements_made = 0
        
        for name, pattern in PATTERNS.items():
            if name in ['API_KEY', 'TOKEN', 'PASSWORD', 'SECRET']:
                # Replace the matched group 2 with [REDACTED] while keeping group 1
                def replace_func(match):
                    return f"{match.group(1)}[REDACTED_{name}]"
                content, count = re.subn(pattern, replace_func, content)
                replacements_made += count
            elif name == 'EMAIL':
                content, count = re.subn(pattern, '[REDACTED_EMAIL]', content)
                replacements_made += count
                
        if replacements_made > 0:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Redacted {replacements_made} items in {file_path}")
            else:
                print(f"[DRY-RUN] Would redact {replacements_made} items in {file_path}")
        else:
            print(f"No sensitive info found in {file_path}")
            
        return True
    except UnicodeDecodeError:
        print(f"WARNING: SKIPPED {file_path} — extension/encoding not supported, redaction NOT applied.")
        return False
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def redact_directory(dir_path, dry_run=False):
    exclude_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build'}
    for root, dirnames, files in os.walk(dir_path):
        # Modify dirnames in-place to prune the search tree
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for file in files:
            # Skip this script itself and hidden files
            if file == "redact_evidence.py" or file.startswith("."):
                continue
                
            file_path = os.path.join(root, file)
            # Try redacting all files; redact_file will skip gracefully if it's binary
            redact_file(file_path, dry_run)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redact sensitive information from text files.")
    parser.add_argument("path", help="File or directory path to process")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be redacted without changing files")
    
    args = parser.parse_args()
    
    if os.path.isdir(args.path):
        redact_directory(args.path, args.dry_run)
    elif os.path.isfile(args.path):
        redact_file(args.path, args.dry_run)
    else:
        print(f"Error: Invalid path {args.path}")
