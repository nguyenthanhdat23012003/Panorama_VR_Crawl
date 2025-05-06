import aiohttp
import asyncio
import os

BASE_URL = "https://imgscdn.ajun720.cn"
OUTPUT_DIR = "output_structure"
MAX_LEVEL = 6
MAX_ROW = 10
MAX_COL = 20
FACE = "b"
TIMEOUT = aiohttp.ClientTimeout(total=10)
CONCURRENT_PRODUCTS = 20  # chỉ xử lý 20 product một lúc
RETRY = 3

os.makedirs(OUTPUT_DIR, exist_ok=True)
sema = asyncio.Semaphore(CONCURRENT_PRODUCTS)

async def check_url(session, url, retries=RETRY):
    for attempt in range(retries):
        try:
            async with session.head(url) as resp:
                return resp.status == 200
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(0.5)
            else:
                return False

async def get_structure(session, cdn_path):
    cdn_id = cdn_path.split("/")[-1]
    full_cdn_url = f"{BASE_URL}/{cdn_path}/{FACE}"
    structure = []

    for level_num in range(1, MAX_LEVEL + 1):
        level = f"l{level_num}"
        first_image_url = f"{full_cdn_url}/{level}/1/{level}_{FACE}_1_1.jpg"
        if not await check_url(session, first_image_url):
            break

        max_row, max_col = 0, 0
        for row in range(1, MAX_ROW + 1):
            col_count = 0
            for col in range(1, MAX_COL + 1):
                image_url = f"{full_cdn_url}/{level}/{row}/{level}_{FACE}_{row}_{col}.jpg"
                if await check_url(session, image_url):
                    col_count += 1
                else:
                    break
            if col_count == 0:
                break
            max_row += 1
            max_col = max(max_col, col_count)

        structure.append((level, max_row, max_col))
    return structure

def format_filename(structure):
    parts = [f"l{len(structure)}"]
    for level, row, col in structure:
        parts.append(f"{level}_{row}_{col}")
    return "_".join(parts) + ".txt"

async def process_key(session, product_key, cdn_key_full):
    async with sema:
        print(f"📦 Bắt đầu: {product_key}")
        structure = await get_structure(session, cdn_key_full)
        if not structure:
            print(f"❌ Không tìm thấy: {product_key}")
            return
        filename = format_filename(structure)
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "a") as f:
            f.write(f"{product_key},{cdn_key_full}\n")
        print(f"✅ Ghi vào: {filename}")

async def main():
    with open("has_image.txt") as f:
        lines = [line.strip() for line in f if line.strip()]
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        tasks = []
        for line in lines:
            try:
                product_key, cdn_key = line.split(",", 1)
                tasks.append(process_key(session, product_key, cdn_key))
            except:
                continue
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
