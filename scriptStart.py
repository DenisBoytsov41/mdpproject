import os
import subprocess
from config import BASE_DIR

def run_python_script(script_path):
    python_exe_path = os.path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe')
    full_script_path = os.path.join(BASE_DIR, script_path)
    subprocess.run([python_exe_path, full_script_path], check=True)

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    run_python_script('createJSON/startJSON.py')
    run_python_script('calUtils/startCreateCAL.py')
