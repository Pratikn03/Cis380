import os
import math
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def evaluate_model():
    model_path = "custom_recommender_model"
    # Ideally, use a separate validation file. For now, we check how well it learned the training data.
    data_file = "combined_training_data.txt" 

    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}. Please run train_recommender.py first.")
        return

    print(f"🚀 Loading model from {model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # 1. Qualitative Evaluation (Generation)
    print("\n--- 🧠 Qualitative Evaluation (Sample Generations) ---")
    prompts = [
        "Recommendation for music:",
        "Recommendation for movie:",
        "Context: I feel happy.\nRecommendation:",
        "Context: Fire detected.\nRecommendation:"
    ]
    
    model.eval()
    for prompt in prompts:
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            # Generate text
            outputs = model.generate(
                **inputs, 
                max_new_tokens=50, 
                num_return_sequences=1, 
                pad_token_id=tokenizer.eos_token_id,
                do_sample=True, # Add some randomness to see variety
                temperature=0.7
            )
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\n🔹 Prompt: {prompt.strip()}")
        print(f"🔸 Result: {generated_text.replace(prompt, '').strip()}")

    # 2. Quantitative Evaluation (Perplexity)
    print("\n--- 📊 Quantitative Evaluation (Perplexity) ---")
    if os.path.exists(data_file):
        print(f"Calculating perplexity on {data_file}...")
        with open(data_file, encoding='utf-8') as f:
            text = f.read()
            
        encodings = tokenizer(text, return_tensors='pt')
        max_length = model.config.n_positions
        stride = 512
        seq_len = encodings.input_ids.size(1)

        nlls = []
        prev_end_loc = 0
        for begin_loc in range(0, seq_len, stride):
            end_loc = min(begin_loc + max_length, seq_len)
            trg_len = end_loc - prev_end_loc 
            input_ids = encodings.input_ids[:, begin_loc:end_loc]
            target_ids = input_ids.clone()
            target_ids[:, :-trg_len] = -100

            with torch.no_grad():
                outputs = model(input_ids, labels=target_ids)
                # Neg Log Likelihood
                nlls.append(outputs.loss)

            prev_end_loc = end_loc
            if end_loc == seq_len:
                break

        ppl = math.exp(torch.stack(nlls).mean())
        print(f"📈 Perplexity: {ppl:.2f}")
        print("(Lower is better. < 20 is usually good for specific domains, < 10 is excellent)")
    else:
        print(f"⚠️ Data file {data_file} not found, skipping perplexity calculation.")

if __name__ == "__main__":
    evaluate_model()