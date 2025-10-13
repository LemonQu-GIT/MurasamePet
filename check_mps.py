#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一个用于检测当前 Python 环境中的 PyTorch 是否支持 Apple Silicon (MPS) 加速的脚本。
"""

import torch
import platform

def check_mps_support():
    """
    执行 MPS 支持的检查并打印结果。
    """
    print("=" * 50)
    print("🚀 PyTorch MPS 支持情况检查工具 🚀")
    print("=" * 50)
    print(f"🐍 Python 版本: {platform.python_version()}")
    print(f"📦 PyTorch 版本: {torch.__version__}")
    print("-" * 50)

    if platform.system() != "Darwin":
        print("❌ 本脚本仅适用于 macOS 系统。")
        print("   当前系统:", platform.system())
        return

    print("✅ 操作系统为 macOS。")

    # 检查 PyTorch 是否在编译时就包含了 MPS 支持
    is_built = torch.backends.mps.is_built()
    if is_built:
        print("✅ 当前 PyTorch 版本已编译 MPS 支持。")
    else:
        print("❌ 当前 PyTorch 版本未编译 MPS 支持。")
        print("   请确保您安装了适用于 arm64 (Apple Silicon) 的 PyTorch。")
        print("   💡 解决方案: 在项目根目录运行 'uv sync' 以根据 pyproject.toml 安装正确版本。")
        return

    # 检查 MPS 是否在当前环境下可用
    is_available = torch.backends.mps.is_available()
    if not is_available:
        print("❌ MPS 设备当前不可用。")
        print("   这可能是因为您的 macOS 版本过低 (需要 12.3 或更高版本)。")
        return
    
    print("✅ MPS 设备当前可用。")
    print("-" * 50)
    print("⚙️ 正在尝试在 MPS 设备上执行一个简单的计算...")

    try:
        # 定义 MPS 设备
        device = torch.device("mps")

        # 创建一个张量并将其移动到 MPS 设备
        x = torch.tensor([1.0, 2.0, 3.0], device=device)
        
        # 在 MPS 设备上执行运算
        y = x * 2
        
        print("   - 在 MPS 上创建张量: 成功")
        print(f"   - 原始张量: {x.cpu().numpy()} (在 {x.device} 上)")
        print(f"   - 计算结果: {y.cpu().numpy()} (在 {y.device} 上)")
        print("\n🎉 恭喜！您的 PyTorch 环境已正确配置并支持 MPS 加速！")

    except Exception as e:
        print("\n❌ 在 MPS 设备上执行计算时出错！")
        print(f"   错误详情: {e}")
        print("   这表明尽管 MPS 显示可用，但实际运行时存在问题。")

    finally:
        print("=" * 50)


if __name__ == "__main__":
    check_mps_support()