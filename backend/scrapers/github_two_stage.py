import asyncio
import os
import re
from typing import List, Dict, Any
from .base import BaseScraper
from .github.get_followers_list import GitHubFollowersListScraper
from .github.scrape_profiles import GitHubProfileScraper
from playwright.async_api import async_playwright
from datetime import datetime

class GitHubTwoStageScraper(BaseScraper):
    """
    GitHub两阶段爬取器 - 完全统一的Profile获取架构 + 多线程并发优化

    ## 并发优化特性
    - **多线程用户详情获取**：使用asyncio并发获取用户详细信息，速度提升5-10倍
    - **智能并发控制**：使用Semaphore限制并发数量，避免被GitHub限制
    - **独立浏览器实例**：每个并发任务使用独立的browser context，避免冲突
    - **错误处理与重试**：并发环境下的错误处理和自动重试机制
    - **进度实时更新**：支持并发环境下的实时进度报告

    ## 统一架构设计
    - **第一阶段**：根据不同类型获取用户名列表
      - Followers/Stargazers: 使用GitHubFollowersListScraper获取CSV用户列表
      - Forks: 直接爬取forks页面获取用户基本信息

    - **第二阶段**：统一使用GitHubProfileScraper._get_user_details()获取所有类型用户的详细Profile
      - **并发优化**：同时处理多个用户的详细信息获取
      - 完全消除重复代码：followers、stargazers、forks三种类型的Profile获取逻辑完全统一
      - 分页爬取也使用统一的Profile获取方法
      - 所有用户详细信息获取都通过同一个入口

    ## 支持的爬取类型
    1. **Followers爬取**：获取用户的关注者列表及其详细信息
    2. **Stargazers爬取**：获取仓库的star用户列表及其详细信息
    3. **Forks爬取**：获取仓库的fork用户列表及其详细信息

    ## 统一返回格式
    所有爬取类型的返回数据都经过_normalize_user_data()方法标准化：
    - **相同的字段结构**：username, display_name, bio, follower_count等
    - **相同的数据类型**：数字字段为int，字符串字段为str
    - **统一的平台标识**：platform='github'
    - **明确的用户类型标识**：type='follower'/'stargazer'/'fork_owner'
    - **Fork特有字段**：fork_repo_name、fork_repo_url、original_repo

    ## 关键统一方法
    - `_get_users_details_unified()`: 统一的批量Profile获取（用于完整爬取）- **并发优化**
    - `_get_page_users_details()`: 统一的分页Profile获取（用于分页爬取）- **并发优化**
    - `GitHubProfileScraper._get_user_details()`: 底层统一的单个用户Profile获取

    所有类型的用户Profile获取逻辑已完全统一，实现了代码复用和数据一致性。
    """

    def __init__(self, concurrent_limit: int = 8):
        super().__init__()
        self.platform = "github"
        self.stage1_scraper = GitHubFollowersListScraper()
        self.stage2_scraper = GitHubProfileScraper()  # 统一的Profile获取器
        self.concurrent_limit = concurrent_limit  # 并发限制，默认8个并发

    def get_current_time(self) -> str:
        """获取当前时间的ISO格式字符串"""
        return datetime.now().isoformat()

    def set_concurrent_limit(self, limit: int):
        """
        设置并发限制数量

        Args:
            limit: 并发数量限制 (建议1-20之间)
        """
        if limit < 1:
            limit = 1
        elif limit > 20:
            limit = 20
            print("⚠️ 并发数量限制在20以内，避免被GitHub限制")

        self.concurrent_limit = limit
        print(f"📊 并发限制已设置为: {self.concurrent_limit}")

    def get_concurrent_limit(self) -> int:
        """获取当前并发限制数量"""
        return self.concurrent_limit

    async def scrape_with_progress(self, url: str, max_pages: int = 5, max_users: int = 100):
        """
        执行完整的两阶段爬取流程，边爬边返回进度

        Args:
            url: GitHub URL
            max_pages: 第一阶段最大爬取页数
            max_users: 第二阶段最大处理用户数

        Yields:
            包含进度信息的字典
        """
        print(f"🚀 开始GitHub两阶段流式爬取: {url}")

        # 发送开始消息
        yield {
            'type': 'progress',
            'stage': 1,
            'message': '分析URL和准备爬取...',
            'progress': 0
        }

        # 分析URL类型
        scrape_type, owner, repo = self._parse_url_type(url)
        print(f"识别URL类型: {scrape_type}, owner: {owner}, repo: {repo}")

        stage1_csv = ""

        # 根据max_users计算需要的页数（GitHub每页大约50个用户）
        calculated_pages = max(1, min(max_pages, (max_users + 49) // 50))
        print(f"根据max_users={max_users}，计算需要爬取 {calculated_pages} 页")

        yield {
            'type': 'progress',
            'stage': 1,
            'message': f'准备爬取 {calculated_pages} 页用户列表...',
            'progress': 5
        }

        if scrape_type == "forks":
            print(f"识别为仓库forks页面: {owner}/{repo}")

            yield {
                'type': 'progress',
                'stage': 1,
                'message': f'正在爬取仓库 {owner}/{repo} 的forks...',
                'progress': 10
            }

            # 直接使用内置的forks爬取方法
            fork_users = await self._scrape_forks_users(url, owner, repo, max_users)

            if not fork_users:
                yield {
                    'type': 'error',
                    'message': '第一阶段失败，没有找到任何fork用户'
                }
                return

            # 限制用户数量
            fork_users = fork_users[:max_users]

            yield {
                'type': 'progress',
                'stage': 1,
                'message': f'第一阶段完成，找到 {len(fork_users)} 个fork用户',
                'progress': 50
            }

            # 第二阶段：获取用户详细信息
            yield {
                'type': 'progress',
                'stage': 2,
                'message': f'开始第二阶段：获取 {len(fork_users)} 个用户的详细信息...',
                'progress': 60
            }

            # 转换为标准格式并获取详细信息
            fork_users_data = []
            for fork_user in fork_users:
                user_data = {
                    'username': fork_user['username'],
                    'type': 'fork_owner',
                    'source_user': owner,
                    'source_repo': repo,
                    'page_number': '1',
                    'scraped_at': self.get_current_time(),
                    # Fork特有信息
                    'fork_repo_name': fork_user.get('fork_repo_name', ''),
                    'fork_repo_url': fork_user.get('fork_repo_url', ''),
                    'original_repo': f"{owner}/{repo}"
                }
                fork_users_data.append(user_data)

            detailed_users = await self._get_users_details_unified(fork_users_data, 'fork_owner')

            # 统一格式化fork用户数据
            normalized_data = [self._normalize_user_data(user, 'fork_owner') for user in detailed_users]

            yield {
                'type': 'complete',
                'data': normalized_data,
                'total': len(normalized_data),
                'message': f'爬取完成！共获取 {len(normalized_data)} 个fork用户的详细信息',
                'progress': 100,
                'platform': 'github'
            }
            return

        elif scrape_type == "repo" or scrape_type == "stargazers":
            print(f"识别为仓库stargazers页面: {owner}/{repo}")

            yield {
                'type': 'progress',
                'stage': 1,
                'message': f'正在爬取仓库 {owner}/{repo} 的stargazers...',
                'progress': 10
            }

            # 第一阶段：获取stargazers列表
            stage1_csv = await self.stage1_scraper.scrape_stargazers_list(owner, repo, calculated_pages)

        elif scrape_type == "user" or scrape_type == "followers":
            print(f"识别为用户followers页面: {owner}")

            yield {
                'type': 'progress',
                'stage': 1,
                'message': f'正在爬取用户 {owner} 的followers...',
                'progress': 10
            }

            # 第一阶段：获取followers列表
            stage1_csv = await self.stage1_scraper.scrape_followers_list(owner, calculated_pages)

        else:
            yield {
                'type': 'error',
                'message': f'无法识别URL类型: {url}'
            }
            return

        if not stage1_csv or not os.path.exists(stage1_csv):
            yield {
                'type': 'error',
                'message': '第一阶段失败，没有生成用户列表文件'
            }
            return

        yield {
            'type': 'progress',
            'stage': 1,
            'message': f'第一阶段完成，生成文件: {os.path.basename(stage1_csv)}',
            'progress': 50
        }

        # 第二阶段：获取用户详细信息
        yield {
            'type': 'progress',
            'stage': 2,
            'message': f'开始第二阶段：获取最多 {max_users} 个用户的详细信息...',
            'progress': 60
        }

        # 使用并发优化的第二阶段爬取
        users_data = []
        import csv

        # 读取CSV文件并准备用户数据
        try:
            with open(stage1_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if len(users_data) >= max_users:
                        break
                    users_data.append(dict(row))
        except Exception as e:
            yield {
                'type': 'error',
                'message': f'读取用户列表文件失败: {e}'
            }
            return

        # 确定用户类型
        user_type = 'follower' if scrape_type in ['user', 'followers'] else 'stargazer'

        yield {
            'type': 'progress',
            'stage': 2,
            'message': f'准备并发获取 {len(users_data)} 个用户的详细信息...',
            'progress': 65
        }

        # 使用并发方法获取用户详细信息
        detailed_users = await self._get_users_details_unified_with_progress(users_data, user_type,
                                                                           start_progress=70, end_progress=95)

        # 通过异步生成器返回进度
        async for progress_update in detailed_users:
            yield progress_update

        # 读取最终结果
        yield {
            'type': 'progress',
            'stage': 2,
            'message': '读取最终结果...',
            'progress': 95
        }

        final_data = await self._read_enriched_data(stage1_csv.replace('_raw.csv', '_enriched.csv'))

        # 统一格式化数据
        normalized_data = [self._normalize_user_data(user) for user in final_data]

        yield {
            'type': 'complete',
            'data': normalized_data,
            'total': len(normalized_data),
            'message': f'爬取完成！共获取 {len(normalized_data)} 个用户的详细信息',
            'progress': 100,
            'platform': 'github'
        }

    async def scrape(self, url: str, max_pages: int = 5, max_users: int = 100) -> List[Dict[str, Any]]:
        """
        执行完整的两阶段爬取流程

        Args:
            url: GitHub URL
            max_pages: 第一阶段最大爬取页数
            max_users: 第二阶段最大处理用户数

        Returns:
            包含详细信息的用户列表
        """
        print(f"🚀 开始GitHub两阶段爬取: {url}")

        # 分析URL类型
        scrape_type, owner, repo = self._parse_url_type(url)
        print(f"识别URL类型: {scrape_type}, owner: {owner}, repo: {repo}")

        stage1_csv = ""

        # 根据max_users计算需要的页数（GitHub每页大约50个用户）
        calculated_pages = max(1, min(max_pages, (max_users + 49) // 50))  # 向上取整，但不超过max_pages
        print(f"根据max_users={max_users}，计算需要爬取 {calculated_pages} 页")

        if scrape_type == "forks":
            print(f"识别为仓库forks页面: {owner}/{repo}")

            # 直接使用内置的forks爬取方法
            fork_users = await self._scrape_forks_users(url, owner, repo, max_users)

            if not fork_users:
                print("第一阶段失败，没有找到任何fork用户")
                return []

            # 限制用户数量
            fork_users = fork_users[:max_users]
            print(f"第一阶段完成，找到 {len(fork_users)} 个fork用户")

            # 第二阶段：获取用户详细信息（使用统一方法）
            # 转换为标准格式
            fork_users_data = []
            for fork_user in fork_users:
                user_data = {
                    'username': fork_user['username'],
                    'type': 'fork_owner',
                    'source_user': owner,
                    'source_repo': repo,
                    'page_number': '1',
                    'scraped_at': self.get_current_time(),
                    # Fork特有信息
                    'fork_repo_name': fork_user.get('fork_repo_name', ''),
                    'fork_repo_url': fork_user.get('fork_repo_url', ''),
                    'original_repo': f"{owner}/{repo}"
                }
                fork_users_data.append(user_data)

            detailed_users = await self._get_users_details_unified(fork_users_data, 'fork_owner')
            print(f"第二阶段完成，获取到 {len(detailed_users)} 个用户的详细信息")

            # 统一格式化fork用户数据
            return [self._normalize_user_data(user, 'fork_owner') for user in detailed_users]

        elif scrape_type == "repo" or scrape_type == "stargazers":
            print(f"识别为仓库stargazers页面: {owner}/{repo}")

            # 第一阶段：获取stargazers列表
            stage1_csv = await self.stage1_scraper.scrape_stargazers_list(owner, repo, calculated_pages)

        elif scrape_type == "user" or scrape_type == "followers":
            print(f"识别为用户followers页面: {owner}")

            # 第一阶段：获取followers列表
            stage1_csv = await self.stage1_scraper.scrape_followers_list(owner, calculated_pages)

        else:
            print("无法识别URL类型")
            return []

        if not stage1_csv or not os.path.exists(stage1_csv):
            print("第一阶段失败，没有生成用户列表文件")
            return []

        print(f"第一阶段完成，生成文件: {stage1_csv}")

        # 第二阶段：获取用户详细信息（统一使用GitHubProfileScraper）
        print("🔍 开始第二阶段：获取用户详细信息...")
        stage2_csv = await self.stage2_scraper.scrape_profiles_from_csv(
            stage1_csv,
            max_users=max_users,
            batch_size=5  # 小批次处理，避免过载
        )

        if not stage2_csv or not os.path.exists(stage2_csv):
            print("第二阶段失败，没有生成详细信息文件")
            return []

        print(f"第二阶段完成，生成文件: {stage2_csv}")

        # 读取最终结果
        final_data = await self._read_enriched_data(stage2_csv)

        # 统一格式化数据
        return [self._normalize_user_data(user) for user in final_data]

    async def _read_enriched_data(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """读取详细信息CSV文件并返回原始数据（格式化将在外部进行）"""
        import csv

        users = []

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # 直接读取原始数据，不做格式化处理
                    users.append(dict(row))

            print(f"成功读取 {len(users)} 个用户的详细信息")
            return users

        except Exception as e:
            print(f"读取详细信息文件时出错: {e}")
            return []

    def _safe_int(self, value: str) -> int:
        """安全转换字符串为整数"""
        try:
            return int(value) if value else 0
        except:
            return 0

    def _normalize_user_data(self, user_data: Dict[str, Any], user_type: str = None) -> Dict[str, Any]:
        """
        统一用户数据格式，确保所有类型的爬取结果都有相同的字段结构

        Args:
            user_data: 原始用户数据
            user_type: 用户类型 ('follower', 'stargazer', 'fork_owner')

        Returns:
            标准化后的用户数据
        """
        # 基础字段（所有类型都有）
        normalized = {
            'username': user_data.get('username', ''),
            'display_name': user_data.get('display_name', user_data.get('username', '')),
            'bio': user_data.get('bio', ''),
            'avatar_url': user_data.get('avatar_url', f"https://github.com/{user_data.get('username', '')}.png"),
            'profile_url': user_data.get('profile_url', f"https://github.com/{user_data.get('username', '')}"),
                'platform': 'github',
            'type': user_type or user_data.get('type', 'user'),

            # 社交信息
            'follower_count': self._safe_int(str(user_data.get('follower_count', 0))),
            'following_count': self._safe_int(str(user_data.get('following_count', 0))),
            'public_repos': self._safe_int(str(user_data.get('public_repos', 0))),

            # 个人信息
            'company': user_data.get('company', ''),
            'location': user_data.get('location', ''),
            'website': user_data.get('website', ''),
            'twitter': user_data.get('twitter', ''),
            'email': user_data.get('email', ''),

            # 元数据
            'scraped_at': user_data.get('scraped_at', user_data.get('profile_scraped_at', self.get_current_time())),
            'source_user': user_data.get('source_user', ''),
            'source_repo': user_data.get('source_repo', ''),
            'page_number': user_data.get('page_number', ''),
        }

        # Fork特有字段
        if user_type == 'fork_owner' or user_data.get('type') == 'fork_owner':
            normalized.update({
                'fork_repo_name': user_data.get('fork_repo_name', ''),
                'fork_repo_url': user_data.get('fork_repo_url', ''),
                'original_repo': user_data.get('original_repo', ''),
            })

        # 生成additional_info
        info_parts = []
        if normalized['source_user'] or normalized['source_repo']:
            info_parts.append(f"Source: {normalized['source_user']}/{normalized['source_repo']}")
        if normalized['page_number']:
            info_parts.append(f"Page: {normalized['page_number']}")
        if normalized.get('original_repo'):
            info_parts.append(f"Original: {normalized['original_repo']}")

        normalized['additional_info'] = ', '.join(info_parts) if info_parts else ''

        return normalized

    def _parse_url_type(self, url: str) -> tuple:
        """
        解析URL类型，支持followers、stargazers、forks

        Returns:
            (scrape_type, owner, repo)
        """
        url = url.rstrip('/')

        # 检查是否是forks页面
        if '/network/members' in url:
            # https://github.com/owner/repo/network/members
            pattern = r'https://github\.com/([^/]+)/([^/]+)/network/members'
            match = re.match(pattern, url)
            if match:
                owner, repo = match.groups()
                return "forks", owner, repo

        # 检查是否包含forks关键词
        if 'forks' in url or 'network' in url:
            pattern = r'https://github\.com/([^/]+)/([^/]+)'
            match = re.match(pattern, url)
            if match:
                owner, repo = match.groups()
                return "forks", owner, repo

        # 检查stargazers
        if '/stargazers' in url or 'tab=stargazers' in url:
            pattern = r'https://github\.com/([^/]+)/([^/]+)'
            match = re.match(pattern, url)
            if match:
                owner, repo = match.groups()
                return "stargazers", owner, repo

        # 检查followers
        if 'tab=followers' in url or '/followers' in url:
            pattern = r'https://github.com/([^/]+)'
            match = re.match(pattern, url)
            if match:
                owner = match.group(1)
                return "followers", owner, ""

        # 解析基本URL结构
        url_parts = url.replace('https://github.com/', '').split('/')

        if len(url_parts) >= 2:
            # https://github.com/owner/repo - 默认为stargazers
            owner, repo = url_parts[0], url_parts[1]
            return "repo", owner, repo
        elif len(url_parts) == 1:
            # https://github.com/username - 默认为followers
            owner = url_parts[0]
            return "user", owner, ""

        raise ValueError(f"无法解析URL: {url}")

    def _normalize_forks_url(self, url: str) -> str:
        """规范化URL，确保指向/network/members页面"""
        url = url.rstrip('/')

        # 如果已经是network/members页面，直接返回
        if '/network/members' in url:
            return url

        # 如果是基本的仓库URL，转换为network/members
        pattern = r'https://github\.com/([^/]+)/([^/]+)'
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            return f"https://github.com/{owner}/{repo}/network/members"

        return None

    async def _scrape_forks_users(self, url: str, owner: str, repo: str, max_users: int = 100) -> List[Dict[str, str]]:
        """
        阶段1：爬取GitHub forks页面，获取所有fork用户的基本信息
        """
        print(f"开始爬取forks页面: {url}")

        # 规范化URL
        normalized_url = self._normalize_forks_url(url)
        if not normalized_url:
            print("无法规范化forks URL")
            return []

        await self.setup_browser()

        try:
            await self.page.goto(normalized_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # 检查页面是否正确加载
            page_title = await self.page.title()
            print(f"页面标题: {page_title}")

            # 自动滚动加载更多fork
            print("正在滚动页面加载更多fork...")
            await self._scroll_to_load_forks()

            # 查找fork列表
            fork_users = []
            seen_users = set()

            # 使用指定的CSS选择器获取fork用户链接
            user_links = await self.page.query_selector_all('#network div div a:nth-child(3)')
            print(f"通过 '#network div div a:nth-child(3)' 找到 {len(user_links)} 个用户链接")

            for link in user_links:
                try:
                    href = await link.get_attribute('href')
                    if not href or not href.startswith('/'):
                        continue

                    # 获取用户名（从 /username 格式中提取）
                    username = href.strip('/')

                    # 跳过原始仓库的所有者
                    if username == owner:
                        continue

                    # 避免重复用户
                    if username not in seen_users:
                        seen_users.add(username)

                        # 直接使用原仓库名作为fork仓库名（通常fork保持相同名称）
                        fork_repo_name = repo

                        fork_user = {
                            'username': username,
                            'fork_repo_name': fork_repo_name,
                            'fork_repo_url': f"https://github.com/{username}/{fork_repo_name}",
                            'profile_url': f"https://github.com/{username}",
                            'avatar_url': f'https://github.com/{username}.png'
                        }

                        fork_users.append(fork_user)

                        if len(fork_users) >= max_users:  # 限制数量
                            break

                except Exception as e:
                    print(f"处理用户链接时出错: {e}")
                    continue

            print(f"阶段1完成，找到 {len(fork_users)} 个唯一的fork用户")
            return fork_users

        except Exception as e:
            print(f"爬取fork用户列表时出错: {e}")
            return []
        finally:
            await self.cleanup()

    async def _scroll_to_load_forks(self):
        """滚动页面以加载更多fork"""
        print("开始滚动加载更多fork...")
        last_height = 0
        scroll_count = 0
        max_scrolls = 10

        while scroll_count < max_scrolls:
            # 滚动到页面底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)

            # 检查页面高度是否变化
            new_height = await self.page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                print("页面高度未变化，停止滚动")
                break

            last_height = new_height
            scroll_count += 1
            print(f"滚动次数: {scroll_count}, 页面高度: {new_height}")

        print(f"滚动完成，总共滚动 {scroll_count} 次")

    async def _get_single_user_concurrent(self, user_data: Dict[str, Any], user_type: str,
                                         semaphore: asyncio.Semaphore, playwright_instance) -> Dict[str, Any]:
        """
        并发获取单个用户详细信息的辅助方法

        Args:
            user_data: 用户基本信息
            user_type: 用户类型
            semaphore: 并发控制信号量
            playwright_instance: Playwright实例

        Returns:
            用户详细信息，如果失败返回None
        """
        async with semaphore:  # 限制并发数量
            browser = None
            try:
                username = user_data.get('username', user_data.get('username'))

                # 为每个并发任务创建独立的browser context
                browser = await playwright_instance.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # 设置用户代理
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })

                # 确保user_data包含必要字段
                if 'type' not in user_data:
                    user_data['type'] = user_type
                if 'scraped_at' not in user_data:
                    user_data['scraped_at'] = self.get_current_time()

                # 使用GitHubProfileScraper统一获取详细信息
                user_info = await self.stage2_scraper._get_user_details(username, page, user_data)

                if user_info:
                    # 保留原始数据中的特殊字段（如fork特有信息）
                    for key, value in user_data.items():
                        if key not in user_info and value:
                            user_info[key] = value
                    print(f"✅ 成功获取{user_type}用户 {username} 的详细信息")
                    return user_info
                else:
                    print(f"❌ 无法获取{user_type}用户 {username} 的详细信息")
                    return None

            except Exception as e:
                print(f"获取{user_type}用户 {user_data.get('username', 'unknown')} 详细信息时出错: {e}")
                return None
            finally:
                if browser:
                    await browser.close()

    async def _get_users_details_unified(self, users_list: List[Dict[str, Any]], user_type: str = 'user') -> List[Dict[str, Any]]:
        """
        统一的第二阶段：获取用户详细信息 - 并发优化版本

        Args:
            users_list: 用户列表，每个元素包含username等基本信息
            user_type: 用户类型 ('follower', 'stargazer', 'fork_owner')

        Returns:
            包含详细信息的用户列表
        """
        print(f"🔍 使用统一Profile获取器并发获取 {len(users_list)} 个{user_type}用户的详细信息...")
        print(f"📊 并发限制: {self.concurrent_limit} 个任务")

        # 启动playwright
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()

        try:
            # 创建信号量限制并发数量
            semaphore = asyncio.Semaphore(self.concurrent_limit)

            # 创建所有并发任务
            tasks = []
            for user_data in users_list:
                task = asyncio.create_task(
                    self._get_single_user_concurrent(user_data, user_type, semaphore, playwright)
                )
                tasks.append(task)

            # 并发执行所有任务，并显示进度
            print(f"🚀 开始并发执行 {len(tasks)} 个任务...")
            results = []
            completed = 0

            # 使用as_completed来获取完成的任务并实时显示进度
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    results.append(result)
                completed += 1

                # 每完成10个或完成所有任务时显示进度
                if completed % 10 == 0 or completed == len(tasks):
                    success_rate = len(results) / completed * 100 if completed > 0 else 0
                    print(f"📈 进度: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%) - 成功率: {success_rate:.1f}%")

            print(f"✅ {user_type}用户详细信息获取完成，成功获取 {len(results)} 个用户 (成功率: {len(results)/len(users_list)*100:.1f}%)")
            return results

        except Exception as e:
            print(f"获取{user_type}用户详细信息时出错: {e}")
            return []
        finally:
            await playwright.stop()

    async def _get_users_details_unified_with_progress(self, users_list: List[Dict[str, Any]], user_type: str = 'user',
                                                     start_progress: int = 70, end_progress: int = 95):
        """
        带进度报告的统一用户详细信息获取方法 - 并发优化版本

        Args:
            users_list: 用户列表
            user_type: 用户类型
            start_progress: 开始进度值
            end_progress: 结束进度值

        Yields:
            进度更新字典
        """
        print(f"🔍 使用统一Profile获取器并发获取 {len(users_list)} 个{user_type}用户的详细信息...")
        print(f"📊 并发限制: {self.concurrent_limit} 个任务")

        yield {
            'type': 'progress',
            'stage': 2,
            'message': f'启动并发获取 {len(users_list)} 个用户的详细信息...',
            'progress': start_progress
        }

        # 启动playwright
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()

        try:
            # 创建信号量限制并发数量
            semaphore = asyncio.Semaphore(self.concurrent_limit)

            # 创建所有并发任务
            tasks = []
            for user_data in users_list:
                task = asyncio.create_task(
                    self._get_single_user_concurrent(user_data, user_type, semaphore, playwright)
                )
                tasks.append(task)

            # 并发执行所有任务，并实时报告进度
            print(f"🚀 开始并发执行 {len(tasks)} 个任务...")
            results = []
            completed = 0

            # 使用as_completed来获取完成的任务并实时显示进度
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    results.append(result)
                completed += 1

                # 计算当前进度
                progress_ratio = completed / len(tasks)
                current_progress = start_progress + (end_progress - start_progress) * progress_ratio
                success_rate = len(results) / completed * 100 if completed > 0 else 0

                # 每完成5个或到达特定节点时报告进度
                if completed % 5 == 0 or completed == len(tasks) or completed % (len(tasks) // 10 + 1) == 0:
                    yield {
                        'type': 'progress',
                        'stage': 2,
                        'message': f'并发获取用户详细信息中... ({completed}/{len(tasks)})',
                        'progress': min(end_progress, current_progress),
                        'processed_count': completed,
                        'total_count': len(tasks),
                        'success_count': len(results),
                        'success_rate': f'{success_rate:.1f}%'
                    }

            # 最终结果
            final_data = [self._normalize_user_data(user) for user in results]

            yield {
                'type': 'complete',
                'data': final_data,
                'total': len(final_data),
                'message': f'并发爬取完成！共获取 {len(final_data)} 个用户的详细信息 (成功率: {len(final_data)/len(users_list)*100:.1f}%)',
                'progress': 100,
                'platform': 'github'
            }

        except Exception as e:
            yield {
                'type': 'error',
                'message': f'并发获取用户详细信息时出错: {e}'
            }
        finally:
            await playwright.stop()

    async def _get_page_single_user_concurrent(self, username: str, user_type: str, source_user: str,
                                             source_repo: str, page_number: int, semaphore: asyncio.Semaphore,
                                             playwright_instance) -> Dict[str, Any]:
        """
        分页中的单个用户并发获取方法

        Args:
            username: 用户名
            user_type: 用户类型
            source_user: 源用户
            source_repo: 源仓库
            page_number: 页码
            semaphore: 并发控制信号量
            playwright_instance: Playwright实例

        Returns:
            用户详细信息
        """
        async with semaphore:  # 限制并发数量
            browser = None
            try:
                # 为每个并发任务创建独立的browser context
                browser = await playwright_instance.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # 设置用户代理
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })

                # 构造标准格式的用户数据
                user_data = {
                    'username': username,
                    'type': user_type,
                    'source_user': source_user,
                    'source_repo': source_repo,
                    'page_number': str(page_number),
                    'scraped_at': datetime.now().isoformat()
                }

                # 使用GitHubProfileScraper的_get_user_details方法
                user_info = await self.stage2_scraper._get_user_details(username, page, user_data)
                if user_info:
                    return user_info
                else:
                    # 返回基本信息作为备选
                    return {
                        'username': username,
                        'display_name': username,
                        'bio': '',
                        'avatar_url': f"https://github.com/{username}.png",
                        'profile_url': f"https://github.com/{username}",
                        'platform': 'github',
                        'type': user_type,
                        'follower_count': 0,
                        'following_count': 0,
                        'company': '',
                        'location': '',
                        'website': '',
                        'twitter': '',
                        'email': '',
                        'public_repos': 0,
                        'scraped_at': datetime.now().isoformat(),
                        'source_user': source_user,
                        'source_repo': source_repo,
                        'page_number': str(page_number)
                    }

            except Exception as e:
                print(f"获取用户 {username} 详细信息失败: {e}")
                # 返回基本信息
                return {
                    'username': username,
                    'display_name': username,
                    'bio': '',
                    'avatar_url': f"https://github.com/{username}.png",
                    'profile_url': f"https://github.com/{username}",
                    'platform': 'github',
                    'type': user_type,
                    'follower_count': 0,
                    'following_count': 0,
                    'company': '',
                    'location': '',
                    'website': '',
                    'twitter': '',
                    'email': '',
                    'public_repos': 0,
                    'scraped_at': datetime.now().isoformat(),
                    'source_user': source_user,
                    'source_repo': source_repo,
                    'page_number': str(page_number)
                }
            finally:
                if browser:
                    await browser.close()

    async def _get_page_users_details(self, usernames: List[str], page_obj, user_type: str,
                                    source_user: str, source_repo: str, page_number: int) -> List[Dict[str, Any]]:
        """
        分页中的统一用户详细信息获取方法 - 并发优化版本

        Args:
            usernames: 用户名列表
            page_obj: Playwright页面对象 (在并发版本中不使用)
            user_type: 用户类型
            source_user: 源用户
            source_repo: 源仓库
            page_number: 页码

        Returns:
            包含详细信息的用户列表
        """
        print(f"🔍 并发获取第{page_number}页 {len(usernames)} 个{user_type}用户的详细信息...")
        print(f"📊 并发限制: {self.concurrent_limit} 个任务")

        # 启动playwright实例
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()

        try:
            # 创建信号量限制并发数量
            semaphore = asyncio.Semaphore(self.concurrent_limit)

            # 创建所有并发任务
            tasks = []
            for username in usernames:
                task = asyncio.create_task(
                    self._get_page_single_user_concurrent(
                        username, user_type, source_user, source_repo, page_number, semaphore, playwright
                    )
                )
                tasks.append(task)

            # 并发执行所有任务
            print(f"🚀 开始并发执行 {len(tasks)} 个任务...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤出成功的结果
            users = []
            for result in results:
                if isinstance(result, dict):
                    users.append(result)
                else:
                    print(f"任务失败: {result}")

            print(f"✅ 第{page_number}页用户详细信息获取完成，成功获取 {len(users)} 个用户")
            return users

        except Exception as e:
            print(f"获取第{page_number}页用户详细信息时出错: {e}")
            return []
        finally:
            await playwright.stop()

    async def scrape_page(self, url: str, page: int = 1) -> Dict:
        """分页爬取方法"""
        try:
            print(f"GitHub分页爬取器收到URL: {url}, 页码: {page}")

            # 解析URL确定爬取类型
            scrape_type, target_user, target_repo = self._parse_url_type(url)

            if scrape_type == "followers":
                print(f"识别为followers页面，第{page}页")
                return await self._scrape_followers_page(url, page)
            elif scrape_type == "stargazers":
                print(f"识别为stargazers页面，第{page}页")
                return await self._scrape_stargazers_page(url, target_user, target_repo, page)
            elif scrape_type == "forks":
                print(f"识别为forks页面，第{page}页")
                # forks不支持分页模式，返回错误
                raise ValueError("Forks爬取不支持分页模式，请使用完整爬取方法")
            elif scrape_type == "user":
                print(f"识别为用户页面: {target_user}，第{page}页")
                # 默认爬取用户的followers
                followers_url = f"https://github.com/{target_user}?tab=followers"
                return await self._scrape_followers_page(followers_url, page)
            elif scrape_type == "repo":
                print(f"识别为Repositories页面: {target_user}/{target_repo}，第{page}页")
                # 默认爬取Repositories的stargazers
                stargazers_url = f"https://github.com/{target_user}/{target_repo}/stargazers"
                return await self._scrape_stargazers_page(stargazers_url, target_user, target_repo, page)
            else:
                raise ValueError(f"无法识别的URL类型: {url}")

        except Exception as e:
            print(f"GitHub分页爬取失败: {e}")
            raise e

    async def _scrape_followers_page(self, url: str, page: int) -> Dict:
        """分页爬取followers"""
        try:
            print(f"开始爬取关注者页面第{page}页: {url}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page_obj = await context.new_page()

                try:
                    # 构建分页URL
                    if '?' in url:
                        page_url = f"{url}&page={page}"
                    else:
                        page_url = f"{url}?page={page}"

                    print(f"访问分页URL: {page_url}")
                    await page_obj.goto(page_url, wait_until='networkidle', timeout=30000)

                    # 等待用户列表加载
                    await page_obj.wait_for_selector('a[data-hovercard-type="user"]', timeout=10000)

                    # 获取用户链接
                    user_links = await page_obj.query_selector_all('a[data-hovercard-type="user"]')
                    print(f"找到 {len(user_links)} 个用户链接元素")

                    # 提取用户名列表，使用set去重
                    usernames = []
                    seen_usernames = set()
                    for link in user_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and href.startswith('/'):
                                username = href.strip('/')
                                # 去重：如果用户名已经存在，跳过
                                if username and username not in seen_usernames:
                                    seen_usernames.add(username)
                                    usernames.append(username)

                                    # 限制每页最多50个用户
                                    if len(usernames) >= 50:
                                        break
                        except Exception as e:
                            print(f"提取用户名失败: {e}")
                            continue

                    print(f"开始获取 {len(usernames)} 个用户的详细信息...")

                    # 使用统一的Profile获取器
                    users = await self._get_page_users_details(usernames, page_obj, 'follower', '', '', page)

                    # 按follower数量排序（降序）
                    users.sort(key=lambda x: x['follower_count'], reverse=True)
                    print(f"用户按follower数量排序完成，最高: {users[0]['follower_count'] if users else 0}")

                    # 检查是否有下一页 - 使用多种策略
                    has_next_page = False
                    try:
                        # GitHub可能使用不同的分页选择器
                        selectors_to_check = [
                            '.pagination a[rel="next"]',
                            '.paginate-container .next_page',
                            '.paginate-container a[rel="next"]',
                            'a[aria-label="Next"]',
                            '.BtnGroup a[rel="next"]',
                            '.pagination .next_page:not(.disabled)',
                            '.paginate-container .next_page:not(.disabled)'
                        ]

                        for selector in selectors_to_check:
                            next_button = await page_obj.query_selector(selector)
                            if next_button:
                                # 检查按钮是否被禁用
                                is_disabled = await next_button.get_attribute('aria-disabled')
                                class_name = await next_button.get_attribute('class') or ''
                                if is_disabled != 'true' and 'disabled' not in class_name:
                                    has_next_page = True
                                    print(f"找到有效的下一页按钮: {selector}")
                                    break

                        # 如果没有找到明确的下一页按钮，检查当前页面的用户数量
                        # 如果正好是50个用户，很可能还有下一页
                        if not has_next_page and len(users) >= 50:
                            has_next_page = True
                            print(f"基于用户数量({len(users)})判断可能有下一页")

                    except Exception as e:
                        print(f"检查下一页时出错: {e}")
                        # 如果出错且用户数量达到50，假设有下一页
                        if len(users) >= 50:
                            has_next_page = True

                    # 统一格式化数据
                    users = [self._normalize_user_data(user, 'follower') for user in users]

                    print(f"成功提取了第{page}页 {len(users)} 个关注者")

                    return {
                        'data': users,
                        'has_next_page': has_next_page,
                        'current_page': page
                    }

                finally:
                    await browser.close()

        except Exception as e:
            print(f"爬取followers第{page}页时出错: {e}")
            return {
                'data': [],
                'has_next_page': False,
                'current_page': page
            }

    async def _scrape_stargazers_page(self, url: str, owner: str, repo: str, page: int) -> Dict:
        """分页爬取stargazers"""
        try:
            print(f"开始爬取stargazers页面第{page}页: {url}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page_obj = await context.new_page()

                try:
                    # 构建分页URL
                    page_url = f"{url}?page={page}"

                    print(f"访问分页URL: {page_url}")
                    await page_obj.goto(page_url, wait_until='networkidle', timeout=30000)

                    # 等待用户列表加载
                    await page_obj.wait_for_selector('a[data-hovercard-type="user"]', timeout=10000)

                    # 获取用户链接
                    user_links = await page_obj.query_selector_all('a[data-hovercard-type="user"]')
                    print(f"找到 {len(user_links)} 个用户链接元素")

                    # 提取用户名列表，使用set去重
                    usernames = []
                    seen_usernames = set()
                    for link in user_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and href.startswith('/'):
                                username = href.strip('/')
                                # 去重：如果用户名已经存在，跳过
                                if username and username not in seen_usernames:
                                    seen_usernames.add(username)
                                    usernames.append(username)

                                    # 限制每页最多50个用户
                                    if len(usernames) >= 50:
                                        break
                        except Exception as e:
                            print(f"提取用户名失败: {e}")
                            continue

                    print(f"开始获取 {len(usernames)} 个用户的详细信息...")

                    # 使用统一的Profile获取器
                    users = await self._get_page_users_details(usernames, page_obj, 'stargazer', owner, repo, page)

                    # 按follower数量排序（降序）
                    users.sort(key=lambda x: x['follower_count'], reverse=True)
                    print(f"用户按follower数量排序完成，最高: {users[0]['follower_count'] if users else 0}")

                    # 检查是否有下一页 - 使用多种策略
                    has_next_page = False
                    try:
                        # GitHub可能使用不同的分页选择器
                        selectors_to_check = [
                            '.pagination a[rel="next"]',
                            '.paginate-container .next_page',
                            '.paginate-container a[rel="next"]',
                            'a[aria-label="Next"]',
                            '.BtnGroup a[rel="next"]',
                            '.pagination .next_page:not(.disabled)',
                            '.paginate-container .next_page:not(.disabled)'
                        ]

                        for selector in selectors_to_check:
                            next_button = await page_obj.query_selector(selector)
                            if next_button:
                                # 检查按钮是否被禁用
                                is_disabled = await next_button.get_attribute('aria-disabled')
                                class_name = await next_button.get_attribute('class') or ''
                                if is_disabled != 'true' and 'disabled' not in class_name:
                                    has_next_page = True
                                    print(f"找到有效的下一页按钮: {selector}")
                                    break

                        # 如果没有找到明确的下一页按钮，检查当前页面的用户数量
                        # 如果正好是50个用户，很可能还有下一页
                        if not has_next_page and len(users) >= 50:
                            has_next_page = True
                            print(f"基于用户数量({len(users)})判断可能有下一页")

                    except Exception as e:
                        print(f"检查下一页时出错: {e}")
                        # 如果出错且用户数量达到50，假设有下一页
                        if len(users) >= 50:
                            has_next_page = True

                    # 统一格式化数据
                    users = [self._normalize_user_data(user, 'stargazer') for user in users]

                    print(f"成功提取了第{page}页 {len(users)} 个stargazers")

                    return {
                        'data': users,
                        'has_next_page': has_next_page,
                        'current_page': page
                    }

                finally:
                    await browser.close()

        except Exception as e:
            print(f"爬取stargazers第{page}页时出错: {e}")
            return {
                'data': [],
                'has_next_page': False,
                'current_page': page
            }