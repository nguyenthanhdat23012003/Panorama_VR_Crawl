import asyncio
from playwright.async_api import async_playwright
import re
import os

KEY_FILE = "product-key.txt"
OUTPUT_FILE = "product-mapping-image-key.txt"
ERROR_FILE = "error_fetch_image_key.txt"
MAX_CONCURRENT = 20
MAX_RETRY = 3
CDN_PATTERN = re.compile(r"https?://imgscdn\.ajun720\.cn/(\d+/works/[a-zA-Z0-9]+)")

# Đọc danh sách product keys
with open(KEY_FILE, "r") as f:
    keys = [line.strip() for line in f if line.strip()]

# Xóa file output cũ nếu có
for path in [OUTPUT_FILE, ERROR_FILE]:
    if os.path.exists(path):
        os.remove(path)

async def fetch_cdn_from_tour(context, key, sema):
    tour_url = f"http://www.ajun720.cn/tour/{key}"
    cdn_path = None

    async with sema:
        for attempt in range(1, MAX_RETRY + 1):
            print(f"🔍 [{key}] Thử lần {attempt}...")
            page = await context.new_page()

            def handle_request(request):
                nonlocal cdn_path
                match = CDN_PATTERN.search(request.url)
                if match and not cdn_path:
                    cdn_path = match.group(1)

            page.on("request", handle_request)

            try:
                await page.goto(tour_url, timeout=60000)
                await page.wait_for_timeout(10000)
            except Exception as e:
                print(f"⚠️ Lỗi {key} lần {attempt}: {e}")
                await page.wait_for_timeout(5000)
            finally:
                await page.close()

            if cdn_path:
                print(f"✅ {key} → {cdn_path}")
                async with asyncio.Lock():
                    with open(OUTPUT_FILE, "a") as out:
                        out.write(f"{key},{cdn_path}\n")
                return

        print(f"❌ Không tìm thấy CDN cho {key} sau {MAX_RETRY} lần")
        async with asyncio.Lock():
            with open(ERROR_FILE, "a") as err:
                err.write(f"{key}\n")

async def check_connection():
    print("🌐 Kiểm tra kết nối đến http://www.ajun720.cn ...")
    try:
        import aiohttp
    except ImportError:
        print("⚠️ Thiếu aiohttp — bỏ qua kiểm tra kết nối.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://www.ajun720.cn", timeout=10) as resp:
                if resp.status == 200:
                    print("✅ Kết nối thành công!")
                else:
                    print(f"⚠️ Trang trả về mã {resp.status}")
    except Exception as e:
        print(f"❌ Không kết nối được: {e}")

async def main():
    await check_connection()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0")
        sema = asyncio.Semaphore(MAX_CONCURRENT)

        tasks = [fetch_cdn_from_tour(context, key, sema) for key in keys]
        await asyncio.gather(*tasks)

        await browser.close()

asyncio.run(main())
