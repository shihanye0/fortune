#!/bin/bash
# 命理运势系统 - 更新部署脚本
# 用于代码更新后重新部署

set -e

APP_DIR="/opt/fortune"

echo "=========================================="
echo "  更新部署"
echo "=========================================="

cd $APP_DIR

# 1. 拉取最新代码（国内镜像加速）
echo "[1/3] 拉取最新代码..."
git fetch --unshallow origin 2>/dev/null || true
git pull origin main

# 2. 更新后端依赖（如有新包）
echo "[2/3] 更新后端..."
cd $APP_DIR/server
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
deactivate

# 3. 重新构建前端 + 重启服务
echo "[3/3] 重新构建前端并重启..."
cd $APP_DIR/client
npm install -q
npm run build

systemctl restart fortune

echo ""
echo "  更新完成！"
echo "  访问: http://82.157.186.52"
echo "  日志: journalctl -u fortune -f"
echo ""
