from ultralytics import YOLO
import os
import yaml

def main():
    # 1. Initialize the Model
    # 'yolov8n.pt' is the Nano model (fastest, least accurate). 
    # Options: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
    model = YOLO("yolov8n.pt")

    # 2. Train the Model
    # This requires a 'data.yaml' file and a dataset folder structure.
    # Example data.yaml content:
    #   path: /absolute/path/to/dataset
    #   train: images/train
    #   val: images/val
    #   names:
    #     0: defect
    #     1: scratch
    
    # Verify dataset usage
    if os.path.exists("data.yaml"):
        with open("data.yaml", "r") as f:
            data_conf = yaml.safe_load(f)
            
        # Try to count images to reassure user
        try:
            base_path = data_conf.get("path", "")
            train_rel = data_conf.get("train", "")
            train_dir = os.path.join(base_path, train_rel) if not os.path.isabs(train_rel) else train_rel
            
            if os.path.exists(train_dir):
                count = len([x for x in os.listdir(train_dir) if x.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
                print(f"📊 Training on 100% of detected dataset: {count} images in '{train_dir}'")
        except Exception as e:
            print(f"⚠️ Could not verify dataset count: {e}")
    
    results = model.train(
        data="data.yaml",   # Path to your dataset config file
        epochs=100,         # Increased to 100 for Elite accuracy
        imgsz=640,          # Image resolution
        name="custom_yolo_model", # Name of the experiment (saved in runs/detect/)
        exist_ok=True       # Overwrite existing experiment folder
    )

if __name__ == "__main__":
    main()