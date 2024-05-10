from tkinter import filedialog, Tk

def get_file_path():
    Tk().withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("jsonAndIcal files", "*.json")])
    return file_path
