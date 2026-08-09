import os
import csv
import ast
import re

def parse_python_file(filepath):
    functions = []
    classes = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read(), filename=filepath)
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                functions.append(item.name)
            elif isinstance(item, ast.ClassDef):
                classes.append(item.name)
    except Exception:
        pass
    return functions, classes

def parse_ts_file(filepath):
    exports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            exports.extend(re.findall(r'export\s+(?:async\s+)?function\s+([A-Za-z0-9_]+)', content))
            exports.extend(re.findall(r'export\s+const\s+([A-Za-z0-9_]+)\s*=', content))
            exports.extend(re.findall(r'export\s+class\s+([A-Za-z0-9_]+)', content))
            if re.search(r'export\s+default\s+', content):
                exports.append('default_export')
    except Exception:
        pass
    return list(set(exports)), []

def map_directory(root_dir, writer, module_prefix=""):
    for root, _, files in os.walk(root_dir):
        if 'node_modules' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if not file.endswith(('.py', '.js', '.ts', '.go')):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, root_dir)
            module_name = f"{module_prefix}/{os.path.dirname(rel_path)}".strip('/')
            if not module_name:
                module_name = module_prefix
                
            functions, classes = [], []
            if file.endswith('.py'):
                functions, classes = parse_python_file(filepath)
            elif file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                functions, classes = parse_ts_file(filepath)
                
            funcs_str = ", ".join(functions + classes) if (functions or classes) else "N/A (or not parsed)"
            
            writer.writerow([module_name, file, funcs_str])

if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), "..", "02_architecture", "source_map.csv")
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module', 'File', 'Functions/Classes'])
        
        ai_dir = os.path.join(repo_root, "HACKATHON", "AI")
        se_dir = os.path.join(repo_root, "HACKATHON", "SE")
        
        if os.path.exists(ai_dir):
            map_directory(ai_dir, writer, "AI")
        if os.path.exists(se_dir):
            map_directory(se_dir, writer, "SE")
            
    print(f"Architecture map exported to {output_file}")
