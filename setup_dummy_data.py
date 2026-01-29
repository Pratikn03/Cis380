import os
import random
from PIL import Image, ImageDraw

def create_dummy_dataset(base_path="dataset"):
    # Define paths based on your data.yaml structure
    train_img_dir = os.path.join(base_path, "images", "train")
    val_img_dir = os.path.join(base_path, "images", "val")
    train_lbl_dir = os.path.join(base_path, "labels", "train")
    val_lbl_dir = os.path.join(base_path, "labels", "val")

    # Create directories
    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    def generate_samples(count, img_dir, lbl_dir):
        print(f"Generating {count} samples in {img_dir}...")
        for i in range(count):
            # 1. Create a blank white image
            img_name = f"sample_{i}.jpg"
            img_path = os.path.join(img_dir, img_name)
            
            w, h = 640, 640
            img = Image.new("RGB", (w, h), "white")
            draw = ImageDraw.Draw(img)
            
            # 2. Draw a "defect" (red rectangle) - Class 0 (Anomaly)
            # Randomly decide if this image has an anomaly (80% chance) or is normal (20%)
            if random.random() > 0.2:
                x1 = random.randint(50, 500)
                y1 = random.randint(50, 500)
                bw = random.randint(50, 100)
                bh = random.randint(50, 100)
                x2, y2 = x1 + bw, y1 + bh
                
                draw.rectangle([x1, y1, x2, y2], outline="red", width=5)
                
                # 3. Create Label File
                # YOLO format: class_id x_center y_center width height (normalized 0-1)
                lbl_name = f"sample_{i}.txt"
                lbl_path = os.path.join(lbl_dir, lbl_name)
                
                xc = (x1 + x2) / 2 / w
                yc = (y1 + y2) / 2 / h
                nw = bw / w
                nh = bh / h
                
                with open(lbl_path, "w") as f:
                    # Class 0 corresponds to 'anomaly' in your data.yaml
                    f.write(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
            
            # Save the image (normal images just won't have a label file, which YOLO accepts as background)
            img.save(img_path)

    generate_samples(20, train_img_dir, train_lbl_dir)
    generate_samples(5, val_img_dir, val_lbl_dir)
    print(f"\n✅ Success! Dummy dataset created in '{base_path}'.")

if __name__ == "__main__":
    create_dummy_dataset()