import os
import ast

def main():
    print("==================================================")
    print("🤖 MODEL TRAINING METRICS REPORT")
    print("==================================================")

    # 1. Recommender Model
    print("\n1️⃣  Recommender Model (DistilGPT2)")
    log_path = "recommender_training.log"
    
    if os.path.exists(log_path):
        losses = []
        with open(log_path, "r") as f:
            for line in f:
                # Hugging Face Trainer logs look like dictionaries: {'loss': 3.5, 'epoch': 1.0 ...}
                if "'loss':" in line and "'epoch':" in line:
                    try:
                        # Extract the dictionary part from the log line
                        start = line.find("{")
                        end = line.rfind("}") + 1
                        if start != -1 and end != -1:
                            dict_str = line[start:end]
                            metrics = ast.literal_eval(dict_str)
                            losses.append(metrics)
                    except Exception:
                        pass
        
        if losses:
            first = losses[0]
            last = losses[-1]
            print("   • Status:       ✅ Trained")
            print(f"   • Initial Loss: {first.get('loss', 'N/A'):.4f}")
            print(f"   • Final Loss:   {last.get('loss', 'N/A'):.4f}")
            print(f"   • Epochs:       {last.get('epoch', 'N/A')}")
            print("\n   ℹ️  Note: For Generative Models, we use 'Loss' instead of 'Accuracy'.")
            print("       Loss < 2.0 is generally good. Loss < 1.0 is excellent.")
        else:
            print("   • Status:       ⚠️ Log file found, but no metrics data detected.")
    else:
        print("   • Status:       ❌ Not trained yet (recommender_training.log not found).")

    # 2. Vision Model (YOLO)
    print("\n2️⃣  Vision Model (YOLOv8)")
    yolo_csv = "runs/detect/custom_yolo_model/results.csv"
    
    if os.path.exists(yolo_csv):
        try:
            with open(yolo_csv, "r") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    headers = [h.strip() for h in lines[0].split(",")]
                    last_vals = [v.strip() for v in lines[-1].split(",")]
                    data = dict(zip(headers, last_vals))
                    
                    # Extract key metrics (headers vary slightly by version, looking for partial matches)
                    epoch = data.get("epoch", "?")
                    map50 = next((v for k, v in data.items() if "mAP50" in k and "95" not in k), "N/A")
                    map5095 = next((v for k, v in data.items() if "mAP50-95" in k), "N/A")
                    
                    print("   • Status:       ✅ Trained")
                    print(f"   • Epochs:       {epoch}")
                    print(f"   • mAP@50:       {map50}")
                    print(f"   • mAP@50-95:    {map5095}")
                else:
                    print("   • Status:       ⚠️ Training started but no results yet.")
        except Exception as e:
             print(f"   • Status:       ⚠️ Error reading results: {e}")
    else:
        print("   • Status:       ❌ Not trained yet (runs/detect/custom_yolo_model/results.csv not found).")
        print("   • Action:       Run 'python setup_dummy_data.py' then 'python train_yolo.py'")

    # 3. Other Models
    print("\n3️⃣  Other Models (Fraud, Cyber, Voice)")
    print("   • Status:       Pre-trained / Heuristic")
    print("   • Accuracy:     N/A (These use logic defined in orchestrator.py, not local training)")

    print("\n==================================================")

if __name__ == "__main__":
    main()
