import asyncio
import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright

class GitHubFollowersListScraper:
    """GitHub第一阶段：批量获取followers/stargazers用户名列表（支持分页）"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def scrape_followers_list(self, username: str, max_pages: int = 10) -> str:
        """
        爬取用户的followers列表
        
        Args:
            username: GitHub用户名
            max_pages: 最大爬取页数
            
        Returns:
            CSV文件路径
        """
        print(f"🚀 第一阶段：开始爬取 {username} 的followers列表...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 设置用户代理
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        followers = []
        
        try:
            for page_num in range(1, max_pages + 1):
                # GitHub followers分页URL格式
                url = f"https://github.com/{username}?page={page_num}&tab=followers"
                print(f"📄 正在爬取第 {page_num} 页: {url}")
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # 获取当前页面的用户链接
                user_links = await page.query_selector_all('a[data-hovercard-type="user"]')
                
                if not user_links:
                    print(f"第 {page_num} 页没有找到用户链接，停止爬取")
                    break
                
                page_followers = []
                seen_usernames = set()
                
                for link in user_links:
                    try:
                        href = await link.get_attribute('href')
                        if href and href.startswith('/'):
                            follower_username = href.strip('/')
                            if follower_username and follower_username not in seen_usernames:
                                seen_usernames.add(follower_username)
                                page_followers.append({
                                    'username': follower_username,
                                    'profile_url': f'https://github.com/{follower_username}',
                                    'type': 'follower',
                                    'source_user': username,
                                    'page_number': page_num,
                                    'scraped_at': datetime.now().isoformat()
                                })
                    except Exception as e:
                        print(f"处理用户链接时出错: {e}")
                        continue
                
                print(f"第 {page_num} 页获取到 {len(page_followers)} 个followers")
                followers.extend(page_followers)
                
                # 检查是否还有下一页
                next_selectors = [
                    '.pagination a:last-child',  # GitHub的下一页按钮
                    'a[href*="page=' + str(page_num + 1) + '"]',  # 包含下一页页码的链接
                    '.pagination a[rel="next"]'  # 标准的next链接
                ]
                
                has_next_page = False
                for selector in next_selectors:
                    try:
                        next_button = await page.query_selector(selector)
                        if next_button:
                            button_text = await next_button.text_content()
                            button_href = await next_button.get_attribute('href')
                            print(f"找到下一页按钮: text='{button_text}', href='{button_href}'")
                            
                            # 检查是否真的是下一页链接
                            if (button_text and 'next' in button_text.lower()) or \
                               (button_href and f'page={page_num + 1}' in button_href):
                                has_next_page = True
                                break
                    except Exception as e:
                        print(f"检查选择器 {selector} 时出错: {e}")
                        continue
                
                if not has_next_page:
                    print(f"没有下一页，总共爬取了 {page_num} 页")
                    break
                
                # 避免请求过快
                await asyncio.sleep(1)
            
            # 保存到CSV文件
            csv_file = await self._save_to_csv(followers, f"{username}_followers_raw.csv")
            print(f"✅ 第一阶段完成！总共获取 {len(followers)} 个followers，保存到: {csv_file}")
            
            return csv_file
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return ""
        finally:
            await browser.close()
            await playwright.stop()
    
    async def scrape_stargazers_list(self, owner: str, repo: str, max_pages: int = 10) -> str:
        """
        爬取Repositories的stargazers列表
        
        Args:
            owner: Repositories所有者
            repo: Repositories名
            max_pages: 最大爬取页数
            
        Returns:
            CSV文件路径
        """
        print(f"🚀 第一阶段：开始爬取 {owner}/{repo} 的stargazers列表...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 设置用户代理
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        stargazers = []
        
        try:
            for page_num in range(1, max_pages + 1):
                # GitHub stargazers分页URL格式
                url = f"https://github.com/{owner}/{repo}/stargazers?page={page_num}"
                print(f"📄 正在爬取第 {page_num} 页: {url}")
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # 获取当前页面的用户链接
                user_links = await page.query_selector_all('a[data-hovercard-type="user"]')
                
                if not user_links:
                    print(f"第 {page_num} 页没有找到用户链接，停止爬取")
                    break
                
                page_stargazers = []
                seen_usernames = set()
                
                for link in user_links:
                    try:
                        href = await link.get_attribute('href')
                        if href and href.startswith('/'):
                            stargazer_username = href.strip('/')
                            if stargazer_username and stargazer_username not in seen_usernames:
                                seen_usernames.add(stargazer_username)
                                page_stargazers.append({
                                    'username': stargazer_username,
                                    'profile_url': f'https://github.com/{stargazer_username}',
                                    'type': 'stargazer',
                                    'source_repo': f'{owner}/{repo}',
                                    'page_number': page_num,
                                    'scraped_at': datetime.now().isoformat()
                                })
                    except Exception as e:
                        print(f"处理用户链接时出错: {e}")
                        continue
                
                print(f"第 {page_num} 页获取到 {len(page_stargazers)} 个stargazers")
                stargazers.extend(page_stargazers)
                
                # 检查是否还有下一页
                next_selectors = [
                    '.pagination a:last-child',  # GitHub的下一页按钮
                    'a[href*="page=' + str(page_num + 1) + '"]',  # 包含下一页页码的链接
                    '.pagination a[rel="next"]'  # 标准的next链接
                ]
                
                has_next_page = False
                for selector in next_selectors:
                    try:
                        next_button = await page.query_selector(selector)
                        if next_button:
                            button_text = await next_button.text_content()
                            button_href = await next_button.get_attribute('href')
                            print(f"找到下一页按钮: text='{button_text}', href='{button_href}'")
                            
                            # 检查是否真的是下一页链接
                            if (button_text and 'next' in button_text.lower()) or \
                               (button_href and f'page={page_num + 1}' in button_href):
                                has_next_page = True
                                break
                    except Exception as e:
                        print(f"检查选择器 {selector} 时出错: {e}")
                        continue
                
                if not has_next_page:
                    print(f"没有下一页，总共爬取了 {page_num} 页")
                    break
                
                # 避免请求过快
                await asyncio.sleep(1)
            
            # 保存到CSV文件
            csv_file = await self._save_to_csv(stargazers, f"{owner}_{repo}_stargazers_raw.csv")
            print(f"✅ 第一阶段完成！总共获取 {len(stargazers)} 个stargazers，保存到: {csv_file}")
            
            return csv_file
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return ""
        finally:
            await browser.close()
            await playwright.stop()
    
    async def _save_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """保存数据到CSV文件"""
        if not data:
            return ""
        
        csv_path = os.path.join(self.data_dir, filename)
        
        # 定义CSV字段
        fieldnames = ['username', 'profile_url', 'type', 'source_user', 'source_repo', 'page_number', 'scraped_at']
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # 确保所有字段都存在
                row = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        return csv_path

# 测试函数
async def main():
    scraper = GitHubFollowersListScraper()
    
    # 测试爬取followers
    csv_file = await scraper.scrape_followers_list("connor4312", max_pages=3)
    print(f"结果文件: {csv_file}")

if __name__ == "__main__":
    asyncio.run(main()) 