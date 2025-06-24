import re
from typing import List, Dict, Any
from .base import BaseScraper

class WeiboScraper(BaseScraper):
    """微博爬取器"""
    
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """爬取微博数据"""
        await self.setup_browser()
        
        try:
            # 解析URL类型
            if '/fans' in url:
                return await self._scrape_fans(url)
            elif '/follow' in url:
                return await self._scrape_following(url)
            else:
                # 如果是用户主页，默认爬取粉丝
                if re.match(r'https://weibo\.com/u/\d+/?$', url) or re.match(r'https://weibo\.com/[^/]+/?$', url):
                    fans_url = url.rstrip('/') + '/fans'
                    return await self._scrape_fans(fans_url)
                else:
                    raise ValueError("无法识别的微博URL格式")
        
        finally:
            await self.cleanup()
    
    async def _scrape_fans(self, url: str) -> List[Dict[str, Any]]:
        """爬取用户的粉丝"""
        await self.page.goto(url)
        
        # 等待内容加载
        await self.wait_for_element('.card-wrap', timeout=15000)
        
        # 滚动加载更多
        await self.scroll_to_load_more(max_scrolls=20)
        
        # 提取粉丝信息
        fans = []
        user_elements = await self.page.query_selector_all('.card-wrap .info')
        
        for element in user_elements:
            try:
                # 提取用户名
                username_elem = await element.query_selector('.name a')
                username = await username_elem.text_content() if username_elem else None
                profile_url = await username_elem.get_attribute('href') if username_elem else None
                
                # 提取个人简介
                bio_elem = await element.query_selector('.item')
                bio = await bio_elem.text_content() if bio_elem else None
                
                # 提取头像URL
                avatar_elem = await element.query_selector('../img')
                avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
                
                # 提取关注状态
                follow_elem = await element.query_selector('.follow')
                follow_status = await follow_elem.text_content() if follow_elem else None
                
                if username:
                    fans.append({
                        'username': username.strip(),
                        'display_name': username.strip(),
                        'bio': bio.strip() if bio else None,
                        'avatar_url': avatar_url,
                        'profile_url': f'https://weibo.com{profile_url}' if profile_url else None,
                        'follow_status': follow_status,
                        'type': 'fan'
                    })
            
            except Exception as e:
                print(f"提取微博粉丝信息时出错: {e}")
                continue
        
        return fans
    
    async def _scrape_following(self, url: str) -> List[Dict[str, Any]]:
        """爬取用户关注的人"""
        await self.page.goto(url)
        
        # 等待内容加载
        await self.wait_for_element('.card-wrap', timeout=15000)
        
        # 滚动加载更多
        await self.scroll_to_load_more(max_scrolls=20)
        
        # 提取关注的人的信息
        following = []
        user_elements = await self.page.query_selector_all('.card-wrap .info')
        
        for element in user_elements:
            try:
                # 提取用户名
                username_elem = await element.query_selector('.name a')
                username = await username_elem.text_content() if username_elem else None
                profile_url = await username_elem.get_attribute('href') if username_elem else None
                
                # 提取个人简介
                bio_elem = await element.query_selector('.item')
                bio = await bio_elem.text_content() if bio_elem else None
                
                # 提取头像URL
                avatar_elem = await element.query_selector('../img')
                avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
                
                # 提取粉丝数等统计信息
                stats_elem = await element.query_selector('.num')
                stats = await stats_elem.text_content() if stats_elem else None
                
                if username:
                    following.append({
                        'username': username.strip(),
                        'display_name': username.strip(),
                        'bio': bio.strip() if bio else None,
                        'avatar_url': avatar_url,
                        'profile_url': f'https://weibo.com{profile_url}' if profile_url else None,
                        'stats': stats,
                        'type': 'following'
                    })
            
            except Exception as e:
                print(f"提取微博关注信息时出错: {e}")
                continue
        
        return following 