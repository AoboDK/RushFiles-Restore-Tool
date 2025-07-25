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
    except:
        pass  # Quiet failure

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
    except:
        pass  # Quiet failure

# Main process
def restore_files_with_structure(folder_path):
    """Restore files based on ``.RFMETA`` data located in ``folder_path``.

    The function recreates the original directory structure and moves data
    files accordingly. Destination paths are validated to ensure that they do
    not escape the provided ``folder_path``.
    """
    folder_path = os.path.normpath(folder_path.strip())
    files = os.listdir(folder_path)
    files_without_extension = [f for f in files if '.' not in f]
    rfmeta_files = [f for f in files if f.lower().endswith('.rfmeta')]
    renamed_files = 0
    skipped_files = []

    for file in tqdm(files_without_extension, desc="Restoring", ncols=75):
        base_name = file
        matching_rfmeta = None

        for rfmeta in rfmeta_files:
            if base_name in rfmeta:
                matching_rfmeta = rfmeta
                break

        if matching_rfmeta:
            meta_path = os.path.join(folder_path, matching_rfmeta)
            data_path = os.path.join(folder_path, base_name)
            try:
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)

                dest_folder = metadata.get("ArchivedFullName")
                timestamp = metadata.get("CreationTime")
                public_name = metadata.get("PublicName")

                if not dest_folder or not public_name:
                    skipped_files.append(f"{base_name} - Missing destination folder or name")
                    continue

                target_dir = os.path.join(folder_path, safe_path(dest_folder))
                normalized_target = os.path.normpath(target_dir)

                # Abort if normalized path escapes the base folder
                if os.path.commonpath([folder_path, normalized_target]) != folder_path:
                    skipped_files.append(f"{base_name} - Invalid destination path")
                    continue

                os.makedirs(normalized_target, exist_ok=True)

                final_name = generate_unique_name(normalized_target, public_name)
                final_path = os.path.join(normalized_target, final_name)

                shutil.move(data_path, final_path)
                remove_hidden_attribute(final_path)
                if timestamp:
                    apply_original_timestamp(final_path, timestamp)

                os.remove(meta_path)
                renamed_files += 1

            except Exception as e:
                skipped_files.append(f"{base_name} - Error: {e}")
        else:
            skipped_files.append(f"{base_name} - No matching .RFMETA file")

    # Log skipped files
    log_path = os.path.join(folder_path, "skipped_files_detailed.log")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("\n".join(skipped_files))

    # Final summary
    print("\n\n========== RESTORE SUMMARY ==========")
    print(f"Files processed     : {len(files_without_extension)}")
    print(f"Files restored      : {renamed_files}")
    print(f"Files skipped       : {len(skipped_files)}")
    print(f"Skipped log written : {log_path}")
    print("=====================================")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    folder_path = input("Enter the folder path containing the files: ").strip()
    if os.path.exists(folder_path):
        restore_files_with_structure(folder_path)
    else:
        print(f"The folder path '{folder_path}' does not exist.")
        input("\nPress Enter to exit...")
