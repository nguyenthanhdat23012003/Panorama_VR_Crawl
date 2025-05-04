import requests
import os
from tqdm import tqdm

FACES = ["f", "b", "l", "r", "u", "d"]
LEVEL_RANGE = range(1, 6)
MAX_ROW = 20
MAX_COL = 20
TIMEOUT = 2
MAX_RETRY = 2

BASE_URL = "https://imgscdn.ajun720.cn"
input_file = "product-mapping-image-key.txt"
output_dir = "image_crawl"
error_file = "error_fetch_image.txt"
success_file = "success_fetch_image.txt"

# Tạo file nếu chưa có
for fpath in [error_file, success_file]:
    if not os.path.exists(fpath):
        open(fpath, "w").close()

def download_with_retry(url):
    for _ in range(MAX_RETRY):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.content
        except:
            pass
    return None

# Đọc toàn bộ mapping ban đầu
with open(input_file, "r") as f:
    mappings = [line.strip() for line in f if "," in line]

remaining_mappings = []

for line in mappings:
    product_key, cdn_path = line.split(",", 1)
    print(f"\n📦 Đang xử lý: {product_key} → {cdn_path}")
    product_path = os.path.join(output_dir, product_key)
    os.makedirs(product_path, exist_ok=True)

    # Tải preview
    preview_url = f"{BASE_URL}/{cdn_path}/preview.jpg"
    preview_path = os.path.join(product_path, "preview.jpg")
    content = download_with_retry(preview_url)

    if not content:
        print(f"❌ Không tải được preview → skip {product_key}")
        with open(error_file, "a") as f:
            f.write(f"{product_key} → {cdn_path}\n")
        continue

    with open(preview_path, "wb") as f:
        f.write(content)
    print("✔️ preview.jpg")

    # Tải tile
    for face in FACES:
        for level_num in LEVEL_RANGE:
            level = f"l{level_num}"
            test_url = f"{BASE_URL}/{cdn_path}/{face}/{level}/1/{level}_{face}_1_1.jpg"
            if not download_with_retry(test_url):
                continue

            print(f"🔎 Bắt đầu tải {face}/{level}")
            for row in range(1, MAX_ROW + 1):
                found_in_row = False
                for col in range(1, MAX_COL + 1):
                    filename = f"{level}_{face}_{row}_{col}.jpg"
                    url = f"{BASE_URL}/{cdn_path}/{face}/{level}/{row}/{filename}"
                    content = download_with_retry(url)

                    if content:
                        local_dir = os.path.join(product_path, face, level, str(row))
                        os.makedirs(local_dir, exist_ok=True)
                        local_path = os.path.join(local_dir, filename)

                        with open(local_path, "wb") as f:
                            f.write(content)
                        tqdm.write(f"✔️ {filename}")
                        found_in_row = True
                    else:
                        break
                if not found_in_row:
                    break

    # Đánh dấu thành công
    with open(success_file, "a") as f:
        f.write(f"{product_key} → {cdn_path}\n")

    # Gỡ dòng đã xử lý khỏi mapping file
    with open(input_file, "r") as f:
        remaining = [line for line in f if not line.startswith(f"{product_key},")]

    with open(input_file, "w") as f:
        f.writelines(remaining)


# Cập nhật lại product-mapping-image-key.txt chỉ còn các key chưa xử lý
with open(input_file, "r") as f:
    original_lines = [line.strip() for line in f if "," in line]
with open(success_file, "r") as f:
    done_keys = {line.split(" → ")[0] for line in f}

with open(input_file, "w") as f:
    for line in original_lines:
        key = line.split(",", 1)[0]
        if key not in done_keys:
            f.write(line + "\n")
