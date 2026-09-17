import cv2
import os

assets_dir = "app_assets"
target_sizes = {
    "mimtens.jpg": (592, 592),      # e.g. exactly at your LSB capacity boundary
    # "ronaldo.jpg": (1200, 1200),  # oversized cover test
}

for filename, (w, h) in target_sizes.items():
    path = os.path.join(assets_dir, filename)
    img = cv2.imread(path)
    resized = cv2.resize(img, (w, h))
    out_path = os.path.join(assets_dir, f"resized_{filename}")
    cv2.imwrite(out_path, resized)
    print(f"{filename}: {img.shape[:2]} -> {resized.shape[:2]}")