import re
from typing import List, Dict, Any
from .base import BaseScraper

class ProductHuntScraper(BaseScraper):
    """Product Hunt爬取器"""
    
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """爬取Product Hunt数据"""
        await self.setup_browser()
        
        try:
            # 解析URL类型
            if '/posts/' in url:
                return await self._scrape_product_voters(url)
            elif '/users/' in url:
                return await self._scrape_user_activity(url)
            else:
                raise ValueError("无法识别的Product Hunt URL格式")
        
        finally:
            await self.cleanup()
    
    async def _scrape_product_voters(self, url: str) -> List[Dict[str, Any]]:
        """爬取产品的投票者"""
        await self.page.goto(url)
        
        # 等待页面加载
        await self.wait_for_element('[data-test="vote-button"]', timeout=15000)
        
        # 点击投票按钮查看投票者
        vote_button = await self.page.query_selector('[data-test="vote-button"]')
        if vote_button:
            await vote_button.click()
            await self.page.wait_for_timeout(2000)
        
        # 等待投票者列表加载
        await self.wait_for_element('[data-test="voter-item"]', timeout=10000)
        
        # 滚动加载更多投票者
        await self.scroll_to_load_more(max_scrolls=10)
        
        # 提取投票者信息
        voters = []
        voter_elements = await self.page.query_selector_all('[data-test="voter-item"]')
        
        for element in voter_elements:
            try:
                # 提取用户名
                username_elem = await element.query_selector('a[href*="/users/"]')
                username = None
                if username_elem:
                    href = await username_elem.get_attribute('href')
                    if href:
                        username = href.split('/users/')[-1]
                
                # 提取显示名称
                name_elem = await element.query_selector('.voter-name')
                display_name = await name_elem.text_content() if name_elem else None
                
                # 提取个人简介
                bio_elem = await element.query_selector('.voter-bio')
                bio = await bio_elem.text_content() if bio_elem else None
                
                # 提取头像URL
                avatar_elem = await element.query_selector('.voter-avatar img')
                avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
                
                # 提取投票时间
                time_elem = await element.query_selector('.voter-time')
                vote_time = await time_elem.text_content() if time_elem else None
                
                if username:
                    voters.append({
                        'username': username,
                        'display_name': display_name or username,
                        'bio': bio,
                        'avatar_url': avatar_url,
                        'profile_url': f'https://www.producthunt.com/users/{username}',
                        'vote_time': vote_time,
                        'type': 'voter'
                    })
            
            except Exception as e:
                print(f"提取Product Hunt投票者信息时出错: {e}")
                continue
        
        return voters
    
    async def _scrape_user_activity(self, url: str) -> List[Dict[str, Any]]:
        """爬取用户的活动信息"""
        await self.page.goto(url)
        
        # 等待用户页面加载
        await self.wait_for_element('.user-profile', timeout=15000)
        
        # 提取用户基本信息
        user_info = []
        
        try:
            # 提取用户名
            username_elem = await self.page.query_selector('.user-username')
            username = await username_elem.text_content() if username_elem else None
            
            # 提取显示名称
            name_elem = await self.page.query_selector('.user-name')
            display_name = await name_elem.text_content() if name_elem else None
            
            # 提取个人简介
            bio_elem = await self.page.query_selector('.user-bio')
            bio = await bio_elem.text_content() if bio_elem else None
            
            # 提取头像URL
            avatar_elem = await self.page.query_selector('.user-avatar img')
            avatar_url = await avatar_elem.get_attribute('src') if avatar_elem else None
            
            # 提取关注者数量
            followers_elem = await self.page.query_selector('.followers-count')
            followers_count = await followers_elem.text_content() if followers_elem else None
            
            # 提取关注数量
            following_elem = await self.page.query_selector('.following-count')
            following_count = await following_elem.text_content() if following_elem else None
            
            # 提取外部链接
            links_elements = await self.page.query_selector_all('.user-links a')
            external_links = []
            for link_elem in links_elements:
                link_url = await link_elem.get_attribute('href')
                if link_url:
                    external_links.append(link_url)
            
            if username:
                user_info.append({
                    'username': username,
                    'display_name': display_name or username,
                    'bio': bio,
                    'avatar_url': avatar_url,
                    'profile_url': url,
                    'followers_count': followers_count,
                    'following_count': following_count,
                    'external_links': ', '.join(external_links),
                    'type': 'user_profile'
                })
        
        except Exception as e:
            print(f"提取Product Hunt用户信息时出错: {e}")
        
        return user_info 