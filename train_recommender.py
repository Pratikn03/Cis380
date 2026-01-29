import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, DataCollatorForLanguageModeling, Trainer, TrainingArguments
from datasets import load_dataset
import random

def train_recommender():
    # Configuration
    base_dir = "data/raw/recommendation"
    train_file = "training_data.txt"
    val_file = "validation_data.txt"
    model_output_dir = "custom_recommender_model"
    base_model = "distilgpt2"

    # 1. Prepare Data
    # Check if data exists, if not create dummy structure for demonstration
    if not os.path.exists(base_dir):
        print(f"⚠️ Data directory '{base_dir}' not found.")
        print("Creating dummy data structure for demonstration...")
        categories = ["music", "movie", "games", "grocery"]
        for cat in categories:
            os.makedirs(os.path.join(base_dir, cat), exist_ok=True)
            with open(os.path.join(base_dir, cat, "sample.txt"), "w") as f:
                f.write(f"Recommendation for {cat}: This item is highly rated and popular among users.\n")
        print("✅ Dummy data created.")

    print(f"📦 Aggregating data from {base_dir}...")
    all_lines = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                content = ""
                if file.endswith(".csv"):
                    df = pd.read_csv(file_path)
                    # Concatenate all columns as text
                    content = df.to_string(index=False, header=False)
                elif file.endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                
                if content:
                    # Normalize newlines and add to list
                    all_lines.append(content.replace('\n', ' ') + "\n")
            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")

    # Split Data (80% Train, 20% Validation)
    random.shuffle(all_lines)
    split_idx = int(len(all_lines) * 0.8)
    
    with open(train_file, "w", encoding="utf-8") as f:
        f.writelines(all_lines[:split_idx])
        
    with open(val_file, "w", encoding="utf-8") as f:
        f.writelines(all_lines[split_idx:])
        
    print(f"✅ Data prepared: {len(all_lines[:split_idx])} training samples, {len(all_lines[split_idx:])} validation samples.")

    # 2. Initialize Model & Tokenizer
    print(f"🚀 Loading {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(base_model)

    # 3. Prepare Dataset
    print("📄 Processing dataset...")
    dataset = load_dataset("text", data_files={"train": train_file, "validation": val_file})
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
    
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # 4. Train
    training_args = TrainingArguments(
        output_dir="./runs/recommender",
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=500,
        save_total_limit=2,
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
    )

    print("🏋️ Starting training...")
    trainer.train()

    # 5. Save
    print(f"💾 Saving model to {model_output_dir}...")
    trainer.save_model(model_output_dir)
    tokenizer.save_pretrained(model_output_dir)
    print("✅ Training complete!")

if __name__ == "__main__":
    train_recommender()