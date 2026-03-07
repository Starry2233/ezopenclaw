"""
MsiExec Python Libary by Starry2233

"""

from typing import List
import subprocess
import os
import sys


class MsiExec(object):
    def __init__(self):
        self.packages: List[str] = []

    def _install_packages_cmd(self, *args) -> List[subprocess.CompletedProcess]:
        completed = []
        cli_args = [str(arg) for arg in args if arg is not None and str(arg) != ""]
        for package in self.packages:
            process = subprocess.Popen(
                ["msiexec.exe", "/i", package, *cli_args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            result = subprocess.CompletedProcess(
                args=process.args,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )
            completed.append(result)
        self.packages = []
        return completed

    def install_msi_package(
            self, 
            package_path: str,
            *args
        ) -> subprocess.CompletedProcess:
        if not os.path.exists(package_path):
            raise FileNotFoundError(f"MSI package {package_path} not found")
        self.packages.append(package_path)
        return self._install_packages_cmd(*args).__getitem__(0)
    
    def install_msi_packages(
        self,
        packages_path: str,
        *args
    ) -> subprocess.CompletedProcess:
        if not os.path.exists(packages_path):
            raise FileNotFoundError(f"MSI packages path {packages_path} not found")
        for file in os.listdir(packages_path):
            self.packages.append(
                os.path.join(
                    packages_path,
                    file
                )
            )

        return self._install_packages_cmd(*args)
    
