#!/usr/bin/env python3
"""
详细检查控制台错误
"""
import asyncio
from playwright.async_api import async_playwright

async def check_console():
    """检查控制台错误详情"""
    print("=" * 60)
    print("🔍 检查控制台错误详情")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))
        
        # 访问 Dashboard
        print("\n📋 访问 Dashboard...")
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        
        # 输出所有控制台消息
        print(f"\n控制台消息 ({len(console_messages)} 条):")
        for msg in console_messages:
            if msg["type"] in ["error", "warning"]:
                print(f"  [{msg['type']}] {msg['text'][:150]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_console())
