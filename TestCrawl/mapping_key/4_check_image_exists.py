import aiohttp
import asyncio
import os

MAPPING_FILE = "product-mapping-image-key.txt"
OUTPUT_FILE = "has_image.txt"
MAX_CONCURRENT = 20
MAX_RETRY = 3
BASE_URL = "https://imgscdn.ajun720.cn"

sem = asyncio.Semaphore(MAX_CONCURRENT)
lock = asyncio.Lock()

async def check_image_exists(session, url):
    for _ in range(MAX_RETRY):
        try:
            async with session.head(url, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except:
            await asyncio.sleep(1)
    return False

async def process_line(session, line, valid_lines):
    line = line.strip()
    if not line:
        return

    product_key, image_path = line.split(",", 1)
    preview_url = f"{BASE_URL}/{image_path}/preview.jpg"
    image_url = f"{BASE_URL}/{image_path}/b/l1/1/l1_b_1_1.jpg"

    async with sem:
        preview_ok = await check_image_exists(session, preview_url)
        img_ok = await check_image_exists(session, image_url)

        if preview_ok and img_ok:
            print(f"✅ {product_key}")
            async with lock:
                valid_lines.append(line)

async def main():
    if not os.path.exists(MAPPING_FILE):
        print("❌ File mapping không tồn tại.")
        return

    with open(MAPPING_FILE, "r") as f:
        lines = f.readlines()

    valid_lines = []

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(process_line(session, line, valid_lines) for line in lines))

    # Ghi dòng hợp lệ vào OUTPUT_FILE
    with open(OUTPUT_FILE, "a") as f:
        for line in valid_lines:
            f.write(line + "\n")

    # Cập nhật lại file mapping gốc, chỉ giữ dòng chưa xử lý hoặc sai
    remaining = [line for line in lines if line.strip() not in valid_lines]
    with open(MAPPING_FILE, "w") as f:
        f.writelines(remaining)

    print(f"\n🧾 Đã ghi {len(valid_lines)} dòng vào {OUTPUT_FILE}")
    print(f"📉 Còn lại {len(remaining)} dòng trong {MAPPING_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
