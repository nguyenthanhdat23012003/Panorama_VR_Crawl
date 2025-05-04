import asyncio
from playwright.async_api import async_playwright
import re
import os

ERROR_FILE = "error_fetch_image_key.txt"
OUTPUT_FILE = "product-mapping-image-key.txt"
TEMP_FILE = "temp_error.txt"
MAX_CONCURRENT = 20
MAX_RETRY = 5
CDN_PATTERN = re.compile(r"https?://imgscdn\.ajun720\.cn/(\d+/works/[a-zA-Z0-9]+)")

async def fetch_and_handle(context, key, sema, lock):
    tour_url = f"http://www.ajun720.cn/tour/{key}"
    cdn_path = None

    async with sema:
        for attempt in range(1, MAX_RETRY + 1):
            print(f"🔁 [{key}] Thử lần {attempt}")
            page = await context.new_page()

            def handle_request(request):
                nonlocal cdn_path
                match = CDN_PATTERN.search(request.url)
                if match and not cdn_path:
                    cdn_path = match.group(1)

            page.on("request", handle_request)

            try:
                await page.goto(tour_url, timeout=60000)
                await page.wait_for_timeout(8000)
            except Exception as e:
                print(f"⚠️ Lỗi {key} lần {attempt}: {e}")
                await page.wait_for_timeout(3000)
            finally:
                await page.close()

            if cdn_path:
                print(f"✅ {key} → {cdn_path}")
                async with lock:
                    with open(OUTPUT_FILE, "a") as out:
                        out.write(f"{key},{cdn_path}\n")
                return True

        print(f"❌ Không tìm thấy CDN cho {key}")
        return False

async def retry_errors():
    lock = asyncio.Lock()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        sema = asyncio.Semaphore(MAX_CONCURRENT)

        while True:
            if not os.path.exists(ERROR_FILE):
                print("🎉 Không còn lỗi để retry.")
                break

            with open(ERROR_FILE, "r") as f:
                keys = [line.strip() for line in f if line.strip()]

            if not keys:
                print("🎉 Retry hoàn tất, không còn key.")
                break

            print(f"🚀 Đang retry {len(keys)} key lỗi...")

            remaining = []

            async def handle_key(key):
                success = await fetch_and_handle(context, key, sema, lock)
                if not success:
                    remaining.append(key)

            await asyncio.gather(*(handle_key(key) for key in keys))

            # Ghi lại danh sách còn lỗi
            with open(ERROR_FILE, "w") as f:
                f.write("\n".join(remaining) + ("\n" if remaining else ""))

            if not remaining:
                print("✅ Tất cả key đã retry thành công.")
                break

        await browser.close()

if __name__ == "__main__":
    asyncio.run(retry_errors())
