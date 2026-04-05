import os
import sys

# Force environment variables for macOS stability BEFORE other imports
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_POLL_STRATEGY'] = 'poll'
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
    print("========================================")
    print("🏥 SYSTEM SANITY CHECK")
    print("========================================")

    # 1. Check Environment Variables
    print("\n1️⃣  Checking Environment Variables...")
    vars_to_check = [
        'KMP_DUPLICATE_LIB_OK', 'TOKENIZERS_PARALLELISM', 
        'OMP_NUM_THREADS', 'GRPC_ENABLE_FORK_SUPPORT',
        'GRPC_POLL_STRATEGY', 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY'
    ]
    for v in vars_to_check:
        val = os.environ.get(v, 'NOT SET')
        print(f"   • {v}: {val}")

    # 2. Check Data
    print("\n2️⃣  Checking Data Availability...")
    data_path = Path("data/raw")
    if data_path.exists():
        files = list(data_path.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        print(f"   • Data directory found at: {data_path}")
        print(f"   • Total files found: {file_count}")
        if file_count == 0:
            print("   ⚠️  Warning: Data directory exists but is empty.")
    else:
        print(f"   ❌ Error: Data directory not found at {data_path}")

    # 3. Check Model Loading & Forward Pass
    print("\n3️⃣  Checking Model & Forward Pass (DistilGPT2)...")
    try:
        model_name = "distilgpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        test_input = "Sanity check test."
        inputs = tokenizer(test_input, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
        print(f"   ✅ Success! Model loaded and forward pass complete. Loss: {outputs.loss.item():.4f}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        sys.exit(1)

    print("\n========================================")
    print("🎉 SANITY CHECK PASSED")
    print("You are ready to run the full training.")
    print("========================================")

if __name__ == "__main__":
    main()