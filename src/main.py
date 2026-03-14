""" EzOpenClaw by Starry2233 """


from msiexec import MsiExec
from colorama import Fore, init
from pathlib import PurePath
from typing import Any, Optional, Union
import os
import sys
import subprocess
import requests
import getpass
import json
import ctypes
try: import winreg
except (ModuleNotFoundError, ImportError): ...
import shutil
import pylnk3
import platform
import stat
import tempfile


INFOX = r"""
 _______    ________   ________   ________   _______    ________    ________   ___        ________   ___       __      
|\  ___ \  |\_____  \ |\   __  \ |\   __  \ |\  ___ \  |\   ___  \ |\   ____\ |\  \      |\   __  \ |\  \     |\  \    
\ \   __/|  \|___/  /|\ \  \|\  \\ \  \|\  \\ \   __/| \ \  \\ \  \\ \  \___| \ \  \     \ \  \|\  \\ \  \    \ \  \   
 \ \  \_|/__    /  / / \ \  \\\  \\ \   ____\\ \  \_|/__\ \  \\ \  \\ \  \     \ \  \     \ \   __  \\ \  \  __\ \  \  
  \ \  \_|\ \  /  /_/__ \ \  \\\  \\ \  \___| \ \  \_|\ \\ \  \\ \  \\ \  \____ \ \  \____ \ \  \ \  \\ \  \|\__\_\  \ 
   \ \_______\|\________\\ \_______\\ \__\     \ \_______\\ \__\\ \__\\ \_______\\ \_______\\ \__\ \__\\ \____________\
    \|_______| \|_______| \|_______| \|__|      \|_______| \|__| \|__| \|_______| \|_______| \|__|\|__| \|____________|   Standalone Installer
    
    by Starry2233
                                                                                                                                                                                                                                             
"""   

INFO = Fore.LIGHTBLUE_EX + "[INFO]" + Fore.RESET
WARN = Fore.LIGHTYELLOW_EX + "[WARN]" + Fore.RESET
ERROR = Fore.RED + "[ERROR]" + Fore.RESET
SUCCESS = Fore.LIGHTGREEN_EX + "[SUCCESS]" + Fore.RESET


class PlatformDetector:
    """Platform detection utility"""
    
    @staticmethod
    def is_windows() -> bool:
        return sys.platform.startswith('win')
    
    @staticmethod
    def is_linux() -> bool:
        return sys.platform.startswith('linux')
    
    @staticmethod
    def is_macos() -> bool:
        return sys.platform.startswith('darwin')
    
    @staticmethod
    def get_platform_name() -> str:
        if PlatformDetector.is_windows():
            return "Windows"
        elif PlatformDetector.is_linux():
            return "Linux"
        elif PlatformDetector.is_macos():
            return "macOS"
        else:
            return "Unknown"


class OpenClawInstall(object):
    def __init__(self, target_path: str):
        self.target_path = target_path
        self.nvm = False
        self.install_mode = 2
        self.platform = PlatformDetector.get_platform_name()
        self.temp_dir = os.path.join(target_path, ".temp")
        
        # Create temp directory
        os.makedirs(self.temp_dir, exist_ok=True)

    @staticmethod
    def _refresh_env():
        """Refresh environment variables (Windows only)"""
        try:
            if PlatformDetector.is_windows():
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
                    sys_path, _ = winreg.QueryValueEx(k, "Path")
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                    user_path, _ = winreg.QueryValueEx(k, "Path")
                
                os.environ["PATH"] = sys_path + os.pathsep + user_path
                
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x02, 1000, ctypes.byref(ctypes.c_long()))
                return True
            else:
                # For Linux, just reload PATH from current environment
                return True
        except Exception as e:
            print(f"{WARN}Failed to refresh environment: {e}")
            return False

    @staticmethod
    def _install_msi_package(package: str, target: str) -> subprocess.CompletedProcess:
        """Install MSI package (Windows only)"""
        if not PlatformDetector.is_windows():
            raise NotImplementedError("MSI installation is Windows-only")
        return MsiExec().install_msi_package(
            package,
            f'INSTALLDIR={target}',
            f'TARGETDIR={target}',
            f'APPDIR={target}',
            f'APPLICATIONFOLDER={target}',
            'REBOOT=Suppress',
            '/qn',
            '/norestart',
        )

    @staticmethod
    def _detect_executable(name) -> Optional[str]:
        """Detect executable in PATH"""
        try:
            if PlatformDetector.is_windows():
                result = subprocess.run(
                    ["cmd.exe", "/c", "where", name],
                    shell=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                ).stdout
            else:
                result = subprocess.run(
                    ["which", name],
                    shell=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                ).stdout
            
            if result.strip() == "":
                return None
            return result.strip()
        except Exception:
            return None

    @staticmethod
    def _get_config(key) -> Any:
        """Get configuration value"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                json_text: dict = json.load(f)
                result = json_text.get(key, None)
                return result
        except FileNotFoundError:
            print(f"{WARN}config.json not found, using defaults")
            return None

    @staticmethod
    def _download_file(url, dst):
        """Download file with progress indicator"""
        chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dst, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        status = f"{percent:.1f}%"
                    else:
                        status = f"{downloaded / 1024:.1f} KB"
                    
                    sys.stdout.write(f"\r{chars[idx % len(chars)]} Downloading {status}")
                    sys.stdout.flush()
                    idx += 1

        sys.stdout.write(f"\r{SUCCESS}Downloaded {dst}\n")
        sys.stdout.flush()

    @staticmethod
    def add_to_startup(app_name, command) -> Union[bool, Exception]:
        """Add to startup (platform-specific)"""
        try:
            if PlatformDetector.is_windows():
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"  
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
                return True
            elif PlatformDetector.is_linux():
                # Create autostart desktop file for Linux
                autostart_dir = os.path.join(os.path.expanduser("~"), ".config", "autostart")
                os.makedirs(autostart_dir, exist_ok=True)
                
                desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")
                with open(desktop_file, "w") as f:
                    f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name={app_name}
Exec={command}
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
""")
                # Make executable
                os.chmod(desktop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                return True
            else:
                return NotImplementedError("Startup integration not implemented for this platform")
        except Exception as e:
            return e
        
    @staticmethod
    def create_start_menu_pylnk(app_group_name, app_name, target_exe, args=""):
        """Create start menu shortcut (Windows only)"""
        if not PlatformDetector.is_windows():
            return
        
        base_path = os.path.join(
            os.environ['APPDATA'], 
            'Microsoft', 'Windows', 'Start Menu', 'Programs'
        )
        
        app_folder = os.path.join(base_path, app_group_name)
        if not os.path.exists(app_folder):
            os.makedirs(app_folder)
        
        lnk_path = os.path.join(app_folder, f"{app_name}.lnk")
        
        lnk = pylnk3.for_file(target_exe)
        
        lnk.arguments = args
        lnk.work_dir = os.path.dirname(target_exe)
        lnk.description = f"Launch {app_name}"
        
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        lnk.icon = os.path.join(system_root, "System32", "imageres.dll")
        lnk.icon_index = 67

        lnk.link_flags.RunAsUser = True 
        
        lnk.save(lnk_path)
        
    def install_nvm_legacy(self) -> bool:
        """Install NVM on Windows (legacy method)"""
        if not PlatformDetector.is_windows():
            return False
            
        url = self._get_config("nvm_url")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        self._download_file(url, os.path.join(self.temp_dir, "nvm-setup.exe"))
        print(f"{INFO}Download successful, now starting install NVM... {Fore.LIGHTBLACK_EX}[下载成功, 开始安装NVM...]{Fore.RESET}")
        
        result = subprocess.run(
            [
                os.path.join(self.temp_dir, "nvm-setup.exe"),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/FORCE",
                "/SP-",
                f"/DIR={os.path.join(self.target_path, 'nvm')}"
            ],
            shell=False,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            print(f"{ERROR}Failed to install NVM (安装NVM失败): The process returned non-zero code {str(result.returncode)}, STDERR:")
            print(result.stderr)
            return False
        print(f"{SUCCESS}NVM installed successfully (NVM安装成功)")
        return True
    
    def install_nvm_winget(self) -> bool:
        """Install NVM on Windows using WinGet"""
        if not PlatformDetector.is_windows():
            return False
            
        if not os.path.exists(os.path.join(self.target_path, "nvm")):
            os.makedirs(os.path.join(self.target_path, "nvm"))
        print(f"{INFO}Checking WinGet... {Fore.LIGHTBLACK_EX}[正在检查WinGet...]{Fore.RESET}")
        winget_location = subprocess.run(["cmd.exe", "/c", "where", "winget"], shell=False, text=True, stdout=subprocess.PIPE).stdout.strip()
        if winget_location == "":
            print(f"{ERROR}WinGet not found. Try: use other installation method {Fore.LIGHTBLACK_EX}[找不到WinGet, 请尝试使用其他安装方式]{Fore.RESET}")
            return False
        cmd = [
            "winget", "install", "CoreyButler.NVMforWindows",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--location", os.path.join(self.target_path, "nvm")
        ]
        match subprocess.run(cmd, text=True).returncode:
            case 0: ...
            case -1978335212: ...
            case 3010: ...
            case _ as returncode:
                print(f"{WARN}The WinGet returned non-zero code {returncode} , this might be a flaw in WinGet itself. (WinGet返回值不为0, 这可能是WinGet本身的缺陷)")
                input(f"{INFO}Press enter to continue (按回车继续)")
        self._refresh_env()
        print(f"{SUCCESS}NVM installed successfully (NVM安装成功)")
        return True
    
    """ SETUP NODE """

    def setup_node_nvm(self):
        """Setup Node.js using NVM (cross-platform)"""
        print(f"{INFO}Starting add Node.js LTS (开始添加Node.js版本)")
        try:
            if PlatformDetector.is_windows():
                subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "install", "lts"], check=True, shell=True, text=True, stdout=subprocess.DEVNULL)
            elif PlatformDetector.is_linux():
                # For Linux, use nvm.sh script
                nvm_path = os.path.join(self.target_path, "nvm")
                os.makedirs(nvm_path, exist_ok=True)
                
                # Download nvm.sh
                nvm_url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh"
                self._download_file(nvm_url, os.path.join(nvm_path, "install.sh"))
                
                # Run installation script
                subprocess.run([
                    "bash", os.path.join(nvm_path, "install.sh"), 
                    "--install-dir", nvm_path
                ], check=True, shell=False, text=True, stdout=subprocess.DEVNULL)
                
                # Source nvm and install node
                nvm_sh = os.path.join(nvm_path, "nvm.sh")
                if os.path.exists(nvm_sh):
                    # Use a temporary script to run nvm commands
                    temp_script = os.path.join(self.temp_dir, "setup_nvm.sh")
                    with open(temp_script, "w") as f:
                        f.write(f"""#!/bin/bash
source "{nvm_sh}"
nvm install --lts
nvm use --lts
nvm alias default node
""")
                    os.chmod(temp_script, stat.S_IRWXU)
                    subprocess.run([temp_script], check=True, shell=False, text=True, stdout=subprocess.DEVNULL)
            else:
                raise NotImplementedError("NVM setup not implemented for this platform")
        except Exception as e:
            print(f"{ERROR}Failed to add Node.js version (添加Node.js版本失败): {e}")
            sys.exit(1)
        print(f"{SUCCESS}Added LTS Node version (添加Node LTS版本成功)")
        
        # Set mirrors (cross-platform)
        if PlatformDetector.is_windows():
            subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "node_mirror", "https://npmmirror.com/mirrors/node/"], shell=True, stdout=subprocess.DEVNULL)
            subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "npm_mirror", "https://npmmirror.com/mirrors/npm/"], shell=True, stdout=subprocess.DEVNULL)
        elif PlatformDetector.is_linux():
            # For Linux, set npm config directly
            subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], shell=False, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["npm", "config", "set", "disturl", "https://npmmirror.com/mirrors/node/"], shell=False, check=True, stdout=subprocess.DEVNULL)

    # Windows Only
    def setup_node_legacy(self):
        """Setup Node.js on Windows (legacy MSI method)"""
        if not PlatformDetector.is_windows():
            return False
            
        print(f"{INFO}Starting install Node.js (开始安装Node.js)")
        self._download_file(self._get_config("nodejs_url"), os.path.join(self.temp_dir, "nodejs.msi"))
        process = self._install_msi_package(os.path.join(self.temp_dir, "nodejs.msi"), os.path.join(self.target_path, "node-lts"))
        if process.returncode != 0:
            print(f"{ERROR}Failed to install Node.js version (安装Node.js版本失败)")
            return False
        
        self._refresh_env()
        subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], shell=True, check=True, stdout=subprocess.DEVNULL)
        print(f"{SUCCESS}Added LTS Node version (添加Node LTS版本成功)")
        return True

    def setup_node_winget(self):
        """Setup Node.js on Windows using WinGet"""
        if not PlatformDetector.is_windows():
            return False
            
        print(f"{INFO}Checking WinGet... {Fore.LIGHTBLACK_EX}[正在检查WinGet...]{Fore.RESET}")
        winget_location = subprocess.run(["cmd.exe", "/c", "where", "winget"], shell=False, text=True, stdout=subprocess.PIPE).stdout.strip()
        if winget_location == "":
            print(f"{ERROR}WinGet not found. Try: use other installation method {Fore.LIGHTBLACK_EX}[找不到WinGet, 请尝试使用其他安装方式]{Fore.RESET}")
            return False
        install_command = [
            "winget", "install", 
            "--id", "OpenJS.NodeJS.LTS", 
            "--silent", 
            "--accept-package-agreements", 
            "--accept-source-agreements"
        ]
        match subprocess.run(install_command, text=True).returncode:
            case 0: ...
            case -1978335212: ...
            case 3010: ...
            case _ as returncode:
                print(f"{WARN}The WinGet returned non-zero code {returncode} , this might be a flaw in itself. (WinGet返回值不为0, 这可能是WinGet本身的缺陷)")
                input(f"{INFO}Press enter to continue (按回车继续)")

        self._refresh_env()
        subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], shell=True, check=True, stdout=subprocess.DEVNULL)
        print(f"{SUCCESS}Node.js installed successfully (Node安装成功)")
        return True
    
    # Linux Only
    def setup_node_apt(self) -> int:
        """Install Node.js on Debian/Ubuntu using apt"""
        if not PlatformDetector.is_linux():
            return 255
            
        packages = ["nodejs", "npm"]
        print(f"{INFO}Checking apt... {Fore.LIGHTBLACK_EX}[正在检查APT...]{Fore.RESET}")
        try:
            result = subprocess.run(["apt", "update", "-y"], shell=False, text=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print(result.stderr)
                print(f"{WARN}apt update failed (apt更新包索引失败)")
        except Exception as e:
            if isinstance(e, (OSError, FileNotFoundError)):
                return 255
            else:
                print(f"{ERROR}Check failed (检查apt失败)")
                return 1
        
        # Add NodeSource repository for latest Node.js
        try:
            subprocess.run(["curl", "-fsSL", "https://deb.nodesource.com/setup_lts.x", "|", "bash", "-"], 
                         shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except Exception:
            print(f"{WARN}NodeSource repository setup failed, using system packages")
        
        for p in packages:
            try:
                subprocess.run(["apt", "install", p, "-y"], shell=False, check=True, text=True, stdout=subprocess.DEVNULL)
            except Exception:
                print(f"{ERROR}Install {p} failed (安装{p}失败)")
                return 1
        return 0
    
    def setup_node_pacman(self) -> int:
        """Install Node.js on Arch Linux using pacman"""
        if not PlatformDetector.is_linux():
            return 255
            
        packages = ["nodejs", "npm"]
        print(f"{INFO}Checking pacman... {Fore.LIGHTBLACK_EX}[正在检查Pacman...]{Fore.RESET}")
        try:
            result = subprocess.run(["pacman", "-Sy", "--noconfirm"], shell=False, text=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print(result.stderr)
                print(f"{ERROR}pacman sync failed (pacman更新包索引失败)")
                return 1
        except Exception as e:
            if isinstance(e, (OSError, FileNotFoundError)):
                return 255
            else:
                print(f"{ERROR}Check failed (检查pacman失败)")
                return 1
        
        for p in packages:
            try:
                subprocess.run(["pacman", "-S", p, "--noconfirm"], shell=False, check=True, text=True, stdout=subprocess.DEVNULL)
            except Exception:
                print(f"{ERROR}Install {p} failed (安装{p}失败)")
                return 1
        return 0

    def setup_node_yum(self) -> int:
        """Install Node.js on RHEL/CentOS using yum/dnf"""
        if not PlatformDetector.is_linux():
            return 255
            
        packages = ["nodejs", "npm"]
        print(f"{INFO}Checking yum/dnf... {Fore.LIGHTBLACK_EX}[正在检查yum/dnf...]{Fore.RESET}")
        
        # Check if dnf is available (RHEL 8+)
        dnf_available = subprocess.run(["which", "dnf"], shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
        yum_available = subprocess.run(["which", "yum"], shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
        
        if dnf_available:
            pkg_manager = "dnf"
        elif yum_available:
            pkg_manager = "yum"
        else:
            return 255
            
        try:
            # Enable NodeSource repository
            subprocess.run([pkg_manager, "install", "-y", "epel-release"], shell=False, check=True, stdout=subprocess.DEVNULL)
            subprocess.run([pkg_manager, "install", "-y", "https://rpm.nodesource.com/pub_20.x/el/8/x86_64/nodesource-release-el8-1.noarch.rpm"], 
                         shell=False, check=True, stdout=subprocess.DEVNULL)
        except Exception:
            print(f"{WARN}NodeSource repository setup failed, using system packages")
        
        for p in packages:
            try:
                subprocess.run([pkg_manager, "install", p, "-y"], shell=False, check=True, text=True, stdout=subprocess.DEVNULL)
            except Exception:
                print(f"{ERROR}Install {p} failed (安装{p}失败)")
                return 1
        return 0

    def install_git_legacy(self) -> bool:
        """Install Git on Windows (legacy method)"""
        if not PlatformDetector.is_windows():
            return False
            
        print(f"{INFO}Starting install Git (开始安装Git)")
        self._download_file(self._get_config("git_url"), os.path.join(self.temp_dir, "git-installer.exe"))
        result = subprocess.run(
            [
                os.path.join(self.temp_dir, "git-installer.exe"),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
            ],
            shell=False,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            print(f"{ERROR}Failed to install Git (安装Git失败): The process returned non-zero code {str(result.returncode)}, STDERR:")
            print(result.stderr)
            return False
        print(f"{SUCCESS}Git installed successfully (Git安装成功)")
        return True

    def install_git_winget(self) -> bool:
        """Install Git on Windows using WinGet"""
        if not PlatformDetector.is_windows():
            return False
            
        print(f"{INFO}Checking WinGet... {Fore.LIGHTBLACK_EX}[正在检查WinGet...]{Fore.RESET}")
        winget_location = subprocess.run(["cmd.exe", "/c", "where", "winget"], shell=False, text=True, stdout=subprocess.PIPE).stdout.strip()
        if winget_location == "":
            print(f"{ERROR}WinGet not found. Try: use other installation method {Fore.LIGHTBLACK_EX}[找不到WinGet, 请尝试使用其他安装方式]{Fore.RESET}")
            return False
        install_command = [
            "winget", "install",
            "--id", "Git.Git",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements"
        ]
        match subprocess.run(install_command, text=True).returncode:
            case 0: ...
            case -1978335212: ...
            case 3010: ...
            case _ as returncode:
                print(f"{WARN}The WinGet returned non-zero code {returncode} , this might be a flaw in itself. (WinGet返回值不为0, 这可能是WinGet本身的缺陷)")
                input(f"{INFO}Press enter to continue (按回车继续)")
        
        self._refresh_env()
        print(f"{SUCCESS}Git installed successfully (Git安装成功)")
        return True

    def install_git_apt(self) -> bool:
        """Install Git on Linux using apt"""
        if not PlatformDetector.is_linux():
            return False
            
        print(f"{INFO}Installing Git using apt... {Fore.LIGHTBLACK_EX}[使用apt安装Git...]{Fore.RESET}")
        try:
            subprocess.run(["apt", "update", "-y"], shell=False, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["apt", "install", "git", "-y"], shell=False, check=True, stdout=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"{ERROR}Failed to install Git: {e}")
            return False

    def install_git_pacman(self) -> bool:
        """Install Git on Linux using pacman"""
        if not PlatformDetector.is_linux():
            return False
            
        print(f"{INFO}Installing Git using pacman... {Fore.LIGHTBLACK_EX}[使用pacman安装Git...]{Fore.RESET}")
        try:
            subprocess.run(["pacman", "-Sy", "--noconfirm"], shell=False, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["pacman", "-S", "git", "--noconfirm"], shell=False, check=True, stdout=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"{ERROR}Failed to install Git: {e}")
            return False

    def install_git_yum(self) -> bool:
        """Install Git on Linux using yum/dnf"""
        if not PlatformDetector.is_linux():
            return False
            
        print(f"{INFO}Installing Git using yum/dnf... {Fore.LIGHTBLACK_EX}[使用yum/dnf安装Git...]{Fore.RESET}")
        
        # Check if dnf is available (RHEL 8+)
        dnf_available = subprocess.run(["which", "dnf"], shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
        yum_available = subprocess.run(["which", "yum"], shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
        
        pkg_manager = "dnf" if dnf_available else "yum"
        
        try:
            subprocess.run([pkg_manager, "install", "-y", "git"], shell=False, check=True, stdout=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"{ERROR}Failed to install Git: {e}")
            return False

    def ensure_git_installed(self) -> bool:
        """Ensure Git is installed (cross-platform)"""
        git_executable = self._detect_executable("git")
        if git_executable is not None:
            print(f"{SUCCESS}Git already exists, skip installation (检测到Git已存在, 跳过安装)")
            return True

        print(f"{INFO}Git not found, preparing pre-installation (未检测到Git, 准备提前安装)")
        
        if PlatformDetector.is_windows():
            if self.install_mode == 1:
                if not self.install_git_winget():
                    return False
            else:
                if not self.install_git_legacy():
                    return False
        elif PlatformDetector.is_linux():
            # Try different package managers
            if self.setup_node_apt() == 0 or self.setup_node_pacman() == 0 or self.setup_node_yum() == 0:
                # If node installation succeeded, git should be available
                pass
            if not self._detect_executable("git"):
                # Install git separately
                if self.install_git_apt() or self.install_git_pacman() or self.install_git_yum():
                    pass
                else:
                    print(f"{ERROR}Git installation verification failed (Git安装校验失败)")
                    return False
        else:
            print(f"{ERROR}Platform not supported for Git installation")
            return False

        self._refresh_env()
        git_executable = self._detect_executable("git")
        if git_executable is None:
            print(f"{ERROR}Git installation verification failed (Git安装校验失败)")
            return False
        return True

    def npm_install_openclaw(self):
        """Install OpenClaw via npm (cross-platform)"""
        print(f"{INFO}The dawn of victory is at hand (胜利的曙光即将到来)")
        print(f"{INFO}Please select a package manager (请选择包管理器):")
        print(f"""
{Fore.CYAN}1. CNPM (Recommended for Chinese users) {Fore.LIGHTBLACK_EX}[国内用户推荐使用]
{Fore.CYAN}2. PNPM (💡Recommended)
{Fore.CYAN}3. NPM (Legacy){Fore.RESET}
        """)
        while True:
            pm = input("Enter your select: ")
            try:
                pm = int(pm)
                if pm < 1 or pm > 3: raise ValueError()
            except ValueError:
                print(f"{ERROR}Invaild Input (输入错误)")
                continue
            break
        print(f"{INFO}Starting install OpenClaw...")
        match pm:
            case 1:
                try:
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["npm", "install", "cnpm", "-g"], shell=shell_arg, text=True, check=True, stdout=subprocess.DEVNULL)
                except Exception:
                    print(f"{ERROR}Failed to install CNPM (安装CNPM失败)")
                    return False
                try:
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["cnpm", "install", "-g", "openclaw@latest"], shell=shell_arg, text=True, check=True)
                    if PlatformDetector.is_windows():
                        with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                            f.write("@echo off & openclaw dashboard")
                    elif PlatformDetector.is_linux():
                        # Create desktop shortcut for Linux
                        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                        os.makedirs(desktop_dir, exist_ok=True)
                        desktop_file = os.path.join(desktop_dir, "OpenClaw.desktop")
                        with open(desktop_file, "w") as f:
                            f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=OpenClaw
Exec=openclaw dashboard
Icon=utilities-terminal
Terminal=false
""")
                        os.chmod(desktop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                        
                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                return True
            case 2:
                try:
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["npm", "install", "pnpm", "-g"], shell=shell_arg, text=True, check=True, stdout=subprocess.DEVNULL)
                    if PlatformDetector.is_linux():
                        pnpm_home = os.path.join(os.path.expanduser("~"), ".local", "share", "pnpm")
                        os.makedirs(pnpm_home, exist_ok=True)
                        # ✅ Linux: shell=False (explicit)
                        subprocess.run(["pnpm", "config", "set", "global-bin-dir", pnpm_home], shell=False, text=True, check=True, stdout=subprocess.DEVNULL)
                        # Add to PATH
                        shell_rc = os.path.join(os.path.expanduser("~"), ".bashrc")
                        if os.path.exists(shell_rc):
                            with open(shell_rc, "a") as f:
                                f.write(f'\nexport PATH="$HOME/.local/share/pnpm:$PATH"\n')
                    self._refresh_env()
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["pnpm", "setup"], shell=shell_arg, text=True, check=True, stdout=subprocess.DEVNULL)
                except Exception:
                    print(f"{ERROR}Failed to install PNPM (安装PNPM失败)")
                    return False
                try:
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["pnpm", "add", "-g", "openclaw@latest"], shell=shell_arg, text=True, check=True)
                    if PlatformDetector.is_windows():
                        with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                            f.write("@echo off & openclaw dashboard")
                    elif PlatformDetector.is_linux():
                        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                        os.makedirs(desktop_dir, exist_ok=True)
                        desktop_file = os.path.join(desktop_dir, "OpenClaw.desktop")
                        with open(desktop_file, "w") as f:
                            f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=OpenClaw
Exec=openclaw dashboard
Icon=utilities-terminal
Terminal=false
""")
                        os.chmod(desktop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                return True
            case 3:
                try:
                    
                    shell_arg = PlatformDetector.is_windows()
                    subprocess.run(["npm", "install", "-g", "openclaw@latest"], shell=shell_arg, text=True, check=True)
                    if PlatformDetector.is_windows():
                        with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                            f.write("@echo off & openclaw dashboard")
                    elif PlatformDetector.is_linux():
                        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                        os.makedirs(desktop_dir, exist_ok=True)
                        desktop_file = os.path.join(desktop_dir, "OpenClaw.desktop")
                        with open(desktop_file, "w") as f:
                            f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=OpenClaw
Exec=openclaw dashboard
Icon=utilities-terminal
Terminal=false
""")
                        os.chmod(desktop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                print(f"{INFO}Running init... {Fore.LIGHTBLACK_EX}[正在初始化OpenClaw...]{Fore.RESET}")
                return True
                

    def install_openclaw(self):
        """Main installation function (cross-platform)"""
        print(INFOX)
        print(INFO + "This program is FOSS (Free and open-source software) (本程序完全免费开源)\n\n")
        
        # Get username (cross-platform)
        try:
            username = getpass.getuser() if getpass.getuser() and getpass.getuser() != "" else "机主"
        except Exception:
            username = "机主"

        print(INFO + f"Hello, {username} (你好，{username})")
        print(INFO + "Please select a Node.js installation method (请选择Node.js安装方式)")
        
        # Platform-specific options
        if PlatformDetector.is_windows():
            print(f"""
{Fore.CYAN}1. WinGet (Windows 11) {Fore.LIGHTBLACK_EX}[WinGet方案 (适用Windows 11+)]
{Fore.CYAN}2. MSIEXEC or Legacy (Windows 10+) {Fore.LIGHTBLACK_EX}[MsiExec or Legacy方案 (适用Windows 10+)]
{INFO}If you want to use NVM, please type choice and 'v'
            """, Fore.RESET)
        elif PlatformDetector.is_linux():
            print(f"""
{Fore.CYAN}1. APT (Debian/Ubuntu) {Fore.LIGHTBLACK_EX}[APT方案 (适用于Debian/Ubuntu)]
{Fore.CYAN}2. Pacman (Arch Linux) {Fore.LIGHTBLACK_EX}[Pacman方案 (适用于Arch Linux)]
{Fore.CYAN}3. YUM/DNF (RHEL/CentOS) {Fore.LIGHTBLACK_EX}[YUM/DNF方案 (适用于RHEL/CentOS)]
{INFO}If you want to use NVM, please type choice and 'v'
            """, Fore.RESET)
        else:
            print(f"{ERROR}Unsupported platform: {self.platform}")
            sys.exit(1)

        while True:
            try:
                i = input(INFO + "Please type your choice (请输入方案): ")
                            
                if i.endswith('v'): 
                    self.nvm = True
                    i = i.replace('v', '')
                i = int(i)
                if i < 1 or i > (3 if PlatformDetector.is_linux() else 2): raise ValueError()
                self.install_mode = i
            except ValueError:
                print(ERROR + "Invaild Input (输入错误)")
                continue
            break

        if not self.ensure_git_installed():
            sys.exit(1)

        # Platform-specific installation logic
        if not self.nvm:
            print(WARN + "You have chosen not to install NVM, which may cause conflict issues (你已选择不安装NVM, 这可能会导致冲突问题)")
            if PlatformDetector.is_windows():
                match self.install_mode:
                    case 1:
                        if self.setup_node_winget():
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
                    case 2:
                        if self.setup_node_legacy():
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else: 
                            sys.exit(1)
            elif PlatformDetector.is_linux():
                match self.install_mode:
                    case 1:
                        if self.setup_node_apt() == 0:
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
                    case 2:
                        if self.setup_node_pacman() == 0:
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
                    case 3:
                        if self.setup_node_yum() == 0:
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
        else:
            if PlatformDetector.is_windows():
                match self.install_mode:
                    case 1:
                        if self.install_nvm_winget():
                            self.setup_node_nvm()
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
                    case 2:
                        if self.install_nvm_legacy():
                            self.setup_node_nvm()
                            if not self.npm_install_openclaw(): sys.exit(1)
                        else:
                            sys.exit(1)
            elif PlatformDetector.is_linux():
                # For Linux, always use nvm.sh
                if self.setup_node_nvm():
                    if not self.npm_install_openclaw(): sys.exit(1)
                else:
                    sys.exit(1)
            
        # Platform-specific post-installation
        if PlatformDetector.is_windows():
            os.makedirs(os.path.join(os.environ["APPDATA"], "OpenClaw"), exist_ok=True)
            with open(os.path.join(os.environ["APPDATA"], "OpenClaw", "gateway.ps1"), "w", encoding="utf-8") as f:
                f.write('Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process\r\n. openclaw.ps1 gateway')
                self.add_to_startup("OpenClawGateway", "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + os.path.join(os.environ["APPDATA"], "OpenClaw", "gateway.ps1") + "\"")
                self._refresh_env()
                powershell_path = subprocess.run(["cmd.exe", "/c", "where", "powershell.exe"], shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip().splitlines()[0]
                oc_path = subprocess.run(["cmd", "/c", "where", "openclaw.ps1"], shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip().splitlines()[0]
                i: str = input(f"{INFO}Do you want to create a icon in the Start Menu (no | yes/y/a) {Fore.LIGHTBLACK_EX}[是否要在开始菜单创建图标? 可能会报毒, 请手动添加白名单 我们保证该操作无毒, 若不放心请跳过]{Fore.RESET}")
                if i.strip().lower() in ['y', "yes", 'a', "yes/y/a"]:
                    self.create_start_menu_pylnk("OpenClaw", "OpenClaw Gateway", powershell_path, f'-ExecutionPolicy Bypass -File "{os.path.join(os.environ["APPDATA"], "OpenClaw", "gateway.ps1")}"')
                    self.create_start_menu_pylnk("OpenClaw", "OpenClaw Dashboard", powershell_path, f"-ExecutionPolicy Bypass -WindowStyle Hidden -File {oc_path} dashboard")
                print(f"\n{INFO}Preparing start OpenClaw setup (正在准备启动OpenClaw配置)\n{INFO}Use up/down/right/left to select, enter to choose (使用键盘上下左右来选择, 回车选中) ")
                print(f"{INFO}The first selection please choose 'Yes' (Agree) {Fore.LIGHTBLACK_EX}[第一个选项为用户协议, 请选择Yes以同意使用OpenClaw]{Fore.RESET}")
                print(f"{INFO}In skill selection, please select 'mcporter' {Fore.LIGHTBLACK_EX}[在让你选择Skill(技能)时, 请选上mcporter]{Fore.RESET}")
                print(f"{INFO}After finish this, please press Ctrl+C to continue (配置提示完成后, 请按Ctrl+C继续)")
                print(f"{Fore.LIGHTBLACK_EX}[若有任何问题, 请使用翻译软件]{Fore.RESET}")
                while True:
                    print(f"Type 'next' to continue (若你已悉知, 请输入next继续)")
                    _: str = input().replace('\'', '')
                    if not _.lower().strip() == "next":
                        continue
                    else:
                        break
        elif PlatformDetector.is_linux():
            # Linux post-installation
            config_dir = os.path.join(os.path.expanduser("~"), ".config", "OpenClaw")
            os.makedirs(config_dir, exist_ok=True)
            
            # Create systemd service for gateway (optional)
            service_dir = os.path.join(os.path.expanduser("~"), ".config", "systemd", "user")
            os.makedirs(service_dir, exist_ok=True)
            service_file = os.path.join(service_dir, "openclaw-gateway.service")
            
            with open(service_file, "w") as f:
                f.write(f"""[Unit]
Description=OpenClaw Gateway Service
After=network.target

[Service]
ExecStart={sys.executable} -m openclaw gateway
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
""")
            
            # Enable the service
            try:
                subprocess.run(["systemctl", "--user", "enable", "openclaw-gateway.service"], shell=False, check=True, stdout=subprocess.DEVNULL)
                subprocess.run(["systemctl", "--user", "start", "openclaw-gateway.service"], shell=False, check=True, stdout=subprocess.DEVNULL)
            except Exception as e:
                print(f"{WARN}Failed to set up systemd service: {e}")
            
            print(f"\n{INFO}OpenClaw installation completed successfully on {self.platform}!")
            print(f"{INFO}You can run 'openclaw gateway' and 'openclaw dashboard' to launch")
            print(f"{INFO}For auto-start, the systemd service has been configured (you may need to log out and back in)")

    def cleanup_temp_files(self):
        """Cleanup temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"{WARN}Failed to clean up temp files: {e}")


def is_path_like(s):
    """Check if string is path-like"""
    try:
        p = PurePath(s)
    except Exception:
        return False
    return len(p.parts) > 1 or p.drive != "" or p.suffix != ""


if __name__ == "__main__":
    while True:
        path = input("Please enter the installation path to install OpenClaw and Runtimes (请输入OpenClaw和运行时安装路径): ").strip()
        if not is_path_like(path) or os.path.isfile(path):
            print("Invaild Input (输入错误)")
            continue
        if not os.path.exists(path):
            os.makedirs(path)
        os.makedirs(os.path.join(path, ".temp"), exist_ok=True)
        break
    
    if PlatformDetector.is_windows():
        init(autoreset=True, convert=True)
    else:
        init(autoreset=True)
    openclaw_installer = OpenClawInstall(path)
    
    try:
        openclaw_installer.install_openclaw()
        subprocess.run(["openclaw", "onboard"], shell=False, text=True)
    finally:
        openclaw_installer.cleanup_temp_files()
    
    print("OpenClaw is ready. Run 'openclaw gateway' and 'openclaw dashboard' to launch")
    input("Press any key to continue...")
    sys.exit(0)