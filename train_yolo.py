from ultralytics import YOLO

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
    
    results = model.train(
        data="data.yaml",   # Path to your dataset config file
        epochs=50,          # Number of training epochs
        imgsz=640,          # Image resolution
        name="custom_yolo_model" # Name of the experiment (saved in runs/detect/)
    )

if __name__ == "__main__":
    main()