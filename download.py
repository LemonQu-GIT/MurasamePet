#TODO:为LoRA也进行分系统的适配
from modelscope import snapshot_download
import os
import json
import platform
import subprocess
from rich.console import Console

console = Console()

def is_macos_with_apple_silicon():
    """检测是否为 macOS + Apple Silicon"""
    if platform.system() != "Darwin":
        return False

    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                              capture_output=True, text=True)
        cpu_brand = result.stdout.strip()
        return 'Apple' in cpu_brand or 'M1' in cpu_brand or 'M2' in cpu_brand or 'M3' in cpu_brand
    except:
        return False

models_dir = './models'
if not os.path.exists(models_dir):
    os.mkdir(models_dir)

console.log("Downloading models...")

console.log("Downloading Murasame LoRA ...")
snapshot_download(
    'LemonQu/Murasame', local_dir=os.path.join(models_dir, 'Murasame'))

console.log("Downloading Murasame SoVITS ...")
snapshot_download(
    'LemonQu/Murasame_SoVITS', local_dir=os.path.join(models_dir, 'Murasame_SoVITS'))

# 智能下载 Qwen 模型
if is_macos_with_apple_silicon():
    console.log("🍎 检测到 Apple Silicon，使用 MLX 版本的 Qwen3-14B...")
    qwen_model_id = 'Qwen/Qwen3-14B-MLX-4bit'
    qwen_dir_name = 'Qwen3-14B-MLX'
    use_mlx = True
else:
    console.log("📥 下载标准版本 Qwen3-14B...")
    qwen_model_id = 'Qwen/Qwen3-14B'
    qwen_dir_name = 'Qwen3-14B'
    use_mlx = False

qwen_path = os.path.join(models_dir, qwen_dir_name)
snapshot_download(qwen_model_id, local_dir=qwen_path)

# 更新 LoRA 配置
with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'r', encoding='utf-8') as f:
    adapter_config = json.load(f)

adapter_config["base_model_name_or_path"] = os.path.abspath(qwen_path)
adapter_config["framework"] = "mlx" if use_mlx else "transformers"

with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'w', encoding='utf-8') as f:
    json.dump(adapter_config, f, ensure_ascii=False, indent=4)

console.log("✅ 所有模型下载完成！")
