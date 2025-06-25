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
    stage: Optional[str] = "full"  # 阶段模式：'full'(完整), 'users_only'(仅用户列表), 'details_only'(仅详细信息)

class ScrapeResponse(BaseModel):
    success: bool
    message: str
    platform: str
    total_extracted: int
    data: List[Dict]
    download_url: str
    current_page: int
    has_next_page: bool
    cache_id: str

class StreamingControlRequest(BaseModel):
    session_id: str
    action: str  # 'pause', 'resume', 'stop'

class BatchDetailsRequest(BaseModel):
    users: List[Dict[str, str]]  # 用户列表
    original_owner: str  # 原始仓库的owner
    original_repo: str   # 原始仓库名

# 全局会话管理
streaming_sessions = {}

class StreamingSession:
    def __init__(self, session_id: str, request: ScrapeRequest):
        self.session_id = session_id
        self.request = request
        self.is_paused = False
        self.is_stopped = False
        self.is_running = False
        self.progress_generator = None
        self.current_data = []

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_stopped = True
        self.is_running = False

def detect_platform(url: str) -> str:
    """检测URL对应的平台"""
    url = url.lower()

    if 'github.com' in url:
        return 'github'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'twitter'
    elif 'producthunt.com' in url:
        return 'producthunt'
    elif 'weibo.com' in url:
        return 'weibo'
    elif 'news.ycombinator.com' in url:
        return 'hackernews'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'reddit.com' in url:
        return 'reddit'
    elif 'medium.com' in url:
        return 'medium'
    elif 'bilibili.com' in url:
        return 'bilibili'
    else:
        raise ValueError(f"不支持的平台: {url}")

# 数据缓存（在生产环境中应该使用数据库或Redis）
data_cache = {}

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
            print("未找到数据，但仍返回空结果")
            data = []

        # 生成缓存ID
        cache_id = str(uuid.uuid4())

        # 保存到内存缓存
        cache_data = {
            'platform': platform,
            'data': data,
            'page': request.page,
            'has_next': has_next,
            'timestamp': datetime.now().isoformat()
        }
        data_cache[cache_id] = cache_data

        print(f"缓存数据到 {cache_id}")

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
    """流式爬取接口 - 边爬边返回数据，支持控制"""
    session_id = str(uuid.uuid4())

    async def generate_stream() -> AsyncGenerator[str, None]:
        session = StreamingSession(session_id, request)
        streaming_sessions[session_id] = session
        session.is_running = True

        try:
            # 发送开始消息，包含session_id
            yield f"data: {json.dumps({'type': 'start', 'message': '开始爬取...', 'url': request.url, 'session_id': session_id})}\n\n"

            # 检测平台
            platform = detect_platform(request.url)
            yield f"data: {json.dumps({'type': 'platform', 'platform': platform, 'session_id': session_id})}\n\n"

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
                yield f"data: {json.dumps({'type': 'error', 'message': f'不支持的平台: {platform}', 'session_id': session_id})}\n\n"
                return

            # 为GitHub特殊处理，支持流式爬取
            if platform == 'github' and hasattr(scraper, 'scrape_with_progress'):
                session.progress_generator = scraper.scrape_with_progress(request.url, max_users=request.max_users)

                async for progress_data in session.progress_generator:
                    # 检查控制状态
                    while session.is_paused and not session.is_stopped:
                        await asyncio.sleep(0.5)

                    if session.is_stopped:
                        yield f"data: {json.dumps({'type': 'stopped', 'message': '爬取已停止', 'session_id': session_id})}\n\n"
                        break

                    # 添加session_id到所有消息
                    progress_data['session_id'] = session_id

                    # 如果是用户完成消息，保存数据
                    if progress_data.get('type') == 'user_completed' and progress_data.get('user_data'):
                        session.current_data.append(progress_data['user_data'])

                    yield f"data: {json.dumps(progress_data)}\n\n"
                    await asyncio.sleep(0.1)  # 小延迟避免前端处理不过来
            else:
                # 其他平台的普通爬取
                yield f"data: {json.dumps({'type': 'progress', 'message': f'正在爬取{platform}数据...', 'session_id': session_id})}\n\n"

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

                session.current_data = data

                # 发送最终结果
                yield f"data: {json.dumps({
                    'type': 'complete',
                    'data': data,
                    'total': len(data),
                    'has_next_page': has_next,
                    'current_page': request.page,
                    'platform': platform,
                    'session_id': session_id,
                    'message': f'爬取完成！共获取 {len(data)} 个用户信息'
                })}\n\n"

        except Exception as e:
            error_msg = f"爬取过程中出错: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'session_id': session_id})}\n\n"
        finally:
            # 清理会话
            session.is_running = False
            if session_id in streaming_sessions:
                del streaming_sessions[session_id]

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

@app.post("/api/streaming-control")
async def control_streaming(request: StreamingControlRequest):
    """控制流式爬取：暂停、继续、停止"""
    if request.session_id not in streaming_sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = streaming_sessions[request.session_id]

    if request.action == 'pause':
        session.pause()
        return {"success": True, "message": "爬取已暂停", "session_id": request.session_id}
    elif request.action == 'resume':
        session.resume()
        return {"success": True, "message": "爬取已继续", "session_id": request.session_id}
    elif request.action == 'stop':
        session.stop()
        return {"success": True, "message": "爬取已停止", "session_id": request.session_id}
    else:
        raise HTTPException(status_code=400, detail="无效的操作")

@app.get("/api/streaming-status/{session_id}")
async def get_streaming_status(session_id: str):
    """获取流式爬取状态"""
    if session_id not in streaming_sessions:
        return {"exists": False, "message": "会话不存在或已过期"}

    session = streaming_sessions[session_id]
    return {
        "exists": True,
        "is_running": session.is_running,
        "is_paused": session.is_paused,
        "is_stopped": session.is_stopped,
        "data_count": len(session.current_data),
        "session_id": session_id
    }

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

@app.post("/api/github-forks/batch-details")
async def get_batch_user_details(request: BatchDetailsRequest):
    """批量获取GitHub fork用户的详细信息（阶段2）"""
    try:
        print(f"开始批量获取 {len(request.users)} 个用户的详细信息")

        scraper = GitHubScraper()

        # 执行阶段2：获取用户详细信息
        detailed_users = await scraper._scrape_forks_users_details(
            request.users,
            request.original_owner,
            request.original_repo
        )

        print(f"批量获取完成，成功获取 {len(detailed_users)} 个用户的详细信息")

        # 生成缓存ID
        cache_id = str(uuid.uuid4())

        # 保存到内存缓存
        cache_data = {
            'platform': 'github',
            'data': detailed_users,
            'page': 1,
            'has_next': False,
            'timestamp': datetime.now().isoformat()
        }
        data_cache[cache_id] = cache_data

        return ScrapeResponse(
            success=True,
            message=f"成功获取 {len(detailed_users)} 个用户的详细信息",
            platform='github',
            total_extracted=len(detailed_users),
            data=detailed_users,
            download_url=f"/api/export-csv/{cache_id}",
            current_page=1,
            has_next_page=False,
            cache_id=cache_id
        )

    except Exception as e:
        print(f"批量获取用户详细信息出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户详细信息失败: {str(e)}")

@app.get("/api/export-csv/{cache_id}")
async def export_csv(cache_id: str):
    """导出缓存数据为CSV文件"""
    try:
        if cache_id not in data_cache:
            raise HTTPException(status_code=404, detail="数据不存在或已过期")

        cache_data = data_cache[cache_id]
        platform = cache_data['platform']
        data = cache_data['data']
        page = cache_data['page']

        if not data:
            raise HTTPException(status_code=404, detail="没有可导出的数据")

        # 创建临时CSV文件
        csv_filename = f"follownet_{platform}_page{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
        await scraper.save_to_csv(data, csv_path)
        print(f"CSV文件已生成: {csv_path}")

        return FileResponse(
            path=csv_path,
            filename=csv_filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
        )

    except Exception as e:
        print(f"导出CSV时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "FollowNet API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)