import os
import aiohttp
import asyncio

FACES = ["f", "b", "l", "r", "u", "d"]
BASE_URL = "https://imgscdn.ajun720.cn"
OUTPUT_DIR = "image_crawled"
INPUT_FOLDER = "output_structure"
MAX_CONCURRENT = 40
MAX_RETRY = 3
TIMEOUT = 10

sem = asyncio.Semaphore(MAX_CONCURRENT)
lock = asyncio.Lock()

def parse_structure_from_filename(filename):
    parts = filename.replace(".txt", "").split("_")
    levels = []
    i = 0
    while i < len(parts):
        if parts[i].startswith("l") and i + 2 < len(parts):
            try:
                lv = int(parts[i][1:])
                row = int(parts[i + 1])
                col = int(parts[i + 2])
                levels.append((lv, row, col))
                i += 3
            except ValueError:
                i += 1
        else:
            i += 1
    return levels

async def fetch(session, url, log_id):
    for attempt in range(1, MAX_RETRY + 1):
        try:
            async with session.get(url, timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    print(f"[\u2705] ({log_id}) Success: {url}")
                    return await resp.read()
                else:
                    print(f"[\u26a0\ufe0f] ({log_id}) Attempt {attempt}: Status {resp.status}")
        except Exception as e:
            print(f"[\u274c] ({log_id}) Attempt {attempt}: {e}")
        await asyncio.sleep(1)
    return None

async def download_images_for_product(session, key, image_path, levels, subfolder_name):
    folder_path = os.path.join(OUTPUT_DIR, subfolder_name, key)
    os.makedirs(folder_path, exist_ok=True)

    print(f"\n📦 Crawling product: {key} in file {subfolder_name}")
    preview_url = f"{BASE_URL}/{image_path}/preview.jpg"
    preview_content = await fetch(session, preview_url, f"{key} - preview")
    if not preview_content:
        return False

    with open(os.path.join(folder_path, "preview.jpg"), "wb") as f:
        f.write(preview_content)

    tasks = []

    async def download_tile(face, lv, r, c):
        img_name = f"l{lv}_{face}_{r}_{c}.jpg"
        url = f"{BASE_URL}/{image_path}/{face}/l{lv}/{r}/{img_name}"
        content = await fetch(session, url, f"{key} - {img_name}")
        if not content:
            return False
        save_dir = os.path.join(folder_path, face, f"l{lv}", str(r))
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, img_name), "wb") as f:
            f.write(content)
        return True

    for face in FACES:
        for lv, rows, cols in levels:
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    tasks.append(download_tile(face, lv, r, c))

    results = await asyncio.gather(*tasks)
    return all(results)

async def process_file(filepath):
    filename = os.path.basename(filepath)
    levels = parse_structure_from_filename(filename)
    subfolder_name = filename.replace(".txt", "")
    print(f"\n📂 Processing file: {filename} with structure {levels}")

    while True:
        # Đọc lại file mỗi vòng
        if not os.path.exists(filepath):
            break

        with open(filepath, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            print(f"\u2705 Hoàn tất file {filename}")
            break

        current_line = lines[0]
        try:
            key, path = current_line.split(",", 1)
        except ValueError:
            print(f"\u274c Bỏ qua dòng lỗi: {current_line}")
            lines = lines[1:]
            with open(filepath, "w") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
            continue

        async with aiohttp.ClientSession() as session:
            success = await download_images_for_product(session, key, path, levels, subfolder_name)

        if success:
            lines = lines[1:]
            with open(filepath, "w") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        else:
            print(f"⚠️ Product {key} failed. Sẽ được thử lại sau.")
            await asyncio.sleep(2)

async def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ Không tìm thấy thư mục {INPUT_FOLDER}")
        return

    for fname in sorted(os.listdir(INPUT_FOLDER)):
        if fname.endswith(".txt"):
            await process_file(os.path.join(INPUT_FOLDER, fname))

if __name__ == "__main__":
    asyncio.run(main())
