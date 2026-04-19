import os
import zipfile

def zip_project(output_filename='colab_project.zip'):
    print(f"Creating {output_filename}...")
    
    # Folders and files to ignore so the zip stays small
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'frontend', '.gemini'}
    ignore_exts = {'.pyc', '.zip'}

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Mutate dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in ignore_exts):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                
    print(f"Done! {output_filename} is ready to be uploaded to Colab.")

if __name__ == '__main__':
    zip_project()
