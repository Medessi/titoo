from cx_Freeze import setup, Executable

build_exe_options = {
    "include_files": ["assets"],
    "excludes": ["tkinter", "unittest", "email", "xmlrpc", "sqlite3", "PyQt5", "PySide2", "PySide6"]
}

setup(
    name="TITO",
    version="1.0",
    description="Organisateur de fichiers",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base="Win32GUI", target_name="TITO.exe")]
)
