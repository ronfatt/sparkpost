#!/bin/bash

# 获取当前脚本所在绝对目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "⚡ 启动 SPARK ONE • Telegram 多语言广播与市场控制台"
echo "=========================================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 正在创建 Python 虚拟环境..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    echo "📥 正在安装所需依赖..."
    ./venv/bin/pip install -r requirements.txt
fi

echo "🚀 启动 Web 控制面板: http://127.0.0.1:8000"
echo "💡 提示: 请在浏览器中打开上面的地址进行管理与广播"
echo "=========================================================="

./venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
