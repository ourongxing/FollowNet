from abc import ABC, abstractmethod
import csv
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict, Any

class BaseScraper(ABC):
    """基础爬取器抽象类"""
    
    def __init__(self):
        self.browser = None
        self.page = None
    
    async def setup_browser(self):
        """设置浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # 设置用户代理以避免检测
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    async def cleanup(self):
        """清理资源"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    @abstractmethod
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """爬取数据的抽象方法"""
        pass
    
    def normalize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化用户数据字段"""
        normalized = {
            'username': user_data.get('username', ''),
            'display_name': user_data.get('display_name', ''),
            'bio': user_data.get('bio', ''),
            'avatar_url': user_data.get('avatar_url', ''),
            'profile_url': user_data.get('profile_url', ''),
            'platform': user_data.get('platform', 'unknown'),
            'type': user_data.get('type', 'user'),
            'follower_count': user_data.get('follower_count', ''),
            'following_count': user_data.get('following_count', ''),
            'company': user_data.get('company', ''),
            'location': user_data.get('location', ''),
            'website': user_data.get('website', ''),
            'twitter': user_data.get('twitter', ''),
            'additional_info': user_data.get('additional_info', ''),
            'scraped_at': user_data.get('scraped_at', ''),
        }
        
        # 合并其他特定平台的字段到additional_info
        platform_specific = {}
        for key, value in user_data.items():
            if key not in normalized and value:
                platform_specific[key] = str(value)
        
        if platform_specific:
            additional_info = []
            if normalized['additional_info']:
                additional_info.append(normalized['additional_info'])
            
            for key, value in platform_specific.items():
                additional_info.append(f"{key}: {value}")
            
            normalized['additional_info'] = '; '.join(additional_info)
        
        return normalized
    
    async def save_to_csv(self, data: List[Dict[str, Any]], filepath: str):
        """将数据保存为CSV文件"""
        if not data:
            return
        
        # 标准化所有数据
        normalized_data = [self.normalize_user_data(item) for item in data]
        
        # 使用标准字段名
        fieldnames = [
            'username', 'display_name', 'bio', 'avatar_url', 'profile_url',
            'platform', 'type', 'follower_count', 'following_count', 
            'company', 'location', 'website', 'twitter', 'additional_info', 'scraped_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized_data)
    
    async def wait_for_element(self, selector: str, timeout: int = 10000):
        """等待元素出现"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def scroll_to_load_more(self, max_scrolls: int = 10):
        """滚动页面以加载更多内容"""
        for i in range(max_scrolls):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            # 检查是否还有更多内容
            current_height = await self.page.evaluate("document.body.scrollHeight")
            await asyncio.sleep(1)
            new_height = await self.page.evaluate("document.body.scrollHeight")
            
            if current_height == new_height:
                break 