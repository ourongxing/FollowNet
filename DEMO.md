# FollowNet 演示文档

## 🎯 项目概述

FollowNet 是一个全栈Web应用，可以爬取社交媒体平台的关注者数据并导出为CSV文件。

## 🏗️ 技术栈

### 后端 (FastAPI)
- **FastAPI**: 现代高性能Web框架
- **Playwright**: 浏览器自动化和网页爬取
- **Pydantic**: 数据验证和序列化
- **Uvicorn**: ASGI服务器

### 前端 (Next.js)
- **Next.js 14**: React全栈框架
- **TypeScript**: 类型安全的JavaScript
- **Tailwind CSS**: 现代化CSS框架
- **Lucide React**: 美观的图标库
- **Axios**: HTTP客户端

## 🔄 数据流程

1. **用户输入**: 用户在前端输入要爬取的URL
2. **平台检测**: 系统自动识别平台类型 (GitHub/Twitter/Product Hunt)
3. **后端处理**: FastAPI接收请求，调用对应的爬取器
4. **数据爬取**: Playwright启动浏览器，爬取目标数据
5. **数据处理**: 提取结构化数据并生成CSV文件
6. **文件下载**: 前端提供下载链接，用户获取CSV文件

## 🎨 用户界面特性

### 主页设计
- **渐变背景**: 现代化的视觉效果
- **平台图标**: 自动显示检测到的平台图标
- **响应式设计**: 适配桌面和移动设备
- **实时反馈**: 加载状态和结果展示

### 交互体验
- **智能检测**: 输入URL时自动检测平台
- **加载动画**: 爬取过程中显示加载指示器
- **成功提示**: 爬取完成后显示统计信息
- **错误处理**: 友好的错误提示和重试选项

## 🛠️ 核心功能实现

### 1. 平台检测算法
```python
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
    else:
        raise ValueError(f"不支持的平台: {domain}")
```

### 2. 基础爬取器架构
```python
class BaseScraper(ABC):
    """基础爬取器抽象类"""
    
    @abstractmethod
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """爬取数据的抽象方法"""
        pass
    
    async def save_to_csv(self, data: List[Dict[str, Any]], filepath: str):
        """将数据保存为CSV文件"""
        # 实现CSV导出逻辑
```

### 3. 前端状态管理
```typescript
const [url, setUrl] = useState('')
const [isLoading, setIsLoading] = useState(false)
const [result, setResult] = useState<ScrapeResult | null>(null)
const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null)
```

## 📊 支持的数据字段

### GitHub数据
- `username`: 用户名
- `display_name`: 显示名称
- `bio`: 个人简介
- `avatar_url`: 头像URL
- `profile_url`: 个人主页URL
- `type`: 数据类型 (stargazer/follower)

### Twitter数据
- `username`: 用户名
- `display_name`: 显示名称
- `bio`: 个人简介
- `avatar_url`: 头像URL
- `profile_url`: 个人主页URL
- `stats`: 统计信息
- `type`: 数据类型 (follower/following)

### Product Hunt数据
- `username`: 用户名
- `display_name`: 显示名称
- `bio`: 个人简介
- `avatar_url`: 头像URL
- `profile_url`: 个人主页URL
- `vote_time`: 投票时间
- `type`: 数据类型 (voter/user_profile)

## 🔧 API端点详情

### POST /api/scrape
**功能**: 爬取指定URL的数据

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/microsoft/vscode/stargazers"}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "成功爬取 50 条数据",
  "download_url": "/api/download/abc123-def456",
  "platform": "github",
  "total_extracted": 50
}
```

### GET /api/download/{file_id}
**功能**: 下载生成的CSV文件

**请求示例**:
```bash
curl -O "http://localhost:8000/api/download/abc123-def456"
```

## 🚀 部署建议

### 开发环境
1. 使用提供的 `start.sh` 脚本一键启动
2. 前端: `http://localhost:3000`
3. 后端: `http://localhost:8000`

### 生产环境
1. **后端**: 使用Gunicorn + Uvicorn部署FastAPI
2. **前端**: 使用Next.js构建静态文件，部署到CDN
3. **数据库**: 可选择添加Redis缓存提升性能
4. **监控**: 添加日志和监控系统

## ⚡ 性能优化

### 爬取优化
- **并发控制**: 合理设置浏览器实例数量
- **请求延迟**: 避免过频繁的请求
- **内存管理**: 及时清理浏览器资源

### 前端优化
- **代码分割**: Next.js自动代码分割
- **图片优化**: 使用Next.js Image组件
- **缓存策略**: 合理设置API响应缓存

## 🔒 安全考虑

### 数据隐私
- 只爬取公开可见的数据
- 生成的CSV文件定期清理
- 不存储用户输入的URL

### 防护措施
- 输入验证和清理
- 请求频率限制
- CORS策略配置

## 📈 扩展可能

### 新平台支持
- LinkedIn
- Instagram
- YouTube
- TikTok

### 功能增强
- 数据过滤和排序
- 多种导出格式 (JSON, Excel)
- 批量URL处理
- 实时数据同步

## 🎯 使用场景

1. **市场研究**: 分析竞争对手的关注者群体
2. **社交分析**: 研究用户行为和兴趣偏好
3. **营销推广**: 寻找潜在客户和影响者
4. **学术研究**: 收集社交网络数据进行分析 