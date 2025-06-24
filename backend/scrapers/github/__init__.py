"""
GitHub爬取器包
包含两阶段爬取功能：
1. get_followers_list.py - 批量获取用户名列表（支持分页）
2. scrape_profiles.py - 逐个获取用户详细信息
"""

from .get_followers_list import GitHubFollowersListScraper
from .scrape_profiles import GitHubProfileScraper

__all__ = ['GitHubFollowersListScraper', 'GitHubProfileScraper'] 