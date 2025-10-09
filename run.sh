#!/bin/bash
# -*- coding: utf-8 -*-
#
# MurasamePet 启动脚本
# 确保中文日志正常显示，无乱码

# 设置 UTF-8 编码环境
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

# 颜色定义
RESET="\033[0m"
BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"

echo -e "${BLUE}${BOLD}============================================================${RESET}"
echo -e "${GREEN}🚀 MurasamePet 启动脚本${RESET}"
echo -e "${BLUE}${BOLD}============================================================${RESET}"
echo -e "${YELLOW}📝 编码设置: UTF-8${RESET}"
echo -e "${YELLOW}🌍 语言环境: ${LANG}${RESET}"
echo -e "${BLUE}${BOLD}============================================================${RESET}"
echo ""

# 启动 API 服务
python api.py

