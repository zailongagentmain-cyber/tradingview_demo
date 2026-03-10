#!/usr/bin/env python3
"""
TradingView Demo - 详细错误分析
"""
import asyncio
from playwright.async_api import async_playwright

async def check_console_errors():
    """检查控制台错误详情"""
    print("=" * 60)
    print("🔍 控制台错误分析")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))
        
        # 访问 K线图表页
        await page.goto("http://localhost:8501/1_K线图表")
        await page.wait_for_load_state("networkidle")
        
        # 等待一下让资源加载
        await asyncio.sleep(2)
        
        # 打印错误
        errors = [m for m in console_messages if m["type"] == "error"]
        print(f"\n发现 {len(errors)} 个错误:")
        
        for i, err in enumerate(errors, 1):
            print(f"\n{i}. {err['text']}")
        
        # 检查 404 资源
        warnings = [m for m in console_messages if m["type"] == "warning"]
        if warnings:
            print(f"\n发现 {len(warnings)} 个警告:")
            for w in warnings[:3]:
                print(f"  - {w['text'][:100]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_console_errors())
