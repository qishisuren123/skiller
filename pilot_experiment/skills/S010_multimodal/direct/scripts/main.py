#!/usr/bin/env python3
"""
Multimodal Biology Dataset Preprocessing CLI
Preprocesses images and texts for ML model training
"""

import argparse
import os
import json
from pathlib import Path
from collections import Counter
import pandas as pd
from PIL import Image
import numpy as np

def parse_arguments():
    parser = argparse.ArgumentParser(description='Preprocess multimodal biology dataset')
    parser.add_argument('--input-dir', required=True, help='Root directory containing images/, texts/, labels.csv')
    parser.add_argument('--output-dir', required=True, help='Output directory for processed data')
    parser.add_argument('--image-size', type=int, default=224, help='Target image size (default: 224)')
    return parser.parse_args()

def validate_input_structure(input_dir):
    """Validate that input directory has required structure"""
    required_paths = ['images', 'texts', 'labels.csv']
    for path in required_paths:
        full_path = os.path.join(input_dir, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Required path not found: {full_path}")
    print(f"✓ Input directory structure validated")

def load_labels(input_dir):
    """Load labels.csv and return sample_id to label mapping"""
    labels_path = os.path.join(input_dir, 'labels.csv')
    try:
        df = pd.read_csv(labels_path)
        if 'sample_id' not in df.columns or 'label' not in df.columns:
            raise ValueError("labels.csv must contain 'sample_id' and 'label' columns")
        return dict(zip(df['sample_id'], df['label']))
    except Exception as e:
        raise ValueError(f"Error loading labels.csv: {e}")

def get_valid_samples(input_dir, labels_dict):
    """Find samples that have both image and text files"""
    images_dir = os.path.join(input_dir, 'images')
    texts_dir = os.path.join(input_dir, 'texts')
    
    # Get sample IDs from filenames (remove extensions)
    image_samples = {Path(f).stem for f in os.listdir(images_dir) if f.endswith('.jpg')}
    text_samples = {Path(f).stem for f in os.listdir(texts_dir) if f.endswith('.txt')}
    label_samples = set(labels_dict.keys())
    
    # Find intersection of all three
    valid_samples = image_samples & text_samples & label_samples
    
    print(f"Found {len(image_samples)} images, {len(text_samples)} texts, {len(label_samples)} labels")
    print(f"Valid complete samples: {len(valid_samples)}")
    
    if len(valid_samples) == 0:
        raise ValueError("No valid samples found with matching image, text, and label")
    
    return valid_samples

def setup_output_directory(output_dir):
    """Create output directory structure"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, 'images').mkdir(exist_ok=True)
    Path(output_dir, 'texts').mkdir(exist_ok=True)
    print(f"✓ Output directory structure created: {output_dir}")

def process_image(sample_id, input_dir, output_dir, target_size):
    """Process a single image: load, resize, save as PNG"""
    input_path = os.path.join(input_dir, 'images', f'{sample_id}.jpg')
    output_path = os.path.join(output_dir, 'images', f'{sample_id}.png')
    
    try:
        with Image.open(input_path) as img:
            original_size = img.size
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Resize and save
            img_resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            img_resized.save(output_path, 'PNG')
            return original_size
    except Exception as e:
        print(f"Error processing image {sample_id}: {e}")
        return None

def process_text(sample_id, input_dir, output_dir):
    """Process a single text file: read and compute statistics"""
    input_path = os.path.join(input_dir, 'texts', f'{sample_id}.txt')
    output_path = os.path.join(output_dir, 'texts', f'{sample_id}.txt')
    
    try:
        # Read with UTF-8, fallback to latin-1
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='latin-1') as f:
                text = f.read()
        
        # Copy to output directory
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Compute statistics
        word_count = len(text.split())
        char_count = len(text)
        
        return word_count, char_count
    except Exception as e:
        print(f"Error processing text {sample_id}: {e}")
        return None, None

def process_dataset(input_dir, output_dir, target_size, valid_samples, labels_dict):
    """Process all valid samples and generate manifest"""
    manifest = []
    failed_samples = []
    
    print(f"Processing {len(valid_samples)} samples...")
    
    for i, sample_id in enumerate(sorted(valid_samples), 1):
        if i % 100 == 0:
            print(f"Processed {i}/{len(valid_samples)} samples")
        
        # Process image
        original_size = process_image(sample_id, input_dir, output_dir, target_size)
        if original_size is None:
            failed_samples.append(sample_id)
            continue
        
        # Process text
        word_count, char_count = process_text(sample_id, input_dir, output_dir)
        if word_count is None:
            failed_samples.append(sample_id)
            continue
        
        # Add to manifest
        manifest.append({
            'sample_id': sample_id,
            'image_path': f'images/{sample_id}.png',
            'text_path': f'texts/{sample_id}.txt',
            'label': labels_dict[sample_id],
            'word_count': word_count,
            'char_count': char_count,
            'original_image_size': original_size
        })
    
    if failed_samples:
        print(f"Failed to process {len(failed_samples)} samples: {failed_samples[:5]}{'...' if len(failed_samples) > 5 else ''}")
    
    return manifest

def save_manifest(manifest, output_dir):
    """Save manifest.json to output directory"""
    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Manifest saved: {manifest_path}")

def print_summary(manifest):
    """Print dataset summary statistics"""
    if not manifest:
        print("No samples processed successfully")
        return
    
    total_samples = len(manifest)
    labels = [item['label'] for item in manifest]
    word_counts = [item['word_count'] for item in manifest]
    
    label_dist = Counter(labels)
    avg_word_count = np.mean(word_counts)
    
    print("\n" + "="*50)
    print("DATASET SUMMARY")
    print("="*50)
    print(f"Total samples: {total_samples}")
    print(f"Average word count: {avg_word_count:.1f}")
    print("\nLabel distribution:")
    for label, count in sorted(label_dist.items()):
        percentage = (count / total_samples) * 100
        print(f"  {label}: {count} ({percentage:.1f}%)")
    print("="*50)

def main():
    args = parse_arguments()
    
    try:
        # Validate input
        validate_input_structure(args.input_dir)
        labels_dict = load_labels(args.input_dir)
        valid_samples = get_valid_samples(args.input_dir, labels_dict)
        
        # Setup output
        setup_output_directory(args.output_dir)
        
        # Process dataset
        manifest = process_dataset(args.input_dir, args.output_dir, args.image_size, valid_samples, labels_dict)
        
        # Save results
        save_manifest(manifest, args.output_dir)
        print_summary(manifest)
        
        print(f"\n✓ Dataset preprocessing completed successfully!")
        print(f"Output directory: {args.output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
