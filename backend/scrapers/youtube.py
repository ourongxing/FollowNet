import re
from typing import List, Dict, Any
from .base import BaseScraper

class YouTubeScraper(BaseScraper):
    """YouTube爬取器"""
    
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """爬取YouTube数据"""
        await self.setup_browser()
        
        try:
            # 解析URL类型
            if '/watch?' in url:
                return await self._scrape_video_comments(url)
            elif '/channel/' in url or '/c/' in url or '/user/' in url:
                return await self._scrape_channel_info(url)
            else:
                raise ValueError("无法识别的YouTube URL格式")
        
        finally:
            await self.cleanup()
    
    async def _scrape_video_comments(self, url: str) -> List[Dict[str, Any]]:
        """爬取视频评论"""
        await self.page.goto(url)
        
        # 等待页面加载
        await self.wait_for_element('#comments', timeout=15000)
        
        # 滚动到评论区
        await self.page.evaluate("document.querySelector('#comments').scrollIntoView()")
        await self.page.wait_for_timeout(3000)
        
        # 滚动加载更多评论
        await self.scroll_to_load_more(max_scrolls=15)
        
        # 提取评论信息
        comments = []
        comment_elements = await self.page.query_selector_all('#comments ytd-comment-thread-renderer')
        
        for element in comment_elements:
            try:
                # 提取用户名
                username_elem = await element.query_selector('#author-text')
                username = await username_elem.text_content() if username_elem else None
                
                # 提取评论内容
                comment_elem = await element.query_selector('#content-text')
                comment_text = await comment_elem.text_content() if comment_elem else None
                
                # 提取头像URL
                avatar_elem = await element.query_selector('#author-thumbnail img')
                avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
                
                # 提取点赞数
                like_elem = await element.query_selector('#vote-count-middle')
                likes = await like_elem.text_content() if like_elem else None
                
                # 提取发布时间
                time_elem = await element.query_selector('.published-time-text')
                publish_time = await time_elem.text_content() if time_elem else None
                
                if username and comment_text:
                    comments.append({
                        'username': username.strip(),
                        'display_name': username.strip(),
                        'comment': comment_text.strip(),
                        'avatar_url': avatar_url,
                        'likes': likes,
                        'publish_time': publish_time,
                        'type': 'video_comment'
                    })
            
            except Exception as e:
                print(f"提取YouTube评论信息时出错: {e}")
                continue
        
        return comments
    
    async def _scrape_channel_info(self, url: str) -> List[Dict[str, Any]]:
        """爬取频道信息"""
        await self.page.goto(url)
        
        # 等待频道页面加载
        await self.wait_for_element('#channel-header', timeout=15000)
        
        # 提取频道基本信息
        channel_info = []
        
        try:
            # 提取频道名称
            channel_name_elem = await self.page.query_selector('#channel-name')
            channel_name = await channel_name_elem.text_content() if channel_name_elem else None
            
            # 提取订阅者数量
            subscriber_elem = await self.page.query_selector('#subscriber-count')
            subscriber_count = await subscriber_elem.text_content() if subscriber_elem else None
            
            # 提取频道简介
            description_elem = await self.page.query_selector('#description')
            description = await description_elem.text_content() if description_elem else None
            
            # 提取频道头像
            avatar_elem = await self.page.query_selector('#channel-header img')
            avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
            
            # 提取视频数量
            video_count_elem = await self.page.query_selector('#videos-count')
            video_count = await video_count_elem.text_content() if video_count_elem else None
            
            if channel_name:
                channel_info.append({
                    'channel_name': channel_name.strip(),
                    'display_name': channel_name.strip(),
                    'subscriber_count': subscriber_count,
                    'description': description.strip() if description else None,
                    'avatar_url': avatar_url,
                    'video_count': video_count,
                    'profile_url': url,
                    'type': 'channel_info'
                })
        
        except Exception as e:
            print(f"提取YouTube频道信息时出错: {e}")
        
        return channel_info 