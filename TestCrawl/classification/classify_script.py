import asyncio
from playwright.async_api import async_playwright

URL = "http://www.ajun720.cn/tour/6406b321b405ea96"

async def open_page(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    print("🧭 Đang mở trang...")
    await page.goto(URL, wait_until="domcontentloaded", timeout=0)

    # Đợi để bạn có thể xem trang bằng mắt, có thể thay đổi hoặc bỏ dòng này
    await page.wait_for_timeout(10000)

    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await open_page(playwright)

if __name__ == "__main__":
    asyncio.run(main())
