import sys, os, subprocess, tempfile, json
import numpy as np

def create_data(root, n=10):
    os.makedirs(f"{root}/images", exist_ok=True)
    os.makedirs(f"{root}/texts", exist_ok=True)
    # 创建简单的 JPEG-like 文件（实际用 numpy 保存为可读图片）
    try:
        from PIL import Image
        has_pil = True
    except ImportError:
        has_pil = False

    labels = []
    for i in range(n):
        name = f"sample_{i:03d}"
        if has_pil:
            img = Image.fromarray(np.random.randint(0, 255, (100+i*10, 80+i*5, 3), dtype=np.uint8))
            img.save(f"{root}/images/{name}.jpg")
        else:
            # 没有 PIL 就写个假图
            np.save(f"{root}/images/{name}.npy", np.random.randint(0, 255, (100+i*10, 80+i*5, 3), dtype=np.uint8))
        with open(f"{root}/texts/{name}.txt", "w") as f:
            words = " ".join([f"word{j}" for j in range(10 + i * 2)])
            f.write(words)
        labels.append({"sample_id": name, "label": ["cell", "tissue", "organ"][i % 3]})

    import pandas as pd
    pd.DataFrame(labels).to_csv(f"{root}/labels.csv", index=False)
    return n

with tempfile.TemporaryDirectory() as tmpdir:
    data_root = f"{tmpdir}/data"
    out_dir = f"{tmpdir}/output"
    n = create_data(data_root)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input-dir", data_root, "--output-dir", out_dir, "--image-size", "64"],
        [sys.executable, "generated.py", data_root, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找 manifest
    manifest_path = None
    for root_d, dirs, files in os.walk(tmpdir):
        for f in files:
            if "manifest" in f.lower() and f.endswith(".json"):
                manifest_path = os.path.join(root_d, f)

    if manifest_path or os.path.exists(out_dir):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L2_manifest","L2_has_samples","L2_has_word_count","L2_images_processed"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    if manifest_path:
        manifest = json.load(open(manifest_path))
        print("PASS:L2_manifest")
        if isinstance(manifest, list) and len(manifest) == n:
            print(f"PASS:L2_has_samples - {n} entries")
        elif isinstance(manifest, dict) and len(manifest.get("samples", manifest.get("data", []))) == n:
            print(f"PASS:L2_has_samples")
        else:
            print(f"FAIL:L2_has_samples - unexpected structure")

        m_str = json.dumps(manifest).lower()
        if "word" in m_str and "count" in m_str:
            print("PASS:L2_has_word_count")
        else:
            print("FAIL:L2_has_word_count")
    else:
        print("FAIL:L2_manifest - no manifest.json found")
        print("FAIL:L2_has_samples")
        print("FAIL:L2_has_word_count")

    # 检查图片是否被处理
    processed_imgs = []
    processed_img_paths = []
    if os.path.exists(out_dir):
        for root_d, dirs, files in os.walk(out_dir):
            for f in files:
                if f.endswith((".png", ".jpg", ".npy")):
                    processed_imgs.append(f)
                    processed_img_paths.append(os.path.join(root_d, f))
    if len(processed_imgs) >= n // 2:
        print(f"PASS:L2_images_processed - {len(processed_imgs)} images")
    else:
        print(f"FAIL:L2_images_processed - only {len(processed_imgs)}")

    # --- 新增测试 ---
    # L2: 图片是否被 resize
    resized_ok = False
    if processed_img_paths:
        try:
            from PIL import Image
            for p in processed_img_paths:
                if p.endswith((".png", ".jpg")):
                    img = Image.open(p)
                    if img.size == (64, 64):
                        resized_ok = True
                    break
        except:
            resized_ok = len(processed_imgs) >= n // 2
    print(f"{'PASS' if resized_ok else 'FAIL'}:L2_resized")

    # L2: labels 信息被整合到 manifest
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "label" in m_str and ("cell" in m_str or "tissue" in m_str or "organ" in m_str):
            print("PASS:L2_labels")
        else:
            print("FAIL:L2_labels - no label information in manifest")
    else:
        print("FAIL:L2_labels - no manifest")

    # L2: 保留了原始图片尺寸信息
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "original" in m_str or "size" in m_str or "width" in m_str or "height" in m_str:
            print("PASS:L2_original_size")
        else:
            print("FAIL:L2_original_size - no original size info")
    else:
        print("FAIL:L2_original_size")

    # L2: 输出格式为 PNG
    png_count = sum(1 for p in processed_imgs if p.endswith(".png"))
    if png_count >= n // 2:
        print(f"PASS:L2_format - {png_count} PNG files")
    else:
        print(f"FAIL:L2_format - only {png_count} PNG files")

    # L2: 处理了所有样本
    if len(processed_imgs) >= n:
        print(f"PASS:L2_all_samples - {len(processed_imgs)}/{n}")
    else:
        print(f"FAIL:L2_all_samples - {len(processed_imgs)}/{n}")

    # L2: 文本字符数正确
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "char" in m_str:
            print("PASS:L2_chars")
        else:
            print("FAIL:L2_chars - no character count in manifest")
    else:
        print("FAIL:L2_chars")

    # SCORE: manifest 完整性
    if manifest_path and os.path.exists(manifest_path):
        manifest_data = json.load(open(manifest_path))
        if isinstance(manifest_data, list):
            items = manifest_data
        elif isinstance(manifest_data, dict):
            items = manifest_data.get("samples", manifest_data.get("data", []))
        else:
            items = []
        if items:
            expected_keys = ["sample_id", "image", "text", "label", "word_count", "char_count"]
            items_str = json.dumps(items[0]).lower() if items else ""
            found_keys = sum(1 for k in expected_keys if k in items_str or k.replace("_", "") in items_str)
            manifest_completeness = round(found_keys / len(expected_keys), 4)
        else:
            manifest_completeness = 0.0
    else:
        manifest_completeness = 0.0
    print(f"SCORE:manifest_completeness={manifest_completeness}")

    # SCORE: 图片质量（处理的图片数 / 总样本数）
    image_quality = round(min(len(processed_imgs) / max(n, 1), 1.0), 4)
    print(f"SCORE:image_quality={image_quality}")
