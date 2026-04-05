import os
# Fix for macOS libc++abi crash (mutex lock failed) related to OpenMP
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_POLL_STRATEGY'] = 'poll'
# Additional macOS fork safety fixes
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['no_proxy'] = '*'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

import json
import logging
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, DataCollatorForLanguageModeling, Trainer, TrainingArguments
from datasets import load_dataset
import random
from pathlib import Path

# Configure logging to write to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recommender_training.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def train_recommender():
    # Configuration
    base_dir = Path("data/raw")
    train_file = "training_data.txt"
    val_file = "validation_data.txt"
    model_output_dir = "custom_recommender_model"
    base_model = "distilgpt2"

    # 1. Prepare Data
    # Check if data exists, if not create dummy structure for demonstration
    if not base_dir.exists():
        logger.warning(f"⚠️ Data directory '{base_dir}' not found.")
        logger.info("Creating dummy data structure for demonstration...")
        categories = ["music", "movie", "games", "grocery"]
        for cat in categories:
            (base_dir / cat).mkdir(parents=True, exist_ok=True)
            with (base_dir / cat / "sample.txt").open("w") as f:
                f.write(f"Domain: {cat} | Content: This item is highly rated and popular among users.\n")
        logger.info("✅ Dummy data created.")

    logger.info(f"📦 Aggregating data from {base_dir}...")
    all_lines = []
    datasets_found = 0
    
    # Iterate over all subdirectories in data/raw as categories
    for category_path in base_dir.iterdir():
        if not category_path.is_dir():
            continue
            
        category = category_path.name.lower()
        logger.info(f"   - Processing category: {category}")
        datasets_found += 1
        
        for file_path in category_path.rglob("*"):
            if not file_path.is_file():
                continue
                
            try:
                content = ""
                if file_path.suffix == ".csv":
                    df = pd.read_csv(file_path)
                    # Convert rows to text representation
                    for _, row in df.iterrows():
                        row_text = " ".join([f"{k}: {v}" for k, v in row.items() if pd.notna(v)])
                        all_lines.append(f"Domain: {category} | Content: {row_text}\n")
                
                elif file_path.suffix == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                all_lines.append(f"Domain: {category} | Content: {str(item)}\n")
                        elif isinstance(data, dict):
                             all_lines.append(f"Domain: {category} | Content: {str(data)}\n")

                elif file_path.suffix in [".txt", ".md"]:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                all_lines.append(f"Domain: {category} | Content: {line.strip()}\n")
                
            except Exception as e:
                logger.error(f"❌ Error reading {file_path}: {e}")

    # Split Data (80% Train, 20% Validation)
    random.shuffle(all_lines)
    split_idx = int(len(all_lines) * 0.8)
    
    with open(train_file, "w", encoding="utf-8") as f:
        f.writelines(all_lines[:split_idx])
        
    with open(val_file, "w", encoding="utf-8") as f:
        f.writelines(all_lines[split_idx:])
        
    logger.info(f"✅ Data prepared: {len(all_lines[:split_idx])} training samples, {len(all_lines[split_idx:])} validation samples.")

    # 2. Initialize Model & Tokenizer
    logger.info(f"🚀 Loading {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(base_model)

    # 3. Prepare Dataset
    logger.info("📄 Processing dataset...")
    dataset = load_dataset("text", data_files={"train": train_file, "validation": val_file})
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)
    
    tokenized_datasets = dataset.map(tokenize_function, batched=True, num_proc=1)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # 4. Train
    training_args = TrainingArguments(
        output_dir="./runs/recommender",
        overwrite_output_dir=True,
        num_train_epochs=5, # Increased for better accuracy
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=500,
        save_total_limit=2,
        logging_steps=50,
        report_to="none",
        dataloader_num_workers=0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
    )

    logger.info("🏋️ Starting training...")
    trainer.train()

    # 5. Save
    logger.info(f"💾 Saving model to {model_output_dir}...")
    trainer.save_model(model_output_dir)
    tokenizer.save_pretrained(model_output_dir)
    logger.info("✅ Training complete!")

if __name__ == "__main__":
    train_recommender()