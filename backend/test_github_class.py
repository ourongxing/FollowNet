#!/usr/bin/env python3
"""
测试完整的GitHubScraper类
"""
import asyncio
import sys
import os

# 添加scrapers目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from scrapers.github import GitHubScraper

async def test_github_scraper():
    """测试GitHubScraper类"""
    
    scraper = GitHubScraper()
    
    try:
        print("测试GitHub followers爬取...")
        url = "https://github.com/connor4312?tab=followers"
        
        result = await scraper.scrape(url)
        
        print(f"爬取结果: {len(result)} 条数据")
        
        for i, item in enumerate(result[:5], 1):  # 只显示前5条
            print(f"{i}. {item.get('username', 'N/A')} - {item.get('display_name', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    result = asyncio.run(test_github_scraper())
    print(f"\n总共获取了 {len(result)} 条数据") 