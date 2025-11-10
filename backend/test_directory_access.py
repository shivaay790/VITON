import os
import glob

# Set PROJECT_ROOT to the parent of ezyZip (i.e., 12_clothes_tryon)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CLOTHES_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'cloth')
PEOPLE_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'image')

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"CLOTHES_DIR: {CLOTHES_DIR}")
print(f"PEOPLE_DIR: {PEOPLE_DIR}")

print(f"\nCLOTHES_DIR exists: {os.path.exists(CLOTHES_DIR)}")
print(f"PEOPLE_DIR exists: {os.path.exists(PEOPLE_DIR)}")

if os.path.exists(CLOTHES_DIR):
    all_files = os.listdir(CLOTHES_DIR)
    jpg_files = [f for f in all_files if f.endswith('.jpg')]
    print(f"\nCLOTHES_DIR total files: {len(all_files)}")
    print(f"CLOTHES_DIR JPG files: {len(jpg_files)}")
    print(f"First 5 JPG files: {jpg_files[:5]}")
else:
    print(f"\n❌ CLOTHES_DIR does not exist!")

if os.path.exists(PEOPLE_DIR):
    all_files = os.listdir(PEOPLE_DIR)
    jpg_files = [f for f in all_files if f.endswith('.jpg')]
    print(f"\nPEOPLE_DIR total files: {len(all_files)}")
    print(f"PEOPLE_DIR JPG files: {len(jpg_files)}")
    print(f"First 5 JPG files: {jpg_files[:5]}")
else:
    print(f"\n❌ PEOPLE_DIR does not exist!")

# Test search functionality
print(f"\n=== Testing search functionality ===")
test_queries = ["all", "14684", "adidas", "shirt", ""]

for query in test_queries:
    if os.path.exists(CLOTHES_DIR):
        all_clothes = [f for f in os.listdir(CLOTHES_DIR) if f.endswith('.jpg')]
        if query.strip() and query.lower() != 'all':
            filtered_clothes = [f for f in all_clothes if query.lower() in f.lower()]
        else:
            filtered_clothes = all_clothes
        print(f"Query '{query}': {len(filtered_clothes)} results")
    else:
        print(f"Query '{query}': Directory not found") 