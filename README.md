# 🛠 RushFiles Restore Tool

A Python-based tool for restoring files from RushFiles

This tool is designed to help recover lost data after cloud sync issues. It automatically matches `.file` and `.RFMETA` pairs, reconstructs the original folder structure, renames the files to their correct names, and restores their timestamps.

---

What It Does

- ✅ Parses `.RFMETA` files to extract original file names and paths
- ✅ Matches `.file` blobs with the correct metadata
- ✅ Recreates original folder hierarchy under the source folder
- ✅ Renames and moves each file to its proper location
- ✅ Restores the original timestamp (creation time)
- ✅ Removes the hidden attribute from restored files
- ✅ Logs skipped files with detailed reasons

## Requirements

- Python 3.x
- [`tqdm`](https://pypi.org/project/tqdm/) for progress bars (`pip install tqdm`)
