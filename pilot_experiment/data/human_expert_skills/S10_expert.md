# Multimodal Biology Dataset Preprocessing — Expert Notes

## What You're Building
Preprocess a multimodal dataset: resize images, compute text stats, merge with labels, and generate a manifest JSON.

## Key Steps
1. Read labels.csv for sample_id → label mapping
2. For each sample: load image → resize → save as PNG; read text → count words/chars
3. Generate manifest.json listing all samples with metadata

## Things That Trip People Up
1. **PIL import**: Use `from PIL import Image`. The package is `Pillow` but import is `PIL`. Make sure to use `Image.open()` not `cv2.imread()`
2. **Resize preserving aspect ratio**: For this task, just resize to (size, size) directly — `img.resize((size, size), Image.LANCZOS)`. Don't overthink aspect ratio
3. **Matching images to texts**: Use filename stem: `Path(img).stem` should match `Path(txt).stem`. Handle the case where some samples might be missing one modality
4. **manifest.json structure**: A list of dicts, each with sample_id, image_path, text_path, label, word_count, char_count, original_image_size. Keep paths relative to output dir
5. **Memory**: Don't load all images at once. Process one at a time

## Reference
```python
manifest = []
for _, row in labels.iterrows():
    sid = row["sample_id"]
    img = Image.open(img_dir / f"{sid}.jpg")
    original_size = img.size
    img_resized = img.resize((image_size, image_size), Image.LANCZOS)
    img_resized.save(out_img_dir / f"{sid}.png")

    text = (txt_dir / f"{sid}.txt").read_text()
    manifest.append({
        "sample_id": sid,
        "image_path": f"images/{sid}.png",
        "text_path": f"texts/{sid}.txt",
        "label": row["label"],
        "word_count": len(text.split()),
        "char_count": len(text),
        "original_image_size": list(original_size),
    })
json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=2)
```
