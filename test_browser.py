#!/usr/bin/env python3
"""
TradingView Demo - Playwright 自动化测试
"""
import asyncio
from playwright.async_api import async_playwright

async def test_streamlit_app():
    """测试 Streamlit 应用"""
    print("=" * 60)
    print("🚀 启动浏览器测试")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动 Chromium
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 测试 1: 访问主页
        print("\n📋 测试 1: 访问 Dashboard")
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        title = await page.title()
        print(f"   页面标题: {title}")
        
        # 检查主要元素
        h1 = await page.locator("h1").first.text_content()
        print(f"   主标题: {h1}")
        
        # 测试 2: 检查页面导航
        print("\n📋 测试 2: 检查页面元素")
        
        # 检查侧边栏
        sidebar = await page.locator("[data-testid='stSidebar']").count()
        print(f"   侧边栏存在: {sidebar > 0}")
        
        # 检查按钮/链接
        buttons = await page.locator("button").count()
        print(f"   按钮数量: {buttons}")
        
        # 测试 3: 检查 Streamlit 特定元素
        print("\n📋 测试 3: Streamlit 组件检查")
        
        # 检查版本信息
        version_text = await page.content()
        if "v2.4.0" in version_text:
            print("   ✅ 版本号显示正确 (v2.4.0)")
        
        # 检查页面链接
        links = await page.locator("a").count()
        print(f"   链接数量: {links}")
        
        # 测试 4: 导航到 K线图表页
        print("\n📋 测试 4: 导航到 K线图表页")
        
        # 点击页面导航 - Streamlit 多页面通常在侧边栏
        try:
            # 尝试点击包含"K线"或"图表"的链接
            kline_link = page.locator("a:has-text('K线'), a:has-text('图表'), a:has-text('K')").first
            if await kline_link.count() > 0:
                await kline_link.click()
                await page.wait_for_load_state("networkidle")
                print("   ✅ 成功导航到 K线图表页")
            else:
                print("   ⚠️ 未找到 K线图表 导航链接")
        except Exception as e:
            print(f"   ❌ 导航失败: {e}")
        
        # 检查控制台错误
        print("\n📋 测试 5: 检查控制台错误")
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        await page.reload()
        await page.wait_for_load_state("networkidle")
        
        if console_errors:
            print(f"   ⚠️ 发现 {len(console_errors)} 个控制台错误:")
            for err in console_errors[:3]:
                print(f"      - {err[:100]}")
        else:
            print("   ✅ 无控制台错误")
        
        await browser.close()
        
        print("\n" + "=" * 60)
        print("✅ 浏览器测试完成!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_streamlit_app())
