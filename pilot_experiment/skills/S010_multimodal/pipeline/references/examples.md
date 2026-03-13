# Sample ID conversion pattern
base_name = img_file.replace('.jpg', '')  # "001.jpg" -> "001"
sample_id = f"sample_{base_name}"         # "001" -> "sample_001"

# Safe dictionary lookup
if sample_id not in labels_dict:
    skipped_samples.append(f"{sample_id} (no label)")
    continue
label = labels_dict[sample_id]

# Image corruption check
try:
    img = Image.open(img_path)
    img.verify()  # Verify integrity
    img = Image.open(img_path)  # Reopen for processing
    # ... process image
except Exception as e:
    error_samples.append(f"{sample_id}: {e}")

# Zero-division protection
if total_samples > 0:
    avg_word_count = sum(item['word_count'] for item in manifest) / total_samples
else:
    print("No samples processed!")

# Relative path creation for portability
manifest_entry = {
    'image_path': f"images/{sample_id}.png",  # Relative path
    'text_path': f"texts/{sample_id}.txt"     # Relative path
}
