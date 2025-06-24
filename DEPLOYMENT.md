# FollowNet 部署指南

## 🚀 部署架构

- **前端**: Cloudflare Pages (Static hosting)
- **后端**: Railway (Supports Playwright + FastAPI)

## 📋 部署前准备

### 环境要求
- Node.js 18+ (前端)
- Python 3.11+ (后端)
- Git 账户
- Cloudflare 账户
- Railway 账户

## 🔧 后端部署 (Railway)

### 1. 准备Railway部署

1. 登录 [Railway](https://railway.app)
2. 创建新项目
3. 连接你的GitHubRepositories

### 2. 配置环境变量

在Railway项目设置中添加以下环境变量：

```bash
PYTHON_VERSION=3.11
PORT=8000
PLAYWRIGHT_BROWSERS_PATH=/opt/railway/bin
```

### 3. 部署配置

Railway会自动检测到Python项目并安装依赖。确保 `railway.json` 文件在根目录：

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt && playwright install",
    "watchPatterns": ["backend/**"]
  },
  "deploy": {
    "startCommand": "cd backend && python main.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 4. 获取部署URL

部署成功后，Railway会提供一个URL，类似：
```
https://your-app-name.railway.app
```

记录这个URL，前端需要用到。

## 🌐 前端部署 (Cloudflare Pages)

### 1. 更新API配置

在 `frontend/next.config.js` 中更新生产环境API URL：

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: process.env.NODE_ENV === 'production' 
        ? 'https://your-railway-app.railway.app/api/:path*'  // 替换为你的Railway URL
        : 'http://localhost:8000/api/:path*',
    },
  ];
},
```

### 2. 部署到Cloudflare Pages

#### 方法1: 通过Dashboard

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 "Pages" 
3. 点击 "Create a project"
4. 连接你的GitHubRepositories
5. 配置构建设置：
   - **Framework preset**: Next.js
   - **Build command**: `cd frontend && npm run build`
   - **Build output directory**: `frontend/out`
   - **Root directory**: `/`

#### 方法2: 通过Wrangler CLI

```bash
# 安装Wrangler
npm install -g wrangler

# 登录Cloudflare
wrangler login

# 部署
cd frontend
npm run build
wrangler pages publish out --project-name follownet
```

### 3. 环境变量配置

在Cloudflare Pages设置中添加：

```bash
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
```

### 4. 自定义域名 (可选)

1. 在Cloudflare Pages项目中点击 "Custom domains"
2. 添加你的域名
3. 配置DNS记录

## 🔄 CORS配置

确保后端正确配置CORS以允许前端访问：

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 开发环境
        "https://your-cloudflare-pages.pages.dev",  # Cloudflare Pages
        "https://your-custom-domain.com"  # 自定义域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ⚙️ 环境特定配置

### 开发环境
```bash
# 前端
cd frontend
npm run dev

# 后端
cd backend
python main.py
```

### 生产环境

前端会自动部署到Cloudflare Pages，后端部署到Railway。

## 🛠️ 部署验证

### 1. 检查后端健康状态

访问: `https://your-railway-app.railway.app/`

应该返回:
```json
{"message": "FollowNet API 正在运行"}
```

### 2. 检查前端

访问你的Cloudflare Pages URL，确保：
- 页面正常加载
- 平台检测功能正常
- API调用成功

### 3. 测试完整流程

1. 输入一个GitHub URL
2. 检查平台是否被正确检测
3. 点击Submit按钮
4. 验证数据爬取和CSV下载功能

## 🚨 常见问题

### Railway部署问题

**Q: Playwright安装失败**
```bash
# 在Railway中，确保使用正确的构建命令
playwright install --with-deps chromium
```

**Q: 内存不足**
- 升级Railway计划
- 优化爬取器的内存使用

### Cloudflare Pages问题

**Q: API调用失败**
- 检查CORS配置
- 验证API URL是否正确
- 检查_headers文件配置

**Q: 构建失败**
```bash
# 确保package.json中有正确的脚本
"scripts": {
  "build": "next build",
  "export": "next export"
}
```

## 📊 性能优化

### 后端优化
- 启用Redis缓存
- 配置CDN
- 优化数据库查询

### 前端优化
- 启用Cloudflare缓存
- 压缩静态资源
- 使用Cloudflare Images优化

## 🔒 安全考虑

### API安全
- 实施速率限制
- 添加API密钥验证
- 配置防火墙规则

### 前端安全
- 启用HSTS
- 配置CSP头部
- 使用HTTPS

## 📈 监控和日志

### Railway监控
- 使用Railway内置监控
- 配置错误警报
- 查看应用日志

### Cloudflare分析
- 启用Web Analytics
- 监控性能指标
- 查看访问统计

## 🔄 CI/CD流程

### 自动部署

1. **代码推送** → GitHub
2. **Railway自动构建** → 后端部署
3. **Cloudflare Pages自动构建** → 前端部署

### 分支策略

- `main` → 生产环境
- `staging` → 测试环境
- `dev` → 开发环境

## 📞 支持

如果遇到部署问题：

1. 检查构建日志
2. 验证环境变量配置
3. 确认依赖版本兼容性
4. 查看官方文档：
   - [Railway Docs](https://docs.railway.app)
   - [Cloudflare Pages Docs](https://developers.cloudflare.com/pages)

---

🎉 部署完成！你的FollowNet应用现在可以在全球范围内访问了。 