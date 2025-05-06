import aiohttp
import asyncio
import os

ERROR_FILE = "error_fetch_image_key.txt"
OUTPUT_FILE = "hacking_attempt_keys.txt"
CHECK_STRING = "hacking attempt"
BASE_URL = "http://www.ajun720.cn"
MAX_CONCURRENT = 10
MAX_RETRY = 3

sem = asyncio.Semaphore(MAX_CONCURRENT)

async def check_key(session, key):
    url = f"{BASE_URL}/{key}"

    for attempt in range(1, MAX_RETRY + 1):
        async with sem:
            try:
                async with session.get(url, timeout=10) as resp:
                    text = await resp.text()
                    if CHECK_STRING in text.lower():
                        print(f"❌ [HACK BLOCKED] {key}")
                        return key
                    else:
                        print(f"✅ [OK] {key}")
                        return None
            except Exception as e:
                print(f"⚠️ [ERROR] {key} lần {attempt}: {e}")
                await asyncio.sleep(1)  # nhỏ delay trước khi thử lại
    return None

async def main():
    if not os.path.exists(ERROR_FILE):
        print("❗ File lỗi không tồn tại.")
        return

    with open(ERROR_FILE, "r") as f:
        keys = [line.strip() for line in f if line.strip()]

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(check_key(session, key) for key in keys))

    blocked_keys = list(filter(None, results))

    if blocked_keys:
        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(blocked_keys))
        print(f"\n🔒 Đã ghi {len(blocked_keys)} key bị chặn vào {OUTPUT_FILE}")
    else:
        print("\n✅ Không có key nào bị chặn.")

if __name__ == "__main__":
    asyncio.run(main())
