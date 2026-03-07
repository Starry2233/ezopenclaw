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
#   EzOpenClaw by Starry2233


from msiexec import MsiExec
from colorama import Fore, init
from pathlib import PurePath
from typing import Any
import os
import sys
import subprocess
import requests
import getpass
import json
import ctypes
import winreg


INFO = Fore.LIGHTBLUE_EX + "[INFO]" + Fore.RESET
WARN = Fore.LIGHTYELLOW_EX + "[WARN]" + Fore.RESET
ERROR = Fore.RED + "[ERROR]" + Fore.RESET
SUCCESS = Fore.LIGHTGREEN_EX + "[SUCCESS]" + Fore.RESET


class OpenClawInstall(object):
    def __init__(self, target_path: str):
        self.target_path = target_path
        self.nvm = False
        self.install_mode = 2

    @staticmethod
    def _refresh_env():
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
                sys_path, _ = winreg.QueryValueEx(k, "Path")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                user_path, _ = winreg.QueryValueEx(k, "Path")
            
            os.environ["PATH"] = sys_path + os.pathsep + user_path
            
            ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x02, 1000, ctypes.byref(ctypes.c_long()))
            return True
        except:
            return False

    @staticmethod
    def _install_msi_package(package: str, target: str) -> subprocess.CompletedProcess:
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
    def _detect_executable(name) -> str | None:
        result = subprocess.run(
            ["cmd.exe", "/c", "where", name],
            shell=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout
        if result == "":
            return None
        return result
    
    @staticmethod
    def _get_config(key) -> Any:
        with open("config.json", "r", encoding="utf-8") as f:
            json_text: dict = json.load(f)
            result = json_text.get(key, None)
            return result

    @staticmethod
    def _download_file(url, dst):
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
    
    def install_nvm_legacy(self) -> bool:
        url = self._get_config("nvm_url")
        if not os.path.exists(os.path.join(self.target_path, ".temp")):
            os.makedirs(os.path.join(self.target_path, ".temp"))
        self._download_file(url, os.path.join(self.target_path, ".temp", "nvm-setup.exe"))
        print(f"{INFO}Download successful, now starting install NVM... {Fore.LIGHTBLACK_EX}[下载成功, 开始安装NVM...]{Fore.RESET}")
        # if not os.path.exists(os.path.join(self.target_path, "nvm")):
        #     os.makedirs(os.path.join(self.target_path, "nvm"))
        result = subprocess.run(
            [
                os.path.join(self.target_path, ".temp", "nvm-setup.exe"),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/FORCE",
                "/SP-",
                f"/DIR={os.path.join(self.target_path, "nvm")}"
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
        try:
            result = subprocess.run(cmd, text=True, check=True)
        except Exception:
            print(f"{ERROR}Failed to install NVM (NVM安装失败)")
            return False
        print(f"{SUCCESS}NVM installed successfully (NVM安装成功)")
        return True
    
    def setup_node_nvm(self):
        print(f"{INFO}Starting add Node.js LTS (开始添加Node.js版本)")
        try:
            subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "install", "lts"], check=True, shell=True, text=True, stdout=subprocess.DEVNULL)
        except Exception:
            print(f"{ERROR}Failed to add Node.js version (添加Node.js版本失败)")
            sys.exit(1)
        print(f"{SUCCESS}Added LTS Node version (添加Node LTS版本成功)")
        subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "use", "lts"], shell=True, stdout=subprocess.DEVNULL)
        subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "node_mirror", "https://npmmirror.com/mirrors/node/"], shell=True, stdout=subprocess.DEVNULL)
        subprocess.run([os.path.join(self.target_path, "nvm", "nvm"), "npm_mirror", "https://npmmirror.com/mirrors/npm/"], shell=True, stdout=subprocess.DEVNULL)
        subprocess.run(["npm", "prefix", "-g"], shell=True, stdout=subprocess.DEVNULL, text=True)

    def setup_node_legacy(self):
        print(f"{INFO}Starting install Node.js (开始安装Node.js)")
        self._download_file(self._get_config("nodejs_url"), os.path.join(self.target_path, ".temp", "nodejs.msi"))
        process = self._install_msi_package(os.path.join(self.target_path, ".temp", "nodejs.msi"), os.path.join(self.target_path, "node-lts"))
        if process.returncode != 0:
            print(f"{ERROR}Failed to install Node.js version (安装Node.js版本失败)")
            return False
        
        self._refresh_env()
        subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], shell=True, check=True, stdout=subprocess.DEVNULL)
        print(f"{SUCCESS}Added LTS Node version (添加Node LTS版本成功)")
        return True

    def setup_node_winget(self):
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
        try:
            subprocess.run(install_command, text=True, check=True)
        except Exception:
            print(f"{ERROR}Failed to install Node.js (Node安装失败)")
            return False
        self._refresh_env()
        subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], shell=True, check=True, stdout=subprocess.DEVNULL)
        print(f"{SUCCESS}Node.js installed successfully (Node安装成功)")
        return True

    def install_git_legacy(self) -> bool:
        print(f"{INFO}Starting install Git (开始安装Git)")
        self._download_file(self._get_config("git_url"), os.path.join(self.target_path, ".temp", "git-installer.exe"))
        result = subprocess.run(
            [
                os.path.join(self.target_path, ".temp", "git-installer.exe"),
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
        try:
            subprocess.run(install_command, text=True, check=True)
        except Exception:
            print(f"{ERROR}Failed to install Git (Git安装失败)")
            return False
        print(f"{SUCCESS}Git installed successfully (Git安装成功)")
        return True

    def ensure_git_installed(self) -> bool:
        git_executable = self._detect_executable("git")
        if git_executable is not None:
            print(f"{SUCCESS}Git already exists, skip installation (检测到Git已存在, 跳过安装)")
            return True

        print(f"{INFO}Git not found, preparing pre-installation (未检测到Git, 准备提前安装)")
        if self.install_mode == 1:
            if not self.install_git_winget():
                return False
        else:
            if not self.install_git_legacy():
                return False

        self._refresh_env()
        git_executable = self._detect_executable("git")
        if git_executable is None:
            print(f"{ERROR}Git installation verification failed (Git安装校验失败)")
            return False
        return True

    def npm_install_openclaw(self):
        print(f"{INFO}The dawn of victory is at hand (胜利的曙光即将到来)")
        print(f"{INFO}Please select a package manager (请选择包管理器):")
        print(f"""
{Fore.CYAN}1. CNPM (Recommended for Chinese users) {Fore.LIGHTBLACK_EX}[中国用户推荐使用]
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
                    subprocess.run(["npm", "install", "cnpm", "-g"], shell=True, text=True, check=True, stdout=subprocess.DEVNULL)
                except Exception:
                    print(f"{ERROR}Failed to install CNPM (安装CNPM失败)")
                    return False
                try:
                    subprocess.run(["cnpm", "install", "-g", "openclaw@latest"], shell=True, text=True, check=True)
                    with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                        f.write("@echo off & npx openclaw gateway")
                        
                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                return True
            case 2:
                try:
                    subprocess.run(["npm", "install", "pnpm", "-g"], shell=True, text=True, check=True, stdout=subprocess.DEVNULL)
                except Exception:
                    print(f"{ERROR}Failed to install PNPM (安装PNPM失败)")
                    return False
                try:
                    subprocess.run(["pnpm", "install", "-g", "openclaw@latest"], shell=True, text=True, check=True)
                    with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                        f.write("@echo off & npx openclaw gateway")
                        
                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                return True
            case 3:
                try:
                    subprocess.run(["npm", "install", "-g", "openclaw@latest"], shell=True, text=True, check=True)
                    with open(os.path.join(os.environ["USERPROFILE"], "Desktop", "OpenClaw.cmd"), "w") as f:
                        f.write("@echo off & npx openclaw gateway")
                        
                except Exception:
                    print(f"{ERROR}Failed to install OpenClaw (安装OpenClaw失败)")
                    return False
                print(f"{SUCCESS}Installation completed successfully, the stage is set. {Fore.LIGHTBLACK_EX}[跨越山海, 终见曙光 OpenClaw安装成功! ]{Fore.RESET}")
                return True
                

    def install_openclaw(self):
        print(INFOX)
        print(INFO + "This program is FOSS (Free and open-source software) (本程序完全免费开源)\n\n")
        username = getpass.getuser() if (
            getpass.getuser()
            and getpass.getuser() != "" 
        ) else "机主"

        print(INFO + f"Hello, {username} (你好，{username})")
        print(INFO + "Please select a Node.js installation method (请选择Node.js安装方式)")
        print(f"""
{Fore.CYAN}1. WinGet (Windows 11) {Fore.LIGHTBLACK_EX}[WinGet方案 (适用Windows 11+)]
{Fore.CYAN}2. MSIEXEC or Legacy (Windows 10+) {Fore.LIGHTBLACK_EX}[MsiExec or Legacy方案 (适用Windows 10+)]
{INFO}If you want to use NVM, please type choice and 'v'
        """, Fore.RESET)

        while True:
            try:
                i = input(INFO + "Please type your choice (请输入方案): ")
                            
                if i.endswith('v'): 
                    self.nvm = True
                    i = i.replace('v', '')
                i = int(i)
                if i < 1 or i > 2: raise ValueError()
                self.install_mode = i
            except ValueError:
                print(ERROR + "Invaild Input (输入错误)")
                continue
            break

        if not self.ensure_git_installed():
            sys.exit(1)

        if not self.nvm:
            print(WARN + "You have chosen not to install NVM, which may cause conflict issues (你已选择不安装NVM, 这可能会导致冲突问题)")
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

        else:
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

def is_path_like(s):
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
    init(autoreset=True, convert=True)
    openclaw_installer = OpenClawInstall(path)
    openclaw_installer.install_openclaw()
    subprocess.run(["npx", "openclaw", "onboard"])
    input("Press any key to continue...")
    sys.exit(0)
    
