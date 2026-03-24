#!/usr/bin/env python3

import os
import zipfile

SOURCE_DIR = "blender_latex_plugin"
OUTPUT_ZIP = "blender_latex_plugin.zip"


def create_zip():
    print(f"Packaging {SOURCE_DIR} into {OUTPUT_ZIP}...")

    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            # Skip __pycache__ directory
            if "__pycache__" in root:
                continue

            for file in files:
                # Skip hidden files
                if file.startswith("."):
                    continue

                file_path = os.path.join(root, file)

                # Ensure the folder structure is preserved inside the zip
                zipf.write(file_path, arcname=file_path)

    print("Build complete!")


if __name__ == "__main__":
    create_zip()
