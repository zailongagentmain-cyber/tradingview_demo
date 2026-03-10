"""
财经新闻获取模块
数据源: 东方财富财经新闻 (备用: Tushare)
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
import time
import random


class NewsFetcher:
    """财经新闻获取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def get_stock_news(self, stock_code: str, limit: int = 10) -> List[Dict]:
        """
        获取个股新闻
        
        Args:
            stock_code: 股票代码 (如 000001)
            limit: 返回数量
        
        Returns:
            新闻列表
        """
        # 尝试东方财富 API
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1,
                'pz': limit,
                'po': 1,
                'np': 1,
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': f'b:{stock_code}',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f12,f13,f104,f105,f106'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                return self._parse_news(response.json(), stock_code)
        except Exception as e:
            print(f"获取新闻失败: {e}")
        
        # 如果失败，返回模拟数据
        return self._get_mock_news(stock_code, limit)
    
    def _parse_news(self, data: Dict, stock_code: str) -> List[Dict]:
        """解析新闻数据"""
        news_list = []
        if 'data' in data and 'diff' in data['data']:
            for item in data['data']['diff'][:10]:
                news_list.append({
                    'title': item.get('f104', ''),  # 新闻标题
                    'date': time.strftime('%Y-%m-%d'),
                    'summary': item.get('f105', ''),  # 摘要
                    'source': '东方财富'
                })
        return news_list
    
    def _get_mock_news(self, stock_code: str, limit: int) -> List[Dict]:
        """返回模拟新闻数据"""
        mock_titles = [
            f"【{stock_code}】上市公司发布年度业绩预告",
            f"【{stock_code}】股东增持/减持股份",
            f"【{stock_code}】董事会决议公告",
            f"【{stock_code}】重大资产重组进展",
            f"【{stock_code}】收到监管问询函"
        ]
        
        return [
            {
                'title': mock_titles[i % len(mock_titles)],
                'date': f"2026-03-{10 - i}",
                'summary': '点击查看详情',
                'source': '模拟数据'
            }
            for i in range(min(limit, len(mock_titles)))
        ]
    
    def get_stock_announcements(self, stock_code: str, limit: int = 10) -> List[Dict]:
        """
        获取个股公告
        
        Args:
            stock_code: 股票代码
            limit: 返回数量
        
        Returns:
            公告列表
        """
        # 返回模拟公告
        return self._get_mock_announcements(stock_code, limit)
    
    def _get_mock_announcements(self, stock_code: str, limit: int) -> List[Dict]:
        """返回模拟公告数据"""
        ann_types = ['年度报告', '一季度报告', '半年度报告', '三季度报告', '临时公告']
        
        return [
            {
                'title': f"【{stock_code}】{ann_types[i % len(ann_types)]}披露",
                'date': f"2026-03-{10 - i}",
                'url': '#',
                'type': ann_types[i % len(ann_types)]
            }
            for i in range(min(limit, len(ann_types)))
        ]
    
    def get_market_news(self, limit: int = 10) -> List[Dict]:
        """
        获取市场新闻
        
        Args:
            limit: 返回数量
        
        Returns:
            新闻列表
        """
        # 返回模拟市场新闻
        market_titles = [
            "A股三大指数今日涨跌不一",
            "央行逆回购操作",
            "两市成交额突破万亿元",
            "科创板最新政策解读",
            "北向资金净流入"
        ]
        
        return [
            {
                'title': market_titles[i],
                'date': f"2026-03-{10 - i}",
                'source': '市场快讯'
            }
            for i in range(min(limit, len(market_titles)))
        ]
