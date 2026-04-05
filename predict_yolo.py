from ultralytics import YOLO
import os

def main():
    # 1. Locate the trained model
    # Note: If you ran training multiple times, check runs/detect/ for the latest folder (e.g., custom_yolo_model2)
    model_path = "runs/detect/custom_yolo_model/weights/best.pt"
    
    # Fallback to checking if a numbered folder exists if the base one doesn't
    if not os.path.exists(model_path):
        # Try to find the latest run automatically
        detect_dir = "runs/detect"
        if os.path.exists(detect_dir):
            runs = sorted([d for d in os.listdir(detect_dir) if d.startswith("custom_yolo_model")])
            if runs:
                model_path = os.path.join(detect_dir, runs[-1], "weights", "best.pt")

    if not os.path.exists(model_path):
        print(f"❌ Error: Model not found at {model_path}. Please check your training logs.")
        return

    print(f"✅ Loading model from: {model_path}")
    model = YOLO(model_path)

    # 2. Select a test image
    image_path = "dataset/images/val/sample_0.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Test image not found at {image_path}. Did you run setup_dummy_data.py?")
        return

    # 3. Run Inference
    results = model.predict(image_path, save=True, conf=0.25)
    print(f"✅ Prediction saved to: {results[0].save_dir}")

if __name__ == "__main__":
    main()