import os
import subprocess
from config import BASE_DIR
def run_python_script(script_path):
    subprocess.run([r'C:\Users\Home\PycharmProjects\pythonProject\.venv\Scripts\python.exe', script_path])

os.chdir(BASE_DIR)
run_python_script('createJSON/startJSON.py')
run_python_script('calUtils/startCreateCAL.py')
