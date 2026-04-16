import os
import shutil
import subprocess
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")

SRC_DIR = os.path.join(BASE_DIR, "src")
ENTRY_FILE = os.path.join(BASE_DIR, "lambda_function.py")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")

OUTPUT_ZIP = os.path.join(DIST_DIR, "lambda_function.zip")


def run(cmd):
    print(f"> {' '.join(cmd)}")
    subprocess.check_call(cmd)


# -----------------------------
# Parse args
# -----------------------------
def parse_args():
    mode = "full"
    no_dist = False

    for arg in sys.argv[1:]:
        if arg.lower() == "fast":
            mode = "fast"
        elif arg == "--no-dist":
            no_dist = True

    return mode, no_dist


# -----------------------------
# Clean
# -----------------------------
def clean(full=True, skip_dist=False):
    if full:
        print("Full clean...")
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)
    else:
        print("Fast mode: keeping build/")

    if not skip_dist:
        if os.path.exists(DIST_DIR):
            print("Cleaning dist/...")
            shutil.rmtree(DIST_DIR)
    else:
        print("Skipping dist cleanup (--no-dist)")


# -----------------------------
# Setup dirs
# -----------------------------
def setup_dirs(skip_dist=False):
    os.makedirs(BUILD_DIR, exist_ok=True)
    if not skip_dist:
        os.makedirs(DIST_DIR, exist_ok=True)


# -----------------------------
# Dependencies
# -----------------------------
def install_dependencies(skip=False):
    if skip:
        print("Skipping dependency install (fast mode)")
        return

    if os.path.exists(REQUIREMENTS):
        print("Installing dependencies...")
        run([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            REQUIREMENTS,
            "-t",
            BUILD_DIR
        ])


# -----------------------------
# Copy code
# -----------------------------
def copy_source():
    print("Copying source files...")

    shutil.copy(ENTRY_FILE, BUILD_DIR)

    target_src = os.path.join(BUILD_DIR, "src")
    if os.path.exists(target_src):
        shutil.rmtree(target_src)

    shutil.copytree(SRC_DIR, target_src)

    if os.path.exists(CONFIG_FILE):
        shutil.copy(CONFIG_FILE, BUILD_DIR)


# -----------------------------
# Zip
# -----------------------------
def create_zip(skip=False):
    if skip:
        print("Skipping ZIP creation (--no-dist)")
        return

    print(f"Creating ZIP: {OUTPUT_ZIP}")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, BUILD_DIR)
                z.write(full_path, arcname)

    print("✅ ZIP ready")


# -----------------------------
# Main
# -----------------------------
def main():
    mode, no_dist = parse_args()
    fast_mode = mode == "fast"

    print(f"Mode: {mode.upper()}")
    print(f"Skip dist: {no_dist}")

    clean(full=not fast_mode, skip_dist=no_dist)
    setup_dirs(skip_dist=no_dist)
    install_dependencies(skip=fast_mode)
    copy_source()
    create_zip(skip=no_dist)

    print("\n🎉 Build complete!")


if __name__ == "__main__":
    main()