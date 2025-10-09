#!/bin/bash
# GPT-SoVITS TTS 快速启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "🚀 GPT-SoVITS TTS 服务启动脚本"
echo "========================================"

# 检查配置文件
CONFIG_FILE="gpt_sovits/configs/tts_infer.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 配置文件不存在: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}💡 请先运行 install.sh 安装依赖和下载模型${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 配置文件已找到${NC}"

# 检查预训练模型
PRETRAINED_DIR="gpt_sovits/GPT_SoVITS/pretrained_models"
if [ ! -d "$PRETRAINED_DIR" ] || [ -z "$(ls -A $PRETRAINED_DIR)" ]; then
    echo -e "${RED}❌ 预训练模型未下载${NC}"
    echo -e "${YELLOW}💡 请先运行 install.sh 下载模型${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 预训练模型已下载${NC}"

# 设置参数
HOST="${TTS_HOST:-127.0.0.1}"
PORT="${TTS_PORT:-9880}"

echo ""
echo "📋 启动配置:"
echo "   - 地址: $HOST"
echo "   - 端口: $PORT"
echo "   - 配置: $CONFIG_FILE"
echo ""

# 启动服务
echo -e "${BLUE}🔄 正在启动 TTS 服务...${NC}"
echo ""

python gpt_sovits/api_v2.py \
    -a "$HOST" \
    -p "$PORT" \
    -c "$CONFIG_FILE"

# 如果服务异常退出
echo ""
echo -e "${RED}❌ TTS 服务已停止${NC}"

