#!/usr/bin/env python3
"""
TradingView Demo - 完整自动化测试
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def test_all_pages():
    """测试所有页面"""
    print("=" * 60)
    print("🚀 TradingView 完整测试")
    print("=" * 60)
    
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 收集控制台错误
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        pages_to_test = [
            ("/", "Dashboard"),
            ("/1_K线图表", "K线图表"),
            ("/2_股票筛选器", "股票筛选器"),
            ("/3_策略回测", "策略回测"),
            ("/4_财经新闻", "财经新闻"),
            ("/5_实盘模拟交易", "实盘模拟交易"),
            ("/6_绩效分析", "绩效分析"),
            ("/7_组合分析", "组合分析"),
            ("/8_风险监控", "风险监控"),
            ("/9_因子看板", "因子看板"),
        ]
        
        for path, name in pages_to_test:
            print(f"\n📋 测试: {name}")
            console_errors.clear()
            
            try:
                url = f"http://localhost:8501{path}"
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                # 检查页面标题
                title = await page.title()
                
                # 检查是否有主要元素
                h1_count = await page.locator("h1, h2, h3").count()
                
                # 检查是否有 Streamlit 错误
                error_elements = await page.locator(".stError, .streamlit-error").count()
                
                # 检查控制台错误数量
                error_count = len(console_errors)
                
                results[name] = {
                    "status": "✅" if h1_count > 0 else "❌",
                    "title": title,
                    "elements": h1_count,
                    "errors": error_count,
                    "streamlit_errors": error_elements
                }
                
                print(f"   状态: {results[name]['status']}")
                print(f"   标题: {title}")
                print(f"   元素数: {h1_count}")
                if error_count > 0:
                    print(f"   ⚠️ 控制台错误: {error_count}")
                if error_elements > 0:
                    print(f"   ⚠️ Streamlit 错误: {error_elements}")
                    
            except Exception as e:
                results[name] = {"status": "❌", "error": str(e)[:100]}
                print(f"   ❌ 加载失败: {e}")
        
        await browser.close()
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results.items():
        status = result.get("status", "❌")
        if status == "✅":
            passed += 1
        else:
            failed += 1
        print(f"{status} {name}")
    
    print(f"\n通过: {passed}/{len(pages_to_test)}")
    print(f"失败: {failed}/{len(pages_to_test)}")
    
    # 详细错误报告
    print("\n" + "=" * 60)
    print("❌ 失败项详情")
    print("=" * 60)
    
    for name, result in results.items():
        if result.get("status") != "✅":
            print(f"\n{name}:")
            if "error" in result:
                print(f"  错误: {result['error']}")
            if result.get("streamlit_errors", 0) > 0:
                print(f"  Streamlit 错误元素: {result['streamlit_errors']}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_all_pages())
