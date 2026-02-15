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

    # Check if data already exists (to avoid overwriting user's 100% dataset)
    if any(os.scandir(train_img_dir)):
        print(f"ℹ️  Data detected in '{train_img_dir}'. Skipping dummy generation to use existing dataset.")
        # We still ensure data.yaml exists below
    else:
        def generate_samples(count, img_dir, lbl_dir):
            print(f"Generating {count} samples in {img_dir}...")
            for i in range(count):
                # 1. Create a blank white image
                img_name = f"sample_{i}.jpg"
                img_path = os.path.join(img_dir, img_name)
                
                w, h = 640, 640
                # Add slight noise/color to background to make it realistic
                bg_color = (random.randint(240, 255), random.randint(240, 255), random.randint(240, 255))
                img = Image.new("RGB", (w, h), bg_color)
                draw = ImageDraw.Draw(img)
                
                # 2. Decide Class: 30% Normal (No label), 70% Defect
                # Classes: 0=Crack, 1=Dent, 2=Scratch
                if random.random() > 0.3:
                    x1 = random.randint(50, 500)
                    y1 = random.randint(50, 500)
                    bw = random.randint(50, 100)
                    bh = random.randint(50, 100)
                    x2, y2 = x1 + bw, y1 + bh
                    
                    defect_type = random.choice([0, 1, 2])
                    
                    if defect_type == 0: # Crack (Jagged line)
                        draw.line([(x1, y1), (x1+20, y1+40), (x2, y2)], fill="black", width=3)
                    elif defect_type == 1: # Dent (Ellipse)
                        draw.ellipse([x1, y1, x2, y2], outline="gray", width=4)
                    elif defect_type == 2: # Scratch (Thin lines)
                        draw.line([(x1, y1), (x2, y2)], fill="gray", width=2)
                        draw.line([(x1+10, y1), (x2+10, y2)], fill="gray", width=2)
                    
                    # 3. Create Label File
                    # YOLO format: class_id x_center y_center width height (normalized 0-1)
                    lbl_name = f"sample_{i}.txt"
                    lbl_path = os.path.join(lbl_dir, lbl_name)
                    
                    xc = (x1 + x2) / 2 / w
                    yc = (y1 + y2) / 2 / h
                    nw = bw / w
                    nh = bh / h
                    
                    with open(lbl_path, "w") as f:
                        f.write(f"{defect_type} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
                
                # Save the image (normal images just won't have a label file, which YOLO accepts as background)
                img.save(img_path)

        # Generate more samples for "Elite" training
        generate_samples(100, train_img_dir, train_lbl_dir)
        generate_samples(20, val_img_dir, val_lbl_dir)
        print(f"\n✅ Success! Dummy dataset created in '{base_path}'.")
    
    # 4. Create data.yaml for YOLO training
    yaml_content = f"""
path: {os.path.abspath(base_path)} # dataset root dir
train: images/train
val: images/val

names:
  0: crack
  1: dent
  2: scratch
"""
    with open("data.yaml", "w") as f:
        f.write(yaml_content.strip())
    print("✅ Created 'data.yaml' configuration file ready for training.")

if __name__ == "__main__":
    create_dummy_dataset()