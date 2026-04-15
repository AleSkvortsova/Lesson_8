import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_DIR = PROJECT_ROOT / "desktop"
ENTRYPOINT = DESKTOP_DIR / "app.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "CompetitorMonitorDesktop.spec"
EXE_NAME = "CompetitorMonitorDesktop"


def run_pyinstaller():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        EXE_NAME,
        str(ENTRYPOINT),
    ]
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=True)


def print_result():
    exe_path = DIST_DIR / f"{EXE_NAME}.exe"
    if exe_path.exists():
        print(f"\nBuild completed: {exe_path}")
    else:
        print("\nBuild finished, but .exe was not found.")


def main():
    if not ENTRYPOINT.exists():
        raise FileNotFoundError(f"Entrypoint not found: {ENTRYPOINT}")

    for path in [BUILD_DIR, DIST_DIR]:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    if SPEC_FILE.exists():
        os.remove(SPEC_FILE)

    run_pyinstaller()
    print_result()


if __name__ == "__main__":
    main()
