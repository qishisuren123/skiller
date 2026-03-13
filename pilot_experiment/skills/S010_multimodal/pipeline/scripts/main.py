import argparse
import os
import json
import csv
import shutil
from PIL import Image
import pandas as pd
from collections import Counter

def validate_args(args):
    """Validate command line arguments"""
    if args.image_size <= 0:
        raise ValueError(f"Image size must be positive, got {args.image_size}")
    
    if not os.path.exists(args.input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {args.input_dir}")
    
    # Check for required subdirectories and files
    required_paths = [
        os.path.join(args.input_dir, 'images'),
        os.path.join(args.input_dir, 'texts'),
        os.path.join(args.input_dir, 'labels.csv')
    ]
    
    for path in required_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required path does not exist: {path}")

def preprocess_dataset(input_dir, output_dir, image_size):
    # Create output directories
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'texts'), exist_ok=True)
    
    # Load labels with validation
    try:
        labels_df = pd.read_csv(os.path.join(input_dir, 'labels.csv'))
        if 'sample_id' not in labels_df.columns or 'label' not in labels_df.columns:
            raise ValueError("labels.csv must contain 'sample_id' and 'label' columns")
        labels_dict = dict(zip(labels_df['sample_id'], labels_df['label']))
    except Exception as e:
        raise ValueError(f"Error reading labels.csv: {e}")
    
    manifest = []
    skipped_samples = []
    error_samples = []
    
    # Process each image
    images_dir = os.path.join(input_dir, 'images')
    texts_dir = os.path.join(input_dir, 'texts')
    
    for img_file in os.listdir(images_dir):
        if img_file.endswith('.jpg'):
            # Extract base filename and construct sample_id
            base_name = img_file.replace('.jpg', '')
            sample_id = f"sample_{base_name}"
            
            # Check if sample_id exists in labels
            if sample_id not in labels_dict:
                skipped_samples.append(f"{sample_id} (no label)")
                continue
            
            # Check if text file exists
            text_file = os.path.join(texts_dir, f"{base_name}.txt")
            if not os.path.exists(text_file):
                skipped_samples.append(f"{sample_id} (no text file)")
                continue
            
            try:
                # Process image with corruption check
                img_path = os.path.join(images_dir, img_file)
                img = Image.open(img_path)
                img.verify()  # Check for corruption
                img = Image.open(img_path)  # Reopen after verify
                original_size = img.size
                
                # Resize and save
                img_resized = img.resize((image_size, image_size))
                output_img_path = os.path.join(output_dir, 'images', f"{sample_id}.png")
                img_resized.save(output_img_path)
                
                # Process and copy text
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # Copy text file to output directory
                output_text_path = os.path.join(output_dir, 'texts', f"{sample_id}.txt")
                shutil.copy2(text_file, output_text_path)
                
                word_count = len(text_content.split())
                char_count = len(text_content)
                
                # Add to manifest with relative paths
                manifest.append({
                    'sample_id': sample_id,
                    'image_path': f"images/{sample_id}.png",
                    'text_path': f"texts/{sample_id}.txt",
                    'label': labels_dict[sample_id],
                    'word_count': word_count,
                    'char_count': char_count,
                    'original_image_size': original_size
                })
                
            except Exception as e:
                error_samples.append(f"{sample_id}: {e}")
    
    # Save manifest
    with open(os.path.join(output_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Print summary with zero-division protection
    total_samples = len(manifest)
    print(f"Total samples processed: {total_samples}")
    print(f"Skipped samples: {len(skipped_samples)}")
    print(f"Error samples: {len(error_samples)}")
    
    if total_samples > 0:
        labels = [item['label'] for item in manifest]
        label_dist = Counter(labels)
        avg_word_count = sum(item['word_count'] for item in manifest) / total_samples
        
        print(f"Label distribution: {dict(label_dist)}")
        print(f"Average word count: {avg_word_count:.2f}")
    else:
        print("No samples were successfully processed!")
        if skipped_samples:
            print("Skipped:", skipped_samples[:5])
        if error_samples:
            print("Errors:", error_samples[:5])

def main():
    parser = argparse.ArgumentParser(description='Preprocess multimodal biology dataset')
    parser.add_argument('--input-dir', required=True, help='Root input directory')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--image-size', type=int, default=224, help='Target image size (must be positive)')
    
    args = parser.parse_args()
    
    try:
        validate_args(args)
        preprocess_dataset(args.input_dir, args.output_dir, args.image_size)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
