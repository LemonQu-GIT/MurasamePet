# -*- coding: utf-8 -*-
"""
MurasamePet 模型下载脚本
支持 macOS 和其他平台的自动模型下载
"""

from modelscope import snapshot_download
import os
import json
import platform
import subprocess
import sys
from rich.console import Console

# 确保标准输出使用 UTF-8 编码，防止中文乱码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

console = Console()

def is_macos_with_apple_silicon():
    """检测是否为 macOS + Apple Silicon"""
    if platform.system() != "Darwin":
        return False

    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                              capture_output=True, text=True)
        cpu_brand = result.stdout.strip()
        # 只检查 'Apple' 即可，覆盖所有 Apple Silicon 芯片 (M1, M2, M3, M4, A系列等)
        return 'Apple' in cpu_brand
    except:
        return False

models_dir = './models'
if not os.path.exists(models_dir):
    os.mkdir(models_dir)

console.log("📦 开始下载模型...")

console.log("🎙️ 正在下载 Murasame SoVITS 语音合成模型...")
snapshot_download(
    'LemonQu/Murasame_SoVITS', local_dir=os.path.join(models_dir, 'Murasame_SoVITS'))

# 根据平台下载不同的模型
if is_macos_with_apple_silicon():
    console.log("🍎 检测到 Apple Silicon，下载合并后的 Qwen3-14B-Murasame-Chat-MLX-Int4 模型...")
    # macOS 下载已经合并 LoRA 的完整模型
    merged_model_id = 'yuemingruoan/Qwen3-14B-Murasame-Chat-MLX-Int4'
    merged_model_dir = 'Murasame'
    snapshot_download(merged_model_id, local_dir=os.path.join(models_dir, merged_model_dir))
    console.log(f"✅ 合并模型下载完成，保存至 {merged_model_dir}")
else:
    # 非 macOS 平台：下载标准版本的 LoRA 和基础模型
    console.log("📥 下载标准版本 Murasame LoRA...")
    murasame_model_id = 'LemonQu/Murasame'
    murasame_dir_name = 'Murasame'
    
    console.log("🔧 正在下载 Murasame LoRA 适配器...")
    snapshot_download(
        murasame_model_id, local_dir=os.path.join(models_dir, murasame_dir_name))
    
    console.log("📥 正在下载标准版本 Qwen3-14B 基础模型...")
    qwen_model_id = 'Qwen/Qwen3-14B'
    qwen_dir_name = 'Qwen3-14B'
    qwen_path = os.path.join(models_dir, qwen_dir_name)
    snapshot_download(qwen_model_id, local_dir=qwen_path)
    
    # 更新 LoRA 配置
    console.log("⚙️ 正在更新 LoRA 配置文件...")
    with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'r', encoding='utf-8') as f:
        adapter_config = json.load(f)
    
    adapter_config["base_model_name_or_path"] = os.path.abspath(qwen_path)
    adapter_config["framework"] = "transformers"
    
    with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'w', encoding='utf-8') as f:
        json.dump(adapter_config, f, ensure_ascii=False, indent=4)
    
    console.log("✅ LoRA 配置文件更新完成")

console.log("✅ 所有模型下载完成！")
