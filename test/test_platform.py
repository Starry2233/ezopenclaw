#!/usr/bin/env python3
"""Test platform detection and basic functionality"""

import sys
import os
import platform
from pathlib import PurePath

print("=== Platform Detection Test ===")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")
print(f"Platform name: {platform.platform()}")
print(f"OS: {os.name}")
print(f"Is Windows: {sys.platform.startswith('win')}")
print(f"Is Linux: {sys.platform.startswith('linux')}")
print(f"Is macOS: {sys.platform.startswith('darwin')}")

print("\n=== Path Testing ===")
test_path = "/home/user/test"
print(f"PurePath test: {PurePath(test_path)}")
print(f"Is path-like: {len(PurePath(test_path).parts) > 1 or PurePath(test_path).drive != '' or PurePath(test_path).suffix != ''}")

print("\n=== Environment Variables ===")
print(f"HOME: {os.getenv('HOME', 'Not set')}")
print(f"USERPROFILE: {os.getenv('USERPROFILE', 'Not set')}")
print(f"APPDATA: {os.getenv('APPDATA', 'Not set')}")

print("\n=== Test Complete ===")