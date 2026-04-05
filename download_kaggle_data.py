import os
import kaggle
import shutil
import random

def download_and_replace_dataset():
    # Configuration
    dataset_name = "mhskjelvareid/dagm-2007-competition-dataset"
    base_path = "dataset"
    temp_path = "temp_kaggle_download"

    print(f"🚀 Starting dataset replacement process...")

    # 1. Clean up existing 'dataset' folder (removes dummy data)
    if os.path.exists(base_path):
        print(f"🗑️ Removing existing '{base_path}' folder...")
        shutil.rmtree(base_path)
    
    # Re-create directory structure for YOLO
    train_img_dir = os.path.join(base_path, "images", "train")
    val_img_dir = os.path.join(base_path, "images", "val")
    train_lbl_dir = os.path.join(base_path, "labels", "train")
    val_lbl_dir = os.path.join(base_path, "labels", "val")
    
    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    # 2. Download from Kaggle
    print(f"⬇️ Downloading {dataset_name} from Kaggle...")
    try:
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(dataset_name, path=temp_path, unzip=True)
        print("✅ Download and extraction complete.")
    except Exception as e:
        print(f"❌ Kaggle Download Error: {e}")
        print("Ensure you have your 'kaggle.json' in ~/.kaggle/ and internet access.")
        return

    # 3. Organize Images into Train/Val
    print("📦 Organizing images...")
    all_images = []
    # Walk through the temp folder to find all images
    for root, dirs, files in os.walk(temp_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif')):
                all_images.append(os.path.join(root, file))
    
    if not all_images:
        print("❌ No images found in the downloaded dataset.")
        return

    # Shuffle and Split (80% Train, 20% Val)
    random.shuffle(all_images)
    split_idx = int(len(all_images) * 0.8)
    train_files = all_images[:split_idx]
    val_files = all_images[split_idx:]

    # Move files to destination
    labels_found = 0
    for src in train_files:
        shutil.move(src, os.path.join(train_img_dir, os.path.basename(src)))
        # Check for corresponding label file
        label_src = os.path.splitext(src)[0] + ".txt"
        if os.path.exists(label_src):
            shutil.move(label_src, os.path.join(train_lbl_dir, os.path.basename(label_src)))
            labels_found += 1
    
    for src in val_files:
        shutil.move(src, os.path.join(val_img_dir, os.path.basename(src)))
        # Check for corresponding label file
        label_src = os.path.splitext(src)[0] + ".txt"
        if os.path.exists(label_src):
            shutil.move(label_src, os.path.join(val_lbl_dir, os.path.basename(label_src)))
            labels_found += 1

    # 4. Cleanup Temp Folder
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)

    print(f"\n🎉 Dataset replaced successfully!")
    print(f"   - Train Images: {len(train_files)} -> {train_img_dir}")
    print(f"   - Val Images:   {len(val_files)}   -> {val_img_dir}")
    print(f"   - Labels Found: {labels_found}")
    
    if labels_found == 0:
        print("\n⚠️ IMPORTANT: No YOLO format labels (.txt files) were found.")
        print("   If you run training now, these will be treated as 'background' (negative) samples.")
    else:
        print("\n✅ Labels detected! You are ready to train.")

if __name__ == "__main__":
    download_and_replace_dataset()