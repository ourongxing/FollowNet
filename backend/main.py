from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import os
import asyncio
from urllib.parse import urlparse
import tempfile
import uuid
from typing import Optional, List, Dict, AsyncGenerator
from datetime import datetime
import json

from scrapers.github_two_stage import GitHubTwoStageScraper as GitHubScraper
from scrapers.twitter import TwitterScraper
from scrapers.producthunt import ProductHuntScraper
from scrapers.weibo import WeiboScraper
from scrapers.hackernews import HackerNewsScraper
from scrapers.youtube import YouTubeScraper
from scrapers.reddit import RedditScraper
from scrapers.medium import MediumScraper
from scrapers.bilibili import BilibiliScraper

app = FastAPI(title="FollowNet API", version="1.0.0")

# 启用CORS以允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    page: Optional[int] = 1  # 添加页码参数
    max_users: Optional[int] = 10  # 添加最大用户数参数

class ScrapeResponse(BaseModel):
    success: bool
    message: str
    platform: Optional[str] = None
    total_extracted: Optional[int] = None
    data: Optional[List[Dict]] = None
    download_url: Optional[str] = None
    current_page: Optional[int] = None  # 当前页码
    has_next_page: Optional[bool] = None  # 是否有下一页
    cache_id: Optional[str] = None  # 缓存ID，用于后续分页请求

# 存储爬取结果的内存缓存
scrape_cache = {}

def detect_platform(url: str) -> str:
    """根据URL检测平台类型"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if 'github.com' in domain:
        return 'github'
    elif 'twitter.com' in domain or 'x.com' in domain:
        return 'twitter'
    elif 'producthunt.com' in domain:
        return 'producthunt'
    elif 'weibo.com' in domain:
        return 'weibo'
    elif 'news.ycombinator.com' in domain:
        return 'hackernews'
    elif 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'
    elif 'reddit.com' in domain:
        return 'reddit'
    elif 'medium.com' in domain:
        return 'medium'
    elif 'bilibili.com' in domain:
        return 'bilibili'
    else:
        raise ValueError(f"不支持的平台: {domain}")

@app.get("/")
async def root():
    return {"message": "FollowNet API 正在运行"}

@app.get("/test-github-direct")
async def test_github_direct():
    """直接测试GitHub爬取器"""
    try:
        print("=== 直接测试GitHub爬取器 ===")

        scraper = GitHubScraper()
        url = "https://github.com/connor4312?tab=followers"

        print(f"测试URL: {url}")

        result = await scraper.scrape(url)

        print(f"爬取结果数量: {len(result) if result else 0}")

        if result:
            print(f"前3条结果:")
            for i, item in enumerate(result[:3], 1):
                print(f"  {i}. {item.get('username', 'N/A')} - {item.get('display_name', 'N/A')}")

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

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_followers(request: ScrapeRequest):
    """分页爬取接口"""
    try:
        print(f"开始处理请求: {request.url}, 页码: {request.page}")

        # 检测平台
        platform = detect_platform(request.url)
        print(f"检测到平台: {platform}")

        # 选择对应的爬取器
        if platform == 'github':
            scraper = GitHubScraper()
        elif platform == 'twitter':
            scraper = TwitterScraper()
        elif platform == 'producthunt':
            scraper = ProductHuntScraper()
        elif platform == 'weibo':
            scraper = WeiboScraper()
        elif platform == 'hackernews':
            scraper = HackerNewsScraper()
        elif platform == 'youtube':
            scraper = YouTubeScraper()
        elif platform == 'reddit':
            scraper = RedditScraper()
        elif platform == 'medium':
            scraper = MediumScraper()
        elif platform == 'bilibili':
            scraper = BilibiliScraper()
        else:
            raise HTTPException(status_code=400, detail="不支持的平台")

        print(f"开始执行第{request.page}页爬取，最多{request.max_users}个用户...")

        # 检查是否支持分页爬取
        if hasattr(scraper, 'scrape_page'):
            # 使用分页爬取
            result = await scraper.scrape_page(request.url, request.page)
            has_next = result.get('has_next_page', False)
            data = result.get('data', [])
        else:
            # 兼容旧版本，只支持第一页
            if request.page > 1:
                return ScrapeResponse(
                    success=False,
                    message="该平台暂不支持分页爬取",
                    platform=platform,
                    current_page=request.page
                )
            # 对于GitHub，传递max_users参数
            if platform == 'github' and hasattr(scraper, 'scrape'):
                result = await scraper.scrape(request.url, max_users=request.max_users)
            else:
                result = await scraper.scrape(request.url)
            data = result if result else []
            has_next = False

        print(f"第{request.page}页爬取完成，结果数量: {len(data)}")

        if not data or len(data) == 0:
            print("返回失败响应：未找到数据")
            return ScrapeResponse(
                success=False,
                message="未找到数据或爬取失败",
                platform=platform,
                current_page=request.page
            )

        # 生成缓存ID
        cache_key = f"{request.url}_{request.page}"
        cache_id = str(uuid.uuid4())
        scrape_cache[cache_id] = {
            'data': data,
            'platform': platform,
            'url': request.url,
            'page': request.page,
            'scraped_at': datetime.now().isoformat()
        }

        print(f"数据已缓存，ID: {cache_id}")

        return ScrapeResponse(
            success=True,
            message=f"成功爬取第{request.page}页 {len(data)} 条数据",
            platform=platform,
            total_extracted=len(data),
            data=data,
            download_url=f"/api/export-csv/{cache_id}",
            current_page=request.page,
            has_next_page=has_next,
            cache_id=cache_id
        )

    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")

@app.post("/api/scrape-stream")
async def scrape_stream(request: ScrapeRequest):
    """流式爬取接口 - 边爬边返回数据"""

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # 发送开始消息
            yield f"data: {json.dumps({'type': 'start', 'message': '开始爬取...', 'url': request.url})}\n\n"

            # 检测平台
            platform = detect_platform(request.url)
            yield f"data: {json.dumps({'type': 'platform', 'platform': platform})}\n\n"

            # 创建爬取器
            if platform == 'github':
                scraper = GitHubScraper()
            elif platform == 'twitter':
                scraper = TwitterScraper()
            elif platform == 'producthunt':
                scraper = ProductHuntScraper()
            elif platform == 'weibo':
                scraper = WeiboScraper()
            elif platform == 'hackernews':
                scraper = HackerNewsScraper()
            elif platform == 'youtube':
                scraper = YouTubeScraper()
            elif platform == 'reddit':
                scraper = RedditScraper()
            elif platform == 'medium':
                scraper = MediumScraper()
            elif platform == 'bilibili':
                scraper = BilibiliScraper()
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': f'不支持的平台: {platform}'})}\n\n"
                return

            # 为GitHub特殊处理，支持流式爬取
            if platform == 'github' and hasattr(scraper, 'scrape_with_progress'):
                async for progress_data in scraper.scrape_with_progress(request.url, max_users=request.max_users):
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    await asyncio.sleep(0.1)  # 小延迟避免前端处理不过来
            else:
                # 其他平台的普通爬取
                yield f"data: {json.dumps({'type': 'progress', 'message': f'正在爬取{platform}数据...'})}\n\n"

                if hasattr(scraper, 'scrape_page'):
                    result = await scraper.scrape_page(request.url, request.page)
                    data = result.get('data', [])
                    has_next = result.get('has_next_page', False)
                else:
                    if platform == 'github':
                        result = await scraper.scrape(request.url, max_users=request.max_users)
                    else:
                        result = await scraper.scrape(request.url)
                    data = result if result else []
                    has_next = False

                # 发送最终结果
                yield f"data: {json.dumps({
                    'type': 'complete',
                    'data': data,
                    'total': len(data),
                    'has_next_page': has_next,
                    'current_page': request.page,
                    'platform': platform
                })}\n\n"

        except Exception as e:
            error_msg = f"爬取过程中出错: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/scrape-and-download")
async def scrape_and_download(request: ScrapeRequest):
    """爬取数据并直接下载CSV文件"""
    try:
        print(f"开始爬取并下载: {request.url}, 页码: {request.page}")

        # 检测平台
        platform = detect_platform(request.url)
        print(f"检测到平台: {platform}")

        # 选择对应的爬取器
        if platform == 'github':
            scraper = GitHubScraper()
        elif platform == 'twitter':
            scraper = TwitterScraper()
        elif platform == 'producthunt':
            scraper = ProductHuntScraper()
        elif platform == 'weibo':
            scraper = WeiboScraper()
        elif platform == 'hackernews':
            scraper = HackerNewsScraper()
        elif platform == 'youtube':
            scraper = YouTubeScraper()
        elif platform == 'reddit':
            scraper = RedditScraper()
        elif platform == 'medium':
            scraper = MediumScraper()
        elif platform == 'bilibili':
            scraper = BilibiliScraper()
        else:
            raise HTTPException(status_code=400, detail="不支持的平台")

        print(f"开始执行第{request.page}页爬取，最多{request.max_users}个用户...")

        # 检查是否支持分页爬取
        if hasattr(scraper, 'scrape_page'):
            # 使用分页爬取
            result = await scraper.scrape_page(request.url, request.page)
            has_next = result.get('has_next_page', False)
            data = result.get('data', [])
        else:
            # 兼容旧版本，只支持第一页
            if request.page > 1:
                raise HTTPException(status_code=400, detail="该平台暂不支持分页爬取")
            # 对于GitHub，传递max_users参数
            if platform == 'github' and hasattr(scraper, 'scrape'):
                result = await scraper.scrape(request.url, max_users=request.max_users)
            else:
                result = await scraper.scrape(request.url)
            data = result if result else []
            has_next = False

        print(f"第{request.page}页爬取完成，结果数量: {len(data)}")

        if not data or len(data) == 0:
            raise HTTPException(status_code=404, detail="未找到数据或爬取失败")

        # 直接生成并返回CSV文件
        from urllib.parse import urlparse, quote
        parsed_url = urlparse(request.url)
        url_parts = parsed_url.path.strip('/').split('/')

        if len(url_parts) >= 1:
            identifier = url_parts[0] if url_parts[0] else "unknown"
        else:
            identifier = "unknown"

        csv_filename = f"follownet_{platform}_{identifier}_page{request.page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(tempfile.gettempdir(), csv_filename)

        # 保存数据到CSV
        await scraper.save_to_csv(data, csv_path)
        print(f"CSV文件已生成: {csv_path}")

        return FileResponse(
            path=csv_path,
            filename=csv_filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
        )

    except ValueError as e:
        print(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")

@app.get("/api/export-csv/{cache_id}")
async def export_csv(cache_id: str):
    """导出CSV文件"""
    if cache_id not in scrape_cache:
        raise HTTPException(status_code=404, detail="数据未找到或已过期")

    cached_data = scrape_cache[cache_id]
    result = cached_data['data']
    platform = cached_data['platform']
    page = cached_data.get('page', 1)

    # 生成CSV文件
    csv_filename = f"follownet_{platform}_page{page}_data_{cache_id}.csv"
    csv_path = os.path.join(tempfile.gettempdir(), csv_filename)

    # 根据平台选择对应的爬取器来保存CSV
    if platform == 'github':
        scraper = GitHubScraper()
    elif platform == 'twitter':
        scraper = TwitterScraper()
    elif platform == 'producthunt':
        scraper = ProductHuntScraper()
    elif platform == 'weibo':
        scraper = WeiboScraper()
    elif platform == 'hackernews':
        scraper = HackerNewsScraper()
    elif platform == 'youtube':
        scraper = YouTubeScraper()
    elif platform == 'reddit':
        scraper = RedditScraper()
    elif platform == 'medium':
        scraper = MediumScraper()
    elif platform == 'bilibili':
        scraper = BilibiliScraper()
    else:
        raise HTTPException(status_code=400, detail="不支持的平台")

    # 保存数据到CSV
    await scraper.save_to_csv(result, csv_path)
    print(f"CSV文件已生成: {csv_path}")

    return FileResponse(
        path=csv_path,
        filename=csv_filename,
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)