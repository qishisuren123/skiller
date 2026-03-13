# SKILL: Multimodal Biology Dataset Preprocessor

## Overview
A Python CLI tool that preprocesses multimodal biology datasets by standardizing images, analyzing text files, and generating a unified manifest for machine learning training pipelines.

## Workflow

1. **Parse CLI Arguments**: Set up argparse with input directory, output directory, and image size parameters
2. **Validate Input Structure**: Check for required directories (images/, texts/) and labels.csv file
3. **Load Labels**: Read labels.csv into a dictionary mapping sample_id to label
4. **Process Images**: Resize and convert all .jpg images to standardized PNG format
5. **Analyze Text Files**: Extract word count and character count from corresponding text files
6. **Generate Manifest**: Create manifest.json with all sample metadata and file paths
7. **Output Summary**: Print dataset statistics including sample count, label distribution, and text metrics

## Common Pitfalls & Solutions

1. **Mismatched Image-Text Pairs**
   - *Problem*: Image files without corresponding text files or vice versa
   - *Solution*: Use set intersection to find common sample IDs across all modalities

2. **Memory Issues with Large Images**
   - *Problem*: Loading high-resolution images causes memory overflow
   - *Solution*: Process images one at a time and use PIL's thumbnail method for efficient resizing

3. **Inconsistent File Extensions**
   - *Problem*: Mixed case extensions (.JPG vs .jpg) cause file not found errors
   - *Solution*: Use case-insensitive file matching with `glob.glob('*.jpg') + glob.glob('*.JPG')`

4. **CSV Encoding Issues**
   - *Problem*: Special characters in labels.csv cause UnicodeDecodeError
   - *Solution*: Open CSV with `encoding='utf-8'` and handle encoding errors gracefully

5. **Output Directory Conflicts**
   - *Problem*: Overwriting existing processed data without warning
   - *Solution*: Check if output directory exists and prompt user or use timestamp suffixes

## Error Handling Tips

- Wrap file operations in try-except blocks with specific exception types
- Validate image files can be opened before processing
- Check for empty text files and handle gracefully
- Ensure output directories are created before writing files
- Log skipped samples with reasons for debugging

## Reference Code Snippet

```python
import argparse
import json
import pandas as pd
from PIL import Image
from pathlib import Path

def process_dataset(input_dir, output_dir, image_size):
    # Load labels
    labels_df = pd.read_csv(input_dir / 'labels.csv')
    labels_dict = dict(zip(labels_df['sample_id'], labels_df['label']))
    
    manifest = []
    
    # Find common sample IDs
    image_files = set(f.stem for f in (input_dir / 'images').glob('*.jpg'))
    text_files = set(f.stem for f in (input_dir / 'texts').glob('*.txt'))
    common_samples = image_files & text_files & set(labels_dict.keys())
    
    for sample_id in common_samples:
        try:
            # Process image
            img_path = input_dir / 'images' / f'{sample_id}.jpg'
            img = Image.open(img_path)
            original_size = img.size
            img_resized = img.resize((image_size, image_size))
            
            output_img_path = output_dir / 'images' / f'{sample_id}.png'
            img_resized.save(output_img_path)
            
            # Process text
            text_path = input_dir / 'texts' / f'{sample_id}.txt'
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            manifest.append({
                'sample_id': sample_id,
                'image_path': str(output_img_path),
                'text_path': str(text_path),
                'label': labels_dict[sample_id],
                'word_count': len(text.split()),
                'char_count': len(text),
                'original_image_size': original_size
            })
            
        except Exception as e:
            print(f"Error processing {sample_id}: {e}")
    
    # Save manifest
    with open(output_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest
```