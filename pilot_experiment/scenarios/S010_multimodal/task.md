Write a Python CLI script to preprocess a multimodal biology dataset for model training.

Input directory structure:
- images/: contains .jpg files
- texts/: contains .txt files (one per sample, matching image names)
- labels.csv: columns sample_id, label

Requirements:
1. Use argparse: --input-dir root directory, --output-dir processed directory, --image-size (default 224)
2. For each image: load, resize to (image_size, image_size), save as PNG in output_dir/images/
3. For each text: read, compute word count and character count
4. Generate manifest.json: list of {sample_id, image_path, text_path, label, word_count, char_count, original_image_size}
5. Print summary: total samples, label distribution, average word count
