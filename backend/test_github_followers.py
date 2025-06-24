#!/usr/bin/env python3
"""
GitHub Followers 爬取测试脚本
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_github_followers():
    """测试GitHub followers爬取功能"""
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        url = "https://github.com/connor4312?tab=followers"
        print(f"开始爬取关注者页面: {url}")
        
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(3)
        
        # 使用最准确的用户链接选择器
        user_links = await page.query_selector_all('a[data-hovercard-type="user"]')
        print(f"找到 {len(user_links)} 个用户链接元素")
        
        if not user_links:
            print("未找到用户链接")
            return []
        
        # 提取关注者信息
        followers = []
        current_time = datetime.now().isoformat()
        processed_users = set()  # 用于去重
        
        for link in user_links:
            try:
                href = await link.get_attribute('href')
                if not href or not href.startswith('/'):
                    continue
                
                username = href.strip('/')
                
                # 去重处理（因为每个用户有两个链接）
                if username in processed_users:
                    continue
                processed_users.add(username)
                
                # 获取显示名称
                text_content = await link.text_content()
                display_name = username  # 默认使用用户名
                bio = ''
                
                if text_content and text_content.strip():
                    # 处理显示名和用户名的组合文本
                    text_lines = [line.strip() for line in text_content.strip().split('\n') if line.strip()]
                    if len(text_lines) >= 2:
                        # 第一行是显示名，第二行是用户名
                        display_name = text_lines[0]
                    elif len(text_lines) == 1 and text_lines[0] != username:
                        display_name = text_lines[0]
                
                # 尝试获取头像URL（从data-hovercard-url或构造）
                avatar_url = f'https://github.com/{username}.png'
                
                follower_data = {
                    'username': username,
                    'display_name': display_name,
                    'bio': bio,
                    'avatar_url': avatar_url,
                    'profile_url': f'https://github.com/{username}',
                    'platform': 'github',
                    'type': 'follower',
                    'scraped_at': current_time
                }
                
                followers.append(follower_data)
                print(f"添加关注者: {username} ({display_name})")
                
                # 限制数量避免过多数据
                if len(followers) >= 10:
                    break
            
            except Exception as e:
                print(f"处理用户链接时出错: {e}")
                continue
        
        print(f"成功提取了 {len(followers)} 个关注者")
        return followers
        
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_github_followers())
    print("\n=== 最终结果 ===")
    for i, follower in enumerate(result, 1):
        print(f"{i}. {follower['username']} - {follower['display_name']}") 