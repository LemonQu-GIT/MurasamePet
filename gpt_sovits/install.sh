#!/bin/bash

# GPT-SoVITS 预训练模型下载脚本 (精简版 - 作为子项目使用)
# 此脚本仅下载 TTS 推理所需的预训练模型，不安装依赖
# 依赖管理由根项目的 pyproject.toml/uv 处理

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR" || exit 1

RESET="\033[0m"
BOLD="\033[1m"
ERROR="\033[1;31m[ERROR]: $RESET"
WARNING="\033[1;33m[WARNING]: $RESET"
INFO="\033[1;32m[INFO]: $RESET"
SUCCESS="\033[1;34m[SUCCESS]: $RESET"

set -eE
set -o errtrace

trap 'on_error $LINENO "$BASH_COMMAND" $?' ERR

on_error() {
    local lineno="$1"
    local cmd="$2"
    local code="$3"
    echo -e "${ERROR}${BOLD}Command \"${cmd}\" Failed${RESET} at ${BOLD}Line ${lineno}${RESET} with Exit Code ${BOLD}${code}${RESET}"
    exit "$code"
}

run_wget_quiet() {
    if wget --tries=25 --wait=5 --read-timeout=40 -q --show-progress "$@" 2>&1; then
        tput cuu1 && tput el
    else
        echo -e "${ERROR} Wget failed"
        exit 1
    fi
}

USE_HF=false
USE_HF_MIRROR=false
USE_MODELSCOPE=false

print_help() {
    echo "用法: bash install.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --source   HF|HF-Mirror|ModelScope     指定模型下载源 (必需)"
    echo "  -h, --help                             显示此帮助信息"
    echo ""
    echo "说明:"
    echo "  此脚本仅下载 GPT-SoVITS TTS 推理所需的预训练模型"
    echo "  Python 依赖由根项目的 pyproject.toml 管理"
    echo ""
    echo "示例:"
    echo "  bash install.sh --source HF"
    echo "  bash install.sh --source ModelScope"
    echo ""
    echo "安装项目依赖:"
    echo "  cd .. && uv sync"
}

# 如果没有参数，显示帮助
if [[ $# -eq 0 ]]; then
    print_help
    exit 0
fi

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
    --source)
        case "$2" in
        HF)
            USE_HF=true
            ;;
        HF-Mirror)
            USE_HF_MIRROR=true
            ;;
        ModelScope)
            USE_MODELSCOPE=true
            ;;
        *)
            echo -e "${ERROR}错误: 无效的下载源: $2"
            echo -e "${ERROR}请选择: [HF, HF-Mirror, ModelScope]"
            exit 1
            ;;
        esac
        shift 2
        ;;
    -h | --help)
        print_help
        exit 0
        ;;
    *)
        echo -e "${ERROR}未知参数: $1"
        echo ""
        print_help
        exit 1
        ;;
    esac
done

# 验证必需参数
if ! $USE_HF && ! $USE_HF_MIRROR && ! $USE_MODELSCOPE; then
    echo -e "${ERROR}错误: 必须指定下载源 (--source)"
    echo ""
    print_help
    exit 1
fi

# 检查 wget 是否可用
if ! command -v wget &>/dev/null; then
    echo -e "${ERROR}错误: 未找到 wget 命令"
    echo -e "${INFO}请先安装 wget:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${INFO}  brew install wget"
    else
        echo -e "${INFO}  sudo apt-get install wget  # Debian/Ubuntu"
        echo -e "${INFO}  sudo yum install wget      # CentOS/RHEL"
    fi
    exit 1
fi

# 检查 unzip 是否可用
if ! command -v unzip &>/dev/null; then
    echo -e "${ERROR}错误: 未找到 unzip 命令"
    echo -e "${INFO}请先安装 unzip"
    exit 1
fi

# 设置下载源 URL
if [ "$USE_HF" = "true" ]; then
    echo -e "${INFO}从 HuggingFace 下载模型"
    PRETRINED_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
    G2PW_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
    NLTK_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
    PYOPENJTALK_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
elif [ "$USE_HF_MIRROR" = "true" ]; then
    echo -e "${INFO}从 HuggingFace-Mirror 下载模型"
    PRETRINED_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
    G2PW_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
    NLTK_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
    PYOPENJTALK_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
elif [ "$USE_MODELSCOPE" = "true" ]; then
    echo -e "${INFO}从 ModelScope 下载模型"
    PRETRINED_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/pretrained_models.zip"
    G2PW_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/G2PWModel.zip"
    NLTK_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/nltk_data.zip"
    PYOPENJTALK_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/open_jtalk_dic_utf_8-1.11.tar.gz"
fi

# 下载预训练模型
if [ ! -d "GPT_SoVITS/pretrained_models/sv" ]; then
    echo -e "${INFO}下载预训练模型..."
    rm -rf pretrained_models.zip
    run_wget_quiet "$PRETRINED_URL"
    
    echo -e "${INFO}解压预训练模型..."
    unzip -q -o pretrained_models.zip -d GPT_SoVITS
    rm -rf pretrained_models.zip
    echo -e "${SUCCESS}预训练模型下载完成"
else
    echo -e "${INFO}预训练模型已存在"
    echo -e "${INFO}跳过下载预训练模型"
fi

# 下载 G2PWModel
if [ ! -d "GPT_SoVITS/text/G2PWModel" ]; then
    echo -e "${INFO}下载 G2PWModel..."
    rm -rf G2PWModel.zip
    run_wget_quiet "$G2PW_URL"
    
    echo -e "${INFO}解压 G2PWModel..."
    unzip -q -o G2PWModel.zip -d GPT_SoVITS/text
    rm -rf G2PWModel.zip
    echo -e "${SUCCESS}G2PWModel 下载完成"
else
    echo -e "${INFO}G2PWModel 已存在"
    echo -e "${INFO}跳过下载 G2PWModel"
fi

# 下载 NLTK 数据
echo -e "${INFO}下载 NLTK 数据..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo -e "${WARNING}未找到 Python，跳过 NLTK 数据下载"
    echo -e "${WARNING}请在安装依赖后手动运行:"
    echo -e "${WARNING}  python -c 'import nltk; nltk.download(\"punkt\"); nltk.download(\"averaged_perceptron_tagger\")'"
    PYTHON_CMD=""
fi

if [ -n "$PYTHON_CMD" ]; then
    PY_PREFIX=$($PYTHON_CMD -c "import sys; print(sys.prefix)" 2>/dev/null || echo "")
    if [ -n "$PY_PREFIX" ] && [ ! -d "$PY_PREFIX/nltk_data/tokenizers/punkt" ]; then
        rm -rf nltk_data.zip
        run_wget_quiet "$NLTK_URL" -O nltk_data.zip
        
        echo -e "${INFO}解压 NLTK 数据..."
        unzip -q -o nltk_data.zip -d "$PY_PREFIX"
        rm -rf nltk_data.zip
        echo -e "${SUCCESS}NLTK 数据下载完成"
    else
        if [ -z "$PY_PREFIX" ]; then
            echo -e "${WARNING}Python 环境未就绪，跳过 NLTK 数据下载"
        else
            echo -e "${INFO}NLTK 数据已存在"
            echo -e "${INFO}跳过下载 NLTK 数据"
        fi
    fi
fi

# 下载 Open JTalk 字典
echo -e "${INFO}下载 Open JTalk 字典..."
if [ -n "$PYTHON_CMD" ]; then
    PYOPENJTALK_PREFIX=$($PYTHON_CMD -c "import os, pyopenjtalk; print(os.path.dirname(pyopenjtalk.__file__))" 2>/dev/null || echo "")
    if [ -n "$PYOPENJTALK_PREFIX" ] && [ ! -d "$PYOPENJTALK_PREFIX/open_jtalk_dic_utf_8-1.11" ]; then
        rm -rf open_jtalk_dic_utf_8-1.11.tar.gz
        run_wget_quiet "$PYOPENJTALK_URL" -O open_jtalk_dic_utf_8-1.11.tar.gz
        
        echo -e "${INFO}解压 Open JTalk 字典..."
        tar -xzf open_jtalk_dic_utf_8-1.11.tar.gz -C "$PYOPENJTALK_PREFIX"
        rm -rf open_jtalk_dic_utf_8-1.11.tar.gz
        echo -e "${SUCCESS}Open JTalk 字典下载完成"
    else
        if [ -z "$PYOPENJTALK_PREFIX" ]; then
            echo -e "${WARNING}pyopenjtalk 未安装，跳过 Open JTalk 字典下载"
            echo -e "${WARNING}请在安装依赖后重新运行此脚本"
        else
            echo -e "${INFO}Open JTalk 字典已存在"
            echo -e "${INFO}跳过下载 Open JTalk 字典"
        fi
    fi
fi

echo ""
echo -e "${SUCCESS}================================"
echo -e "${SUCCESS}所有模型下载完成！"
echo -e "${SUCCESS}================================"
echo ""
echo -e "${INFO}接下来的步骤:"
echo -e "${INFO}  1. 返回项目根目录: cd .."
echo -e "${INFO}  2. 安装 Python 依赖: uv sync"
echo -e "${INFO}  3. 启动 TTS 服务: python gpt_sovits/api_v2.py"
echo ""
