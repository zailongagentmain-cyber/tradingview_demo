#!/usr/bin/env python3
"""
TradingView Demo - 详细错误分析 v2
"""
import asyncio
from playwright.async_api import async_playwright

async def check_404_resources():
    """检查 404 资源"""
    print("=" * 60)
    print("🔍 404 资源检查")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 记录所有网络请求
        failed_requests = []
        
        async def handle_request(request):
            if request.url.startswith("http") and request.url != "http://localhost:8501/":
                pass
        
        async def handle_response(response):
            if response.status == 404:
                failed_requests.append({
                    "url": response.url,
                    "status": response.status
                })
        
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on("response", handle_response)
        
        # 访问主页
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        print("\n404 资源:")
        for req in failed_requests:
            print(f"  - {req['url']}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_404_resources())
