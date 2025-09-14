from modelscope import snapshot_download
import os
import json
from rich.console import Console

console = Console()

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

console.log("Downloading Qwen3-14B ...")
snapshot_download(
    'Qwen/Qwen3-14B', local_dir=os.path.join(models_dir, 'Qwen3-14B'))

with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'r', encoding='utf-8') as f:
    adapter_config = json.load(f)
    adapter_config["base_model_name_or_path"] = os.path.abspath(
        os.path.join(models_dir, "Qwen3-14B"))

with open(os.path.join(models_dir, "Murasame", "adapter_config.json"), 'w', encoding='utf-8') as f:
    json.dump(adapter_config, f, ensure_ascii=False, indent=4)
