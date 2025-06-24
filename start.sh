#!/bin/bash

# FollowNet 启动脚本

echo "🚀 正在启动 FollowNet..."

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 请在项目根目录下运行此脚本"
    exit 1
fi

# 启动后端服务
echo "📚 启动后端服务..."
cd backend
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到 requirements.txt 文件"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
playwright install

# 后台启动后端
echo "🔄 启动 FastAPI 服务器..."
python main.py &
BACKEND_PID=$!

cd ../frontend

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端
echo "🎨 启动 Next.js 开发服务器..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ FollowNet 已启动！"
echo "🔗 前端: http://localhost:3000"
echo "🔗 后端: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待中断信号
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait 