import os

def analyze_data_folder(base_dir="data"):
    print(f"🔍 Analyzing '{base_dir}' directory...")
    
    if not os.path.exists(base_dir):
        print(f"❌ Directory '{base_dir}' does not exist.")
        # Create it so the user sees where to put data
        os.makedirs(os.path.join(base_dir, "raw", "recommendation"), exist_ok=True)
        print(f"   Created '{base_dir}/raw/recommendation' for you. Please place your music/movie/game folders there.")
        return

    file_counts = {}
    total_files = 0
    
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        
        for f in files:
            total_files += 1
            ext = os.path.splitext(f)[1].lower()
            file_counts[ext] = file_counts.get(ext, 0) + 1
            
            # Preview specific files (limit output)
            if total_files <= 20: 
                print(f"{subindent}📄 {f}")
                
    print("\n📊 Summary:")
    print(f"Total Files: {total_files}")
    for ext, count in file_counts.items():
        print(f"  {ext}: {count}")

    # Check specific readiness for recommender training
    rec_path = os.path.join(base_dir, "raw", "recommendation")
    if os.path.exists(rec_path):
        print(f"\n✅ Recommendation data found at '{rec_path}'")
        files_found = []
        for root, _, files in os.walk(rec_path):
            for f in files:
                if f.endswith(('.txt', '.csv')):
                    files_found.append(os.path.join(root, f))
        
        if files_found:
            print(f"   - Found {len(files_found)} text/csv files ready for aggregation.")
            print("   - You can run 'python train_recommender.py' now.")
        else:
            print("   ⚠️  Folder exists but contains no .txt or .csv files.")
    else:
        print(f"\n⚠️ Recommendation data folder '{rec_path}' not found.")

if __name__ == "__main__":
    analyze_data_folder()