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

async def process_line(session, line):
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
                with open(OUTPUT_FILE, "a") as f:
                    f.write(line + "\n")
                if os.path.exists(MAPPING_FILE):
                    with open(MAPPING_FILE, "r") as f:
                        lines = f.readlines()
                    with open(MAPPING_FILE, "w") as f:
                        for l in lines:
                            if l.strip() != line:
                                f.write(l)
        else:
            print(f"❌ {product_key} - Thiếu: ", end="")
            if not preview_ok:
                print("preview.jpg", end=" ")
            if not img_ok:
                print("l1_b_1_1.jpg", end="")
            print()

async def main():
    if not os.path.exists(MAPPING_FILE):
        print("❌ File mapping không tồn tại.")
        return

    with open(MAPPING_FILE, "r") as f:
        lines = f.readlines()

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(process_line(session, line) for line in lines))

    print("\n🎯 Hoàn tất xử lý.")

if __name__ == "__main__":
    asyncio.run(main())
