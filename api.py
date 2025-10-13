# -*- coding: utf-8 -*-
"""
MurasamePet API 服务
提供聊天、问答和视觉理解接口
"""

from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import requests
import json
import torch
import platform
import sys
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from Murasame.utils import get_config

# 确保标准输出使用 UTF-8 编码，防止中文乱码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 检测平台和强制要求
IS_MACOS = platform.system() == "Darwin"

if IS_MACOS:
    # 在 macOS 上强制要求 MLX
    print("🍎 检测到 macOS 系统，初始化 MLX 引擎...")
    try:
        from mlx_lm.utils import load
        from mlx_lm.generate import generate
        ENGINE = "mlx"
        DEVICE = "mlx"  # MLX 会自动使用 Apple Silicon GPU (Metal)
        print("✅ MLX 引擎加载成功 (Apple Silicon GPU 加速)")
    except ImportError as e:
        print(f"❌ 严重错误：macOS 系统需要 MLX 但未找到该库！")
        print(f"导入错误详情: {e}")
        print()
        print("🔍 解决方案：")
        print("1. 安装 MLX: pip install mlx-lm")
        print("2. 或确保您使用的 Python 环境支持 MLX")
        print()
        print("🚨 程序退出：macOS 系统必须使用 MLX 以获得最佳性能")
        exit(1)
else:
    # 在非 macOS 系统上使用 PyTorch
    print("🖥️ 检测到非 macOS 系统，初始化 PyTorch 引擎...")
    ENGINE = "torch"
    # 检测设备优先级：MPS > CUDA > CPU
    if hasattr(torch, "backends") and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        DEVICE = "mps"
        print("✅ PyTorch 引擎加载成功 (使用 MPS 加速)")
    elif torch.cuda.is_available():
        DEVICE = "cuda"
        print("✅ PyTorch 引擎加载成功 (使用 CUDA 加速)")
    else:
        DEVICE = "cpu"
        print("⚠️ PyTorch 引擎加载成功 (使用 CPU，性能可能较慢)")

api = FastAPI()

adapter_path = "./models/Murasame"
max_seq_length = 2048


def load_model_and_tokenizer():
    print(f"📂 模型加载路径: {adapter_path}")
    print(f"⚙️ 推理引擎: {ENGINE} | 计算设备: {DEVICE}")

    if IS_MACOS:
        # 在 macOS 上使用已合并的 MLX 模型
        print("🍎 正在加载合并后的 MLX 模型 (Qwen3-14B-Murasame-Chat-MLX-Int4)...")

        # 检查合并后的模型是否存在
        # 检查 MLX 模型必需文件（配置文件和模型权重）
        required_static_files = ["tokenizer.json", "config.json"]
        missing_files = [f for f in required_static_files if not os.path.exists(os.path.join(adapter_path, f))]

        # 检查模型权重文件（单个 model.safetensors 或分片 model-*.safetensors）
        has_model_weights = False
        try:
            if os.path.exists(os.path.join(adapter_path, "model.safetensors")):
                has_model_weights = True
            else:
                if any(f.startswith("model-") and f.endswith(".safetensors") for f in os.listdir(adapter_path)):
                    has_model_weights = True
        except FileNotFoundError:
             # 如果 adapter_path 不存在，os.listdir 会报错
             pass

        if missing_files or not has_model_weights:
            if not has_model_weights:
                missing_files.append("model.safetensors (或 model-*.safetensors)")
            
            print(f"❌ 严重错误：在 {adapter_path} 中缺少以下 MLX 模型文件: {', '.join(missing_files)}")
            print("💡 请确保已为 macOS 下载了正确的合并模型，而不是 Windows 使用的 LoRA 文件。")
            print("   - 运行 'python download.py' 脚本来获取正确的模型。")
            exit(1)

        try:
            print("🔄 正在从磁盘读取模型文件...")
            # 直接加载合并后的完整模型（不需要单独的 base_model 和 adapter）
            model, tokenizer = load(adapter_path)
            print("✅ 合并 MLX 模型加载成功！")
            print(f"   📍 模型路径: {adapter_path}")
            print(f"   🏷️ 模型类型: Qwen3-14B + Murasame LoRA (已合并, Int4 量化)")
            print(f"   🚀 已启用 Apple Silicon GPU 加速")

        except Exception as e:
            print(f"❌ 严重错误：无法加载合并 MLX 模型！")
            print(f"错误详情: {e}")
            print()
            print("🔍 可能的原因：")
            print("1. 模型文件损坏或不完整")
            print("2. 下载的模型版本与 MLX 不兼容")
            print("3. 缺少必需的 MLX 依赖")
            print()
            print("💡 解决方案：")
            print("1. 重新运行 download.py 确保合并模型正确下载")
            print("2. 检查 MLX 和 mlx-lm 是否正确安装 (pip install mlx-lm)")
            print("3. 验证 ./models/Murasame 目录中的模型文件")
            print()
            print("🚨 程序退出：应用需要合并 MLX 模型才能运行")
            exit(1)
    else:
        # 在非 macOS 系统上使用 PyTorch (保持原有逻辑)
        print("🔧 正在加载 PyTorch LoRA 模型...")

        try:
            print("🔄 正在准备基础模型和 LoRA 适配器...")
            adapter_config_path = os.path.join(adapter_path, "adapter_config.json")
            if not os.path.exists(adapter_config_path):
                print(f"❌ 严重错误：未找到适配器配置文件 {adapter_config_path}")
                print("💡 请运行 download.py 以下载基础模型与 LoRA 适配器")
                exit(1)

            with open(adapter_config_path, "r", encoding="utf-8") as f:
                adapter_config = json.load(f)

            base_model_path = adapter_config.get("base_model_name_or_path")
            if not base_model_path:
                print("❌ 严重错误：适配器配置缺少 base_model_name_or_path")
                exit(1)
            if not os.path.exists(base_model_path):
                print(f"❌ 严重错误：基础模型路径不存在: {base_model_path}")
                print("💡 请确认 Qwen3-14B 模型是否已下载并与 adapter_config.json 中的路径一致")
                exit(1)

            torch_dtype = torch.float16 if DEVICE == "cuda" else torch.float32
            device_map = "auto" if DEVICE == "cuda" else "cpu"
            if DEVICE == "cpu":
                print("⚠️  警告: 在 CPU 上加载 14B 模型需要大量内存 (通常 > 32GB)，请确保可用内存充足。")

            print(f"📦 正在加载基础模型: {base_model_path}")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
                trust_remote_code=True,
            )

            print(f"🎯 正在应用 LoRA 适配器: {adapter_path}")
            model = PeftModel.from_pretrained(
                base_model,
                adapter_path,
                device_map=device_map,
            )

            if DEVICE in ("cpu", "cuda"):
                model = model.to(DEVICE)

            model.eval()

            tokenizer = AutoTokenizer.from_pretrained(
                base_model_path,
                trust_remote_code=True,
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            tokenizer.padding_side = "left"

            print("✅ LoRA 模型加载成功！")
            print(f"   📍 基础模型: {base_model_path}")
            print(f"   📍 适配器: {adapter_path}")
            print(f"   🏷️ 推理设备: {DEVICE}")
        except Exception as e:
            print(f"❌ 严重错误：无法加载 PyTorch LoRA 模型！")
            print(f"错误详情: {e}")
            print()
            print("🔍 可能的原因：")
            print("1. LoRA 文件损坏或不完整")
            print("2. 缺少必需的 PyTorch 依赖")
            print()
            print("💡 解决方案：")
            print("重新运行 download.py 确保 LoRA 文件正确下载")
            print()
            print("🚨 程序退出：应用需要 LoRA 模型才能运行")
            exit(1)

    return model, tokenizer


# 辅助函数：获取当前时间
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 辅助函数：记录请求日志
def log_request(prompt):
    print(f'📥 [{get_current_time()}] 收到用户请求: {prompt}')


# 辅助函数：记录响应日志
def log_response(response):
    print(f'📤 [{get_current_time()}] 生成最终回复: {response}')


# 辅助函数：解析请求
def parse_request(json_post_list):
    prompt = json_post_list.get('prompt')
    history = json_post_list.get('history')
    return prompt, history


# 辅助函数：创建标准响应
def create_response(response_text, history, status=200):
    time = get_current_time()
    return {
        "response": response_text,
        "history": history,
        "status": status,
        "time": time
    }


# MLX 不需要手动垃圾回收


def call_openrouter_api(config, api_key, model, messages, image_url=None, max_tokens=2048):
    """调用 OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://murasame-pet.local",
        "X-Title": "MurasamePet"
    }

    # 处理图像输入 - 按照 OpenRouter 官方文档格式
    if image_url:
        # 如果有图像，将最后一个用户消息修改为包含图像
        for message in reversed(messages):
            if message['role'] == 'user':
                if isinstance(message['content'], str):
                    # 将字符串转换为官方文档要求的数组格式
                    message['content'] = [
                        {"type": "text", "text": message['content']},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                elif isinstance(message['content'], list):
                    # 如果已经是数组格式，直接添加图像
                    message['content'].append({"type": "image_url", "image_url": {"url": image_url}})
                break

    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    # 从配置中获取 OpenRouter 地址，如果不存在则使用默认值
    endpoint_url = config.get('endpoints', {}).get('openrouter', "https://openrouter.ai/api/v1/chat/completions")
    response = requests.post(endpoint_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


@api.post("/chat")
async def create_chat(request: Request):
    json_post_list = await request.json()
    prompt, history = parse_request(json_post_list)
    log_request(prompt)
    history = history + [{'role': 'user', 'content': prompt}]

    # 使用 MLX 进行推理
    print(f"💬 使用 {ENGINE.upper()} 引擎进行推理...")
    print(f"📊 最大生成长度: {json_post_list.get('max_new_tokens', 2048)} tokens")
    
    text = tokenizer.apply_chat_template(
        history,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    print("✅ 聊天模板应用完成")

    max_new_tokens = int(json_post_list.get('max_new_tokens', 2048))
    max_new_tokens = max(1, max_new_tokens)
    temperature = float(json_post_list.get('temperature', 0.7))
    top_p = float(json_post_list.get('top_p', 0.9))
    top_p = max(0.01, min(top_p, 1.0))

    # 推理
    print("🤖 正在生成回复...")
    if ENGINE == "mlx":
        response = generate(
            model, tokenizer,
            prompt=text,
            max_tokens=max_new_tokens,
            verbose=False
        )
        reply = response.strip()
    else:
        encoded = tokenizer(
            text,
            return_tensors="pt",
        )
        encoded = {k: v.to(DEVICE) for k, v in encoded.items()}
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": True,
            "temperature": max(0.01, temperature),
            "top_p": top_p,
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.eos_token_id,
        }
        with torch.no_grad():
            generated = model.generate(
                **encoded,
                **generation_kwargs,
            )
        generated_tokens = generated[0, encoded["input_ids"].shape[-1]:]
        reply = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    print(f"✅ 回复生成完成 (长度: {len(reply)} 字符)")

    history.append({"role": "assistant", "content": reply})

    log_response(reply)
    return create_response(reply, history)


@api.post("/qwen3")
async def create_qwen3_chat(request: Request):
    json_post_list = await request.json()
    prompt, history = parse_request(json_post_list)
    role = json_post_list.get('role', 'user')
    log_request(prompt)
    if prompt != "":
        history = history + [{'role': role, 'content': prompt}]

    config = get_config()
    api_key = config.get('openrouter_api_key', '')
    endpoint_url = config.get('server', {}).get('qwen3', '')

    # 仅当 endpoint 指向 openrouter 且 API key 存在时，才使用 OpenRouter
    if "openrouter.ai" in endpoint_url and api_key.strip():
        print(f"🌐 检测到 qwen3 endpoint 指向 OpenRouter，使用 API Key 进行调用...")
        try:
            result = call_openrouter_api(
                config,
                api_key,
                "qwen/qwen3-235b-a22b",
                history,
                max_tokens=4096
            )
            final_response = result['choices'][0]['message']['content']
            print("✅ OpenRouter API 调用成功")
        except Exception as e:
            error_msg = f"OpenRouter API 错误: {str(e)}"
            print(f"❌ {error_msg}")
            log_response(error_msg)
            return create_response(error_msg, history, status=500)
    else:
        # 使用本地端点 (Ollama 或其他)
        print(f"🏠 使用本地端点 ({endpoint_url}) 进行调用...")
        response = None
        try:
            response = requests.post(
                f"{endpoint_url}/api/chat",
                json={"model": "qwen3:14b", "messages": history,
                      "stream": False, "options": {"keep_alive": -1}},
            )
            response.raise_for_status() # 检查 HTTP 错误
            final_response = response.json()['message']['content']
            print("✅ 本地 API 调用成功")
        except requests.exceptions.RequestException as e:
            print(f"❌ 调用本地 API 时出错: {e}")
            if response is not None:
                print(f"响应状态: {response.status_code}")
                print(f"响应内容: {response.text[:500]}")
            raise

    history = history + [{'role': 'assistant', 'content': final_response}]
    log_response(final_response)
    return create_response(final_response, history)


@api.post("/qwenvl")
async def create_qwenvl_chat(request: Request):
    json_post_list = await request.json()
    prompt, history = parse_request(json_post_list)
    log_request(prompt)

    if "image" in json_post_list:
        image_url = json_post_list.get('image')
        print(f"🖼️ 检测到图像输入: {image_url[:100]}...")
        history = history + [{'role': 'user', 'content': prompt, 'images': [image_url]}]
    else:
        print("📝 纯文本模式（无图像输入）")
        history = history + [{'role': 'user', 'content': prompt}]

    config = get_config()
    api_key = config.get('openrouter_api_key', '')
    endpoint_url = config.get('server', {}).get('qwenvl', '')
    image_url_for_api = json_post_list.get('image') if "image" in json_post_list else None

    # 仅当 endpoint 指向 openrouter 且 API key 存在时，才使用 OpenRouter
    if "openrouter.ai" in endpoint_url and api_key.strip():
        print(f"🌐 检测到 qwenvl endpoint 指向 OpenRouter，使用 API Key 进行调用...")
        try:
            result = call_openrouter_api(
                config,
                api_key,
                "qwen/qwen-2.5-vl-7b-instruct",
                history,
                image_url=image_url_for_api
            )
            final_response = result['choices'][0]['message']['content']
            print("✅ OpenRouter 视觉 API 调用成功")
        except Exception as e:
            error_msg = f"OpenRouter API 错误: {str(e)}"
            print(f"❌ {error_msg}")
            log_response(error_msg)
            return create_response(error_msg, history, status=500)
    else:
        # 使用本地端点 (Ollama 或其他)
        print(f"🏠 使用本地端点 ({endpoint_url}) 进行调用...")
        try:
            response = requests.post(
                f"{endpoint_url}/api/chat",
                json={"model": "qwen2.5vl:7b", "messages": history,
                      "stream": False, "options": {"keep_alive": -1}},
            )
            response.raise_for_status()
            final_response = response.json()['message']['content']
            print("✅ 本地视觉 API 调用成功")
        except requests.exceptions.RequestException as e:
            print(f"❌ 调用本地视觉 API 时出错: {e}")
            raise

    history = history + [{'role': 'assistant', 'content': final_response}]
    log_response(final_response)
    return create_response(final_response, history)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MurasamePet API 服务启动中...")
    print("=" * 60)
    
    model, tokenizer = load_model_and_tokenizer()
    
    print("=" * 60)
    print("✅ 模型加载完成，启动 FastAPI 服务器...")
    print(f"🌐 服务地址: http://0.0.0.0:28565")
    print(f"📡 可用端点:")
    print(f"   - POST /chat    (主对话接口 - Murasame)")
    print(f"   - POST /qwen3   (通用问答接口 - Qwen3)")
    print(f"   - POST /qwenvl  (视觉理解接口 - Qwen-VL)")
    print("=" * 60)
    
    uvicorn.run(api, host='0.0.0.0', port=28565, workers=1)
