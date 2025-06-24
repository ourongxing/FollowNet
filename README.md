# FollowNet

一个强大的社交媒体关注者数据导出工具，支持 GitHub、Twitter、Product Hunt 等平台的数据爬取和导出。

## 🎯 功能特性

- **多平台支持**: 支持 GitHub、Twitter/X、Product Hunt
- **智能检测**: 自动识别输入的URL对应的平台
- **数据导出**: 将爬取的数据导出为CSV格式
- **现代界面**: 基于 Next.js 和 Tailwind CSS 的现代化UI
- **高性能爬取**: 使用 Playwright 进行高效的数据爬取

## 🚀 支持的平台和数据

### GitHub
- Repositories的星标者信息
- 用户的关注者信息
- 提取用户名、显示名称、头像、简介等

### Twitter/X
- 用户的关注者列表
- 用户关注的人列表
- 提取用户名、显示名称、简介、统计信息等

### Product Hunt
- 产品的投票者信息
- 用户的活动数据
- 提取用户名、简介、投票时间等

## 📁 项目结构

```
FollowNet/
├── frontend/              # Next.js 前端应用
│   ├── app/
│   │   ├── page.tsx      # 主页面
│   │   ├── layout.tsx    # 布局组件
│   │   └── globals.css   # 全局样式
│   ├── package.json
│   └── next.config.js
├── backend/               # FastAPI 后端应用
│   ├── scrapers/          # 爬取器模块
│   │   ├── base.py       # 基础爬取器类
│   │   ├── github.py     # GitHub 爬取器
│   │   ├── twitter.py    # Twitter 爬取器
│   │   └── producthunt.py # Product Hunt 爬取器
│   ├── main.py           # FastAPI 主应用
│   └── requirements.txt   # Python 依赖
└── README.md
```

## 🛠️ 安装和运行

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 安装Python依赖：
```bash
pip install -r requirements.txt
```

3. 安装Playwright浏览器：
```bash
playwright install
```

4. 启动后端服务：
```bash
python main.py
```

后端服务将在 `http://localhost:8000` 运行。

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装Node.js依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 `http://localhost:3000` 运行。

## 📖 使用方法

1. 在浏览器中打开 `http://localhost:3000`
2. 在输入框中粘贴要爬取的URL，例如：
   - GitHubRepositories: `https://github.com/owner/repo`
   - GitHub用户: `https://github.com/username`
   - Twitter用户: `https://twitter.com/username`
   - Product Hunt产品: `https://www.producthunt.com/posts/product-name`
3. 系统会自动检测平台类型
4. 点击"开始爬取"按钮
5. 等待爬取完成后，点击"下载CSV文件"获取数据

## 🔧 API接口

### POST /api/scrape
爬取指定URL的数据

**请求体:**
```json
{
  "url": "https://github.com/username/repo"
}
```

**响应:**
```json
{
  "success": true,
  "message": "成功爬取 50 条数据",
  "download_url": "/api/download/uuid",
  "platform": "github",
  "total_extracted": 50
}
```

### GET /api/download/{file_id}
下载生成的CSV文件

## ⚠️ 注意事项

1. **合规使用**: 请确保您的爬取行为符合目标网站的使用条款
2. **频率限制**: 避免过于频繁的请求，以免被平台限制
3. **数据隐私**: 只爬取公开可见的数据
4. **服务条款**: 使用前请仔细阅读各平台的服务条款

## 🤝 贡献

欢迎提交问题和功能请求！如果您想贡献代码，请：

1. Fork 这个项目
2. 创建您的功能分支
3. 提交您的更改
4. 推送到分支
5. 开启一个 Pull Request

## 📄 许可证

这个项目基于 MIT 许可证开源。详见 LICENSE 文件。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Next.js](https://nextjs.org/) - React全栈框架
- [Playwright](https://playwright.dev/) - 现代化的Web自动化库
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的CSS框架
