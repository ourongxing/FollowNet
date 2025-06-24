#!/usr/bin/env python3
"""
调试API - 专门测试GitHub爬取器
"""
from fastapi import FastAPI
import asyncio
from scrapers.github import GitHubScraper

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "调试API运行中"}

@app.get("/test-github")
async def test_github():
    """测试GitHub爬取器"""
    try:
        print("=== 开始测试GitHub爬取器 ===")
        
        scraper = GitHubScraper()
        url = "https://github.com/connor4312?tab=followers"
        
        print(f"测试URL: {url}")
        
        result = await scraper.scrape(url)
        
        print(f"爬取结果数量: {len(result) if result else 0}")
        
        if result:
            print(f"前3条结果:")
            for i, item in enumerate(result[:3], 1):
                print(f"  {i}. {item.get('username', 'N/A')} - {item.get('display_name', 'N/A')}")
        else:
            print("没有结果")
        
        return {
            "success": True,
            "total": len(result) if result else 0,
            "sample_data": result[:3] if result else []
        }
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 