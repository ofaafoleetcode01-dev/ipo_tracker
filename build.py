import os
import shutil
import subprocess
import sys
import zipfile

# -----------------------------
# Paths (always relative to script location)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUILD_DIR = os.path.join(BASE_DIR, "build")
DIST_DIR = os.path.join(BASE_DIR, "dist")

SRC_DIR = os.path.join(BASE_DIR, "src")
ENTRY_FILE = os.path.join(BASE_DIR, "lambda_function.py")
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.yaml")

OUTPUT_ZIP = os.path.join(DIST_DIR, "lambda_function.zip")


# -----------------------------
# Helper
# -----------------------------
def run(cmd):
    print(f"> {' '.join(cmd)}")
    subprocess.check_call(cmd)


# -----------------------------
# Clean previous artifacts
# -----------------------------
def clean():
    print("Cleaning build artifacts...")

    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)

    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)


# -----------------------------
# Setup directories
# -----------------------------
def setup_dirs():
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)


# -----------------------------
# Install dependencies
# -----------------------------
def install_dependencies():
    if os.path.exists(REQUIREMENTS):
        print("Installing dependencies into build/...")

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
    else:
        print("No requirements.txt found, skipping dependencies.")


# -----------------------------
# Copy application files
# -----------------------------
def copy_source():
    print("Copying source files...")

    # Lambda entry point (must be root of zip)
    if os.path.exists(ENTRY_FILE):
        shutil.copy(ENTRY_FILE, BUILD_DIR)
    else:
        raise FileNotFoundError("lambda_function.py not found in project root")

    # src folder (preserve imports like: from src.main import ...)
    if os.path.exists(SRC_DIR):
        shutil.copytree(
            SRC_DIR,
            os.path.join(BUILD_DIR, "src"),
            dirs_exist_ok=True
        )
    else:
        print("Warning: src/ not found")

    # config.yaml (root level in Lambda)
    if os.path.exists(CONFIG_FILE):
        print("Copying config.yaml...")
        shutil.copy(CONFIG_FILE, BUILD_DIR)
    else:
        print("Warning: config.yaml not found")


# -----------------------------
# Create Lambda deployment ZIP
# -----------------------------
def create_zip():
    print(f"Creating deployment package: {OUTPUT_ZIP}")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                full_path = os.path.join(root, file)

                # IMPORTANT: Lambda requires root-relative paths
                arcname = os.path.relpath(full_path, BUILD_DIR)

                z.write(full_path, arcname)

    print(f"✅ ZIP created: {OUTPUT_ZIP}")


# -----------------------------
# Build pipeline
# -----------------------------
def main():
    clean()
    setup_dirs()
    install_dependencies()
    copy_source()
    create_zip()

    print("\n🎉 Build complete!")
    print(f"📦 Upload this file to AWS Lambda:")
    print(f"   {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()