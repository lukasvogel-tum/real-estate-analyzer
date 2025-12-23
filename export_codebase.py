import os

def export_codebase():
    output_filename = "codebase.txt"
    # Get the directory where this script is located
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Directories to exclude to keep the file small and relevant
    ignore_dirs = {
        "__pycache__", "venv", ".venv", "env", ".git", ".idea", 
        "node_modules", "dist", "build", "lancedb", "projects"
    }
    
    with open(output_filename, "w", encoding="utf-8") as out_f:
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Only include .py files and exclude this script itself
                if file.endswith(".py") and file != os.path.basename(__file__):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as in_f:
                            content = in_f.read()
                            
                        out_f.write(f"--- {rel_path} ---\n")
                        out_f.write(content.strip()) # Strip to remove excess whitespace
                        out_f.write("\n\n")
                    except Exception as e:
                        print(f"Could not read {rel_path}: {e}")

    print(f"Exported codebase to {os.path.join(root_dir, output_filename)}")

if __name__ == "__main__":
    export_codebase()