import os
import json
import shutil
import ctypes
from datetime import datetime
from tqdm import tqdm

# Generate unique filename if needed
def generate_unique_name(folder_path, new_name):
    base, ext = os.path.splitext(new_name)
    counter = 1
    while os.path.exists(os.path.join(folder_path, new_name)):
        new_name = f"{base} ({counter}){ext}"
        counter += 1
    return new_name

# Apply original timestamp
def apply_original_timestamp(dest_file, timestamp):
    try:
        from dateutil.parser import isoparse
        dt = isoparse(timestamp)
        ts = dt.timestamp()
        os.utime(dest_file, (ts, ts))
    except Exception as e:
        tqdm.write(f"Failed to apply timestamp to {dest_file}: {e}")

# Normalize path safely
def safe_path(path):
    return os.path.normpath(path.strip().replace("\\", os.sep).replace("/", os.sep))

# Unhide file on Windows
def remove_hidden_attribute(file_path):
    try:
        if os.name == 'nt':
            FILE_ATTRIBUTE_HIDDEN = 0x02
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
            if attrs & FILE_ATTRIBUTE_HIDDEN:
                ctypes.windll.kernel32.SetFileAttributesW(str(file_path), attrs & ~FILE_ATTRIBUTE_HIDDEN)
    except Exception as e:
        tqdm.write(f"Failed to remove hidden attribute from {file_path}: {e}")

# Main process

def restore_files_with_structure(folder_path):
    files = os.listdir(folder_path)
    files_without_extension = [f for f in files if '.' not in f]
    rfmeta_files = [f for f in files if f.lower().endswith('.rfmeta')]
    meta_map = {rfm.split('.')[0]: rfm for rfm in rfmeta_files}
    renamed_files = 0
    skipped_files = []

    print(f"Files in folder: {len(files)}")
    print(f"Files without extension: {len(files_without_extension)}")
    print(f".RFMETA files: {len(rfmeta_files)}")

    for file in tqdm(files_without_extension, desc="Restoring"):
        base_name = file
        matching_rfmeta = meta_map.get(base_name)

        if matching_rfmeta:
            meta_path = os.path.join(folder_path, matching_rfmeta)
            data_path = os.path.join(folder_path, base_name)
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                dest_folder = metadata.get("ArchivedFullName")
                timestamp = metadata.get("CreationTime")
                public_name = metadata.get("PublicName")

                if not dest_folder or not public_name:
                    skipped_files.append(f"{base_name} - Missing destination folder or name in {matching_rfmeta}")
                    continue

                rel_path = safe_path(dest_folder)
                target_dir = os.path.join(folder_path, rel_path)
                os.makedirs(target_dir, exist_ok=True)

                final_name = generate_unique_name(target_dir, public_name)
                final_path = os.path.join(target_dir, final_name)

                shutil.move(data_path, final_path)
                remove_hidden_attribute(final_path)
                if timestamp:
                    apply_original_timestamp(final_path, timestamp)

                os.remove(meta_path)
                renamed_files += 1
                tqdm.write(f"Restored: {final_path}")

            except Exception as e:
                skipped_files.append(f"{base_name} - Error during processing: {e}")
        else:
            skipped_files.append(f"{base_name} - No matching .RFMETA file found")

    with open(os.path.join(folder_path, "skipped_files_detailed.log"), "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(skipped_files))

    print("\nRestoration completed.")
    print(f"Files restored: {renamed_files}")
    print(f"Files skipped: {len(skipped_files)} (see skipped_files_detailed.log)")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing the files: ").strip()
    if os.path.exists(folder_path):
        restore_files_with_structure(folder_path)
    else:
        print(f"The folder path '{folder_path}' does not exist.")
        input("\nPress Enter to exit...")
