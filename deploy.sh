#!/bin/bash
# 命理运势系统 - 腾讯云部署脚本
# 服务器: Ubuntu, 2核2G
# IP: 82.157.186.52

set -e

echo "=========================================="
echo "  命理运势系统 - 部署脚本"
echo "=========================================="

# 配置
APP_DIR="/opt/fortune"
PYTHON_CMD="python3"
NODE_VERSION="22"

# 1. 系统依赖
echo "[1/7] 安装系统依赖..."
apt update -y
apt install -y python3 python3-pip python3-venv nginx curl git

# 2. 安装 Node.js (如未安装)
if ! command -v node &> /dev/null; then
    echo "[2/7] 安装 Node.js ${NODE_VERSION}..."
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt install -y nodejs
else
    echo "[2/7] Node.js 已安装: $(node -v)"
fi

# 3. 创建应用目录
echo "[3/7] 创建应用目录..."
mkdir -p $APP_DIR

# 4. 克隆代码（如目录为空）
if [ ! -f "$APP_DIR/server/requirements.txt" ]; then
    echo "[4/7] 克隆代码..."
    rm -rf $APP_DIR/*
    git clone --depth 1 https://gitclone.com/github.com/shihanye0/fortune.git $APP_DIR
else
    echo "[4/7] 更新代码..."
    cd $APP_DIR
    git pull origin main
fi

cd $APP_DIR

# 5. 后端依赖
echo "[5/7] 安装后端依赖..."
cd $APP_DIR/server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
deactivate

# 6. 前端构建
echo "[6/7] 构建前端..."
cd $APP_DIR/client
npm install
npm run build

# 7. 配置
echo "[7/7] 配置服务..."

# 后端 .env（如不存在则从部署环境创建）
if [ ! -f "$APP_DIR/server/.env" ]; then
    : "${DEEPSEEK_API_KEY:?请在部署前设置 DEEPSEEK_API_KEY}"
    : "${SMTP_USER:?请在部署前设置 SMTP_USER}"
    : "${SMTP_PASSWORD:?请在部署前设置 SMTP_PASSWORD}"
    : "${INTERNAL_API_KEY:?请在部署前设置与 GitHub Actions Secret 一致的 INTERNAL_API_KEY}"

    DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
    LLM_CREDENTIAL_ENCRYPTION_KEY="${LLM_CREDENTIAL_ENCRYPTION_KEY:-$(python3 -c 'import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')}"
    JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"

    cat > "$APP_DIR/server/.env" << ENVEOF
# 数据库
DATABASE_URL=sqlite:///./fortune.db

# LLM API（默认 DeepSeek）
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL=$DEEPSEEK_BASE_URL
LLM_ALLOWED_HOSTS=api.deepseek.com,api.xiaomimimo.com
LLM_CREDENTIAL_ENCRYPTION_KEY=$LLM_CREDENTIAL_ENCRYPTION_KEY

# QQ 邮箱 SMTP
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD

# JWT
JWT_SECRET=$JWT_SECRET
JWT_EXPIRE_HOURS=24
INTERNAL_API_KEY=$INTERNAL_API_KEY

# 应用
APP_PORT=8080
APP_ENV=production
ENVEOF
    chmod 600 "$APP_DIR/server/.env"
    echo "  已根据部署环境创建 server/.env"
fi

# Nginx 配置
cat > /etc/nginx/sites-available/fortune << 'NGXEOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/fortune/client/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # Swagger 文档
    location /docs {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8080;
    }
}
NGXEOF

ln -sf /etc/nginx/sites-available/fortune /etc/nginx/sites-enabled/fortune
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Systemd 服务
cat > /etc/systemd/system/fortune.service << SVCEOF
[Unit]
Description=Fortune API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fortune/server
ExecStart=/opt/fortune/server/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable fortune
systemctl restart fortune

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "  访问地址: http://82.157.186.52"
echo "  API 文档: http://82.157.186.52/docs"
echo ""
echo "  管理命令:"
echo "    systemctl status fortune    # 查看状态"
echo "    systemctl restart fortune   # 重启后端"
echo "    journalctl -u fortune -f    # 查看日志"
echo "    cd /opt/fortune && git pull # 更新代码"
echo ""
