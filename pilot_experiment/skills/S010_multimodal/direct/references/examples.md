# Example 1: Basic usage
python main.py --input-dir /data/biology_dataset --output-dir /data/processed --image-size 256

# Example 2: Minimal dataset structure
biology_dataset/
├── images/
│   ├── sample001.jpg
│   ├── sample002.jpg
│   └── sample003.jpg
├── texts/
│   ├── sample001.txt
│   ├── sample002.txt
│   └── sample003.txt
└── labels.csv

# labels.csv content:
sample_id,label
sample001,positive
sample002,negative
sample003,positive

# Example manifest.json output:
[
  {
    "sample_id": "sample001",
    "image_path": "images/sample001.png",
    "text_path": "texts/sample001.txt",
    "label": "positive",
    "word_count": 45,
    "char_count": 312,
    "original_image_size": [1024, 768]
  }
]
