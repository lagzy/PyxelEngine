#!/usr/bin/env python3
"""
build_panda3d.py - Simple Panda3D build script
Run this from "Developer Command Prompt for VS 2022"
"""

import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("Panda3D Build Script")
    print("=" * 60)
    print()
    
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    core_engine_dir = os.path.join(script_dir, "core_engine")
    
    # Check if in Developer Command Prompt
    try:
        result = subprocess.run(["where", "cl.exe"], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: Not in Developer Command Prompt!")
            print("Please open 'Developer Command Prompt for VS 2022' from Start menu.")
            return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    print("[OK] Developer Command Prompt detected.")
    print()
    
    # Change to core_engine directory
    os.chdir(core_engine_dir)
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Clean previous build
    built_dir = os.path.join(core_engine_dir, "built")
    if os.path.exists(built_dir):
        print("Cleaning previous build...")
        import shutil
        shutil.rmtree(built_dir)
        print("[OK] Previous build removed.")
        print()
    
    # Clean cached files
    print("Cleaning cached files...")
    for root, dirs, files in os.walk(core_engine_dir):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"), ignore_errors=True)
    print("[OK] Cached files cleaned.")
    print()
    
    # Set up thirdparty Python
    thirdparty_dir = os.path.join(core_engine_dir, "thirdparty", "win-python3.10-x64")
    if not os.path.exists(thirdparty_dir):
        os.makedirs(thirdparty_dir, exist_ok=True)
    
    # Get system Python
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    
    print("Setting up thirdparty Python...")
    
    # Copy Python files
    try:
        import shutil
        dst_exe = os.path.join(thirdparty_dir, "python.exe")
        if not os.path.exists(dst_exe):
            shutil.copy2(python_exe, dst_exe)
            print("[OK] Copied python.exe")
        
        dll_src = os.path.join(python_dir, "python310.dll")
        if os.path.exists(dll_src):
            dll_dst = os.path.join(thirdparty_dir, "python310.dll")
            if not os.path.exists(dll_dst):
                shutil.copy2(dll_src, dll_dst)
                print("[OK] Copied python310.dll")
        
        include_src = os.path.join(os.path.dirname(python_dir), "include")
        if os.path.exists(include_src):
            include_dst = os.path.join(thirdparty_dir, "include")
            if not os.path.exists(include_dst):
                shutil.copytree(include_src, include_dst)
                print("[OK] Copied include directory")
        
        libs_src = os.path.join(os.path.dirname(python_dir), "libs")
        if os.path.exists(libs_src):
            libs_dst = os.path.join(thirdparty_dir, "libs")
            if not os.path.exists(libs_dst):
                shutil.copytree(libs_src, libs_dst)
                print("[OK] Copied libs directory")
    except Exception as e:
        print(f"[WARNING] {e}")
    
    print()
    
    # Verify setup
    if os.path.exists(os.path.join(thirdparty_dir, "python.exe")):
        print("[OK] python.exe found")
    else:
        print("[FAIL] python.exe NOT found")
    
    if os.path.exists(os.path.join(thirdparty_dir, "python310.dll")):
        print("[OK] python310.dll found")
    else:
        print("[FAIL] python310.dll NOT found")
    
    print()
    
    # Build Panda3D
    print("Building Panda3D (this may take 15-30 minutes)...")
    print()
    
    cmd = [
        sys.executable,
        "makepanda/makepanda.py",
        "--use-python",
        "--nothing",
        "--outputdir", "built",
        "--windows-sdk", "10"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print("=" * 60)
        print("Build completed successfully!")
        print(f"Built files are in: {built_dir}")
        print("=" * 60)
        return 0
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("Build failed!")
        print("=" * 60)
        print()
        print("Troubleshooting:")
        print("1. Make sure 'Desktop development with C++' is installed in Visual Studio")
        print("2. Make sure Windows 10/11 SDK is installed")
        print("3. Make sure Python 3.10 is installed and in PATH")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
