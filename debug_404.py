#!/usr/bin/env python3
"""
详细排查 404 错误
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_404():
    """详细检查 404 错误"""
    print("=" * 60)
    print("🔍 排查 404 错误")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 收集所有网络请求
        failed_requests = []
        
        def log_request(request):
            if request.response and request.response.status in [404, 400, 500]:
                failed_requests.append({
                    "url": request.url,
                    "status": request.response.status,
                    "method": request.method
                })
        
        page.on("requestfailed", lambda req: failed_requests.append({
            "url": req.url,
            "status": "failed",
            "method": req.method
        }))
        
        # 测试 K线图表页
        print("\n📋 测试 K线图表页...")
        await page.goto("http://localhost:8501/1_K线图表")
        await page.wait_for_load_state("networkidle")
        
        # 等待一下确保所有请求完成
        await page.wait_for_timeout(2000)
        
        print(f"\n发现 {len(failed_requests)} 个失败请求:")
        for req in failed_requests[:10]:
            print(f"  [{req['status']}] {req['url'][:80]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_404())
