import os
import sys
import shutil
import subprocess
from setuptools import setup, Command

class BuildExeCommand(Command):
    description = "Install requirements and run PyInstaller"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("--- [1/3] Upgrading pip ---")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

        print("--- [2/3] Installing dependencies ---")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

        print("--- [3/3] Running PyInstaller ---")
        subprocess.check_call(["pyinstaller", "--clean", "main.spec"])
        print("\nBuild complete! Check the 'dist' folder.")

class CleanAllCommand(Command):
    description = "Clean build and dist folders"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        folders = ['build', 'dist']
        for folder in folders:
            if os.path.exists(folder):
                print(f"Removing {folder}...")
                shutil.rmtree(folder)
        print("Clean complete.")

setup(
    name="ezopenclaw",
    version="0.1.0",
    cmdclass={
        'build': BuildExeCommand,
        'clean': CleanAllCommand,
    },
)
