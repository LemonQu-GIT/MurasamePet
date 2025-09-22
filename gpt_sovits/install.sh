#!/bin/bash

# cd into GPT-SoVITS Base Path
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

# shellcheck disable=SC2317
on_error() {
    local lineno="$1"
    local cmd="$2"
    local code="$3"

    echo -e "${ERROR}${BOLD}Command \"${cmd}\" Failed${RESET} at ${BOLD}Line ${lineno}${RESET} with Exit Code ${BOLD}${code}${RESET}"
    echo -e "${ERROR}${BOLD}Call Stack:${RESET}"
    for ((i = ${#FUNCNAME[@]} - 1; i >= 1; i--)); do
        echo -e "  in ${BOLD}${FUNCNAME[i]}()${RESET} at ${BASH_SOURCE[i]}:${BOLD}${BASH_LINENO[i - 1]}${RESET}"
    done
    exit "$code"
}

# Removed conda and pip3 install functions

run_wget_quiet() {
    if wget --tries=25 --wait=5 --read-timeout=40 --show-progress "$@" 2>&1; then
        tput cuu1 && tput el
    else
        echo -e "${ERROR} Wget failed"
        exit 1
    fi
}

# Removed conda check for uv-based dependency management

USE_CUDA=false
USE_ROCM=false
USE_CPU=false
WORKFLOW=${WORKFLOW:-"false"}

USE_HF=false
USE_HF_MIRROR=false
USE_MODELSCOPE=false
DOWNLOAD_UVR5=false

print_help() {
    echo "Usage: bash install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --device   CU126|CU128|ROCM|MPS|CPU    Specify the Device (REQUIRED)"
    echo "  --source   HF|HF-Mirror|ModelScope     Specify the model source (REQUIRED)"
    echo "  --download-uvr5                        Enable downloading the UVR5 model"
    echo "  -h, --help                             Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  bash install.sh --device CU128 --source HF --download-uvr5"
    echo "  bash install.sh --device MPS --source ModelScope"
}

# Show help if no arguments provided
if [[ $# -eq 0 ]]; then
    print_help
    exit 0
fi

# Parse arguments
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
            echo -e "${ERROR}Error: Invalid Download Source: $2"
            echo -e "${ERROR}Choose From: [HF, HF-Mirror, ModelScope]"
            exit 1
            ;;
        esac
        shift 2
        ;;
    --device)
        case "$2" in
        CU126)
            CUDA=126
            USE_CUDA=true
            ;;
        CU128)
            CUDA=128
            USE_CUDA=true
            ;;
        ROCM)
            USE_ROCM=true
            ;;
        MPS)
            USE_CPU=true
            ;;
        CPU)
            USE_CPU=true
            ;;
        *)
            echo -e "${ERROR}Error: Invalid Device: $2"
            echo -e "${ERROR}Choose From: [CU126, CU128, ROCM, MPS, CPU]"
            exit 1
            ;;
        esac
        shift 2
        ;;
    --download-uvr5)
        DOWNLOAD_UVR5=true
        shift
        ;;
    -h | --help)
        print_help
        exit 0
        ;;
    *)
        echo -e "${ERROR}Unknown Argument: $1"
        echo ""
        print_help
        exit 1
        ;;
    esac
done

if ! $USE_CUDA && ! $USE_ROCM && ! $USE_CPU; then
    echo -e "${ERROR}Error: Device is REQUIRED"
    echo ""
    print_help
    exit 1
fi

if ! $USE_HF && ! $USE_HF_MIRROR && ! $USE_MODELSCOPE; then
    echo -e "${ERROR}Error: Download Source is REQUIRED"
    echo ""
    print_help
    exit 1
fi

# Architecture check removed - assuming compatible with uv

# System dependencies - assuming managed via uv or system package manager
echo -e "${INFO}Detected system: $(uname -s) $(uname -r) $(uname -m)"
if [ "$(uname)" = "Darwin" ]; then
    if ! command -v brew &>/dev/null; then
        echo -e "${WARNING}Homebrew not found. Please install FFmpeg, wget, and OpenSSL manually: brew install ffmpeg cmake make unzip wget openssl"
        echo -e "${WARNING}Also set environment variables for OpenSSL: export LDFLAGS=\"-L/opt/homebrew/opt/openssl/lib\" && export CPPFLAGS=\"-I/opt/homebrew/opt/openssl/include\""
    else
        echo -e "${INFO}Installing FFmpeg, CMake, Make, Unzip, Wget, OpenSSL via Homebrew..."
        brew install ffmpeg cmake make unzip wget openssl
        echo -e "${SUCCESS}System dependencies installed"
        echo -e "${INFO}Setting OpenSSL environment variables for urllib3 v2 compatibility..."

        # Set environment variables for current session
        export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
        export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"

        # Make environment variables permanent by adding to ~/.zshrc
        ZSHRC_FILE="$HOME/.zshrc"
        LDFLAGS_LINE='export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"'
        CPPFLAGS_LINE='export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"'

        if ! grep -q "$LDFLAGS_LINE" "$ZSHRC_FILE" 2>/dev/null; then
            echo "$LDFLAGS_LINE" >> "$ZSHRC_FILE"
            echo -e "${INFO}Added LDFLAGS to ~/.zshrc"
        else
            echo -e "${INFO}LDFLAGS already in ~/.zshrc"
        fi

        if ! grep -q "$CPPFLAGS_LINE" "$ZSHRC_FILE" 2>/dev/null; then
            echo "$CPPFLAGS_LINE" >> "$ZSHRC_FILE"
            echo -e "${INFO}Added CPPFLAGS to ~/.zshrc"
        else
            echo -e "${INFO}CPPFLAGS already in ~/.zshrc"
        fi

        echo -e "${SUCCESS}OpenSSL environment variables configured permanently"
    fi
else
    echo -e "${WARNING}Please ensure FFmpeg, CMake, Make, Unzip, Wget, and OpenSSL are installed on your system"
fi

if [ "$USE_HF" = "true" ]; then
    echo -e "${INFO}Download Model From HuggingFace"
    PRETRINED_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
    G2PW_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
    UVR5_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/uvr5_weights.zip"
    NLTK_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
    PYOPENJTALK_URL="https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
elif [ "$USE_HF_MIRROR" = "true" ]; then
    echo -e "${INFO}Download Model From HuggingFace-Mirror"
    PRETRINED_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
    G2PW_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
    UVR5_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/uvr5_weights.zip"
    NLTK_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
    PYOPENJTALK_URL="https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
elif [ "$USE_MODELSCOPE" = "true" ]; then
    echo -e "${INFO}Download Model From ModelScope"
    PRETRINED_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/pretrained_models.zip"
    G2PW_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/G2PWModel.zip"
    UVR5_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/uvr5_weights.zip"
    NLTK_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/nltk_data.zip"
    PYOPENJTALK_URL="https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/open_jtalk_dic_utf_8-1.11.tar.gz"
fi

if [ ! -d "gpt_sovits/pretrained_models/sv" ]; then
    echo -e "${INFO}Downloading Pretrained Models..."
    rm -rf pretrained_models.zip
    run_wget_quiet "$PRETRINED_URL"

    unzip -q -o pretrained_models.zip -d gpt_sovits
    rm -rf pretrained_models.zip
    echo -e "${SUCCESS}Pretrained Models Downloaded"
else
    echo -e "${INFO}Pretrained Model Exists"
    echo -e "${INFO}Skip Downloading Pretrained Models"
fi

if [ ! -d "gpt_sovits/text/G2PWModel" ]; then
    echo -e "${INFO}Downloading G2PWModel.."
    rm -rf G2PWModel.zip
    run_wget_quiet "$G2PW_URL"

    unzip -q -o G2PWModel.zip -d gpt_sovits/text
    rm -rf G2PWModel.zip
    echo -e "${SUCCESS}G2PWModel Downloaded"
else
    echo -e "${INFO}G2PWModel Exists"
    echo -e "${INFO}Skip Downloading G2PWModel"
fi

if [ "$DOWNLOAD_UVR5" = "true" ]; then
    if find -L "tools/uvr5/uvr5_weights" -mindepth 1 ! -name '.gitignore' | grep -q .; then
        echo -e "${INFO}UVR5 Models Exists"
        echo -e "${INFO}Skip Downloading UVR5 Models"
    else
        echo -e "${INFO}Downloading UVR5 Models..."
        rm -rf uvr5_weights.zip
        run_wget_quiet "$UVR5_URL"

        unzip -q -o uvr5_weights.zip -d tools/uvr5
        rm -rf uvr5_weights.zip
        echo -e "${SUCCESS}UVR5 Models Downloaded"
    fi
fi

# Hardware checks removed - assuming MPS/CPU for macOS

# PyTorch installation removed - managed via uv/pyproject.toml

# Python dependencies removed - managed via uv/pyproject.toml

PY_PREFIX=$(python3 -c "import sys; print(sys.prefix)")
PYOPENJTALK_PREFIX=$(python3 -c "import os, pyopenjtalk; print(os.path.dirname(pyopenjtalk.__file__))")

if [ ! -d "$PY_PREFIX/nltk_data" ]; then
    echo -e "${INFO}Downloading NLTK Data..."
    rm -rf nltk_data.zip
    run_wget_quiet "$NLTK_URL" -O nltk_data.zip
    unzip -q -o nltk_data -d "$PY_PREFIX"
    rm -rf nltk_data.zip
    echo -e "${SUCCESS}NLTK Data Downloaded"
else
    echo -e "${INFO}NLTK Data Exists"
    echo -e "${INFO}Skip Downloading NLTK Data"
fi

if [ ! -d "$PYOPENJTALK_PREFIX/open_jtalk_dic_utf_8-1.11" ]; then
    echo -e "${INFO}Downloading Open JTalk Dict..."
    rm -rf open_jtalk_dic_utf_8-1.11.tar.gz
    run_wget_quiet "$PYOPENJTALK_URL" -O open_jtalk_dic_utf_8-1.11.tar.gz
    tar -xzf open_jtalk_dic_utf_8-1.11.tar.gz -C "$PYOPENJTALK_PREFIX"
    rm -rf open_jtalk_dic_utf_8-1.11.tar.gz
    echo -e "${SUCCESS}Open JTalk Dic Downloaded"
else
    echo -e "${INFO}Open JTalk Dic Exists"
    echo -e "${INFO}Skip Downloading Open JTalk Dic"
fi

# ROCm WSL fix removed

echo -e "${SUCCESS}Installation Completed"
