from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import requests
import json
import torch
import platform
import sys
import os
from Murasame.utils import get_config

# 检测平台和强制要求
IS_MACOS = platform.system() == "Darwin"

if IS_MACOS:
    # 在 macOS 上强制要求 MLX
    try:
        from mlx_lm.utils import load
        from mlx_lm.generate import generate
        ENGINE = "mlx"
        DEVICE = "mlx"  # MLX 会自动使用 Apple Silicon GPU (Metal)
        print("Using MLX engine on macOS (Apple Silicon optimized)")
    except ImportError as e:
        print(f"❌ CRITICAL ERROR: MLX is required on macOS but not available!")
        print(f"Import error: {e}")
        print()
        print("🔍 SOLUTION:")
        print("1. Install MLX: pip install mlx-lm")
        print("2. Or ensure you're using Python with MLX support")
        print()
        print("🚨 EXITING: macOS requires MLX for optimal performance.")
        exit(1)
else:
    # 在非 macOS 系统上使用 PyTorch
    ENGINE = "torch"
    # 检测设备优先级：MPS > CUDA > CPU
    if torch.backends.mps.is_available():
        DEVICE = "mps"
    elif torch.cuda.is_available():
        DEVICE = "cuda"
    else:
        DEVICE = "cpu"
    print(f"Using PyTorch engine with device: {DEVICE}")

api = FastAPI()

adapter_path = "./models/Murasame"
max_seq_length = 2048


def load_model_and_tokenizer():
    print(f"Loading model and tokenizer from adapter path: {adapter_path}")
    print(f"Engine: {ENGINE}, Device: {DEVICE}")

    if IS_MACOS:
        # 在 macOS 上使用 MLX + LoRA 的组合方式
        print("🍎 Loading MLX model with LoRA adapter...")

        # 基底模型路径 (Qwen3-14B-MLX)
        base_model_path = "./models/Qwen3-14B-MLX"

        # 检查基底模型是否存在
        if not os.path.exists(base_model_path):
            print(f"❌ CRITICAL ERROR: Base model not found at {base_model_path}")
            print("Please run download.py first to download the required models.")
            exit(1)

        # 检查 LoRA 适配器是否存在
        if not os.path.exists(adapter_path):
            print(f"❌ CRITICAL ERROR: LoRA adapter not found at {adapter_path}")
            print("Please run download.py first to download the LoRA adapter.")
            exit(1)

        try:
            # 使用 MLX 加载基底模型和 LoRA 适配器
            model, tokenizer = load(base_model_path, adapter_path=adapter_path)
            print("✅ MLX model with LoRA adapter loaded successfully!")
            print(f"   - Base model: {base_model_path}")
            print(f"   - LoRA adapter: {adapter_path}")

        except Exception as e:
            print(f"❌ CRITICAL ERROR: Failed to load MLX model with LoRA!")
            print(f"Error details: {e}")
            print()
            print("🔍 POSSIBLE CAUSES:")
            print("1. Base model files are corrupted or incomplete")
            print("2. LoRA adapter files are incompatible with MLX")
            print("3. Missing required MLX dependencies")
            print()
            print("💡 SOLUTION:")
            print("1. Re-run download.py to ensure all models are properly downloaded")
            print("2. Check that MLX and mlx-lm are properly installed")
            print("3. Verify the LoRA adapter is compatible with the base model")
            print()
            print("🚨 EXITING: This application requires working MLX + LoRA setup.")
            exit(1)
    else:
        # 在非 macOS 系统上使用 PyTorch (保持原有逻辑)
        print("Loading PyTorch model with LoRA...")

        try:
            model, tokenizer = load(adapter_path)
            print("LoRA model loaded successfully with PyTorch.")
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Failed to load LoRA model with PyTorch!")
            print(f"Error details: {e}")
            print()
            print("🔍 POSSIBLE CAUSES:")
            print("1. LoRA files are corrupted or incomplete")
            print("2. Missing required PyTorch dependencies")
            print()
            print("💡 SOLUTION:")
            print("Re-run download.py to ensure LoRA files are properly downloaded")
            print()
            print("🚨 EXITING: This application requires LoRA to function properly.")
            exit(1)

    return model, tokenizer


# 辅助函数：获取当前时间
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 辅助函数：记录请求日志
def log_request(prompt):
    print(f'[{get_current_time()}] Prompt: {prompt}')


# 辅助函数：记录响应日志
def log_response(response):
    print(f'[{get_current_time()}] Final Response: {response}')


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


def should_use_openrouter(config):
    """检测是否应该使用 OpenRouter"""
    api_key = config.get('openrouter_api_key', '')
    return bool(api_key.strip())  # 有非空值就使用 OpenRouter


def call_openrouter_api(api_key, model, messages, image_url=None):
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
        "max_tokens": 2048
    }

    # 硬编码 OpenRouter 地址
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()


@api.post("/chat")
async def create_chat(request: Request):
    json_post_list = await request.json()
    prompt, history = parse_request(json_post_list)
    log_request(prompt)
    history = history + [{'role': 'user', 'content': prompt}]

    # 使用 MLX 进行推理
    print("Using MLX for inference...")
    text = tokenizer.apply_chat_template(
        history,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    # MLX LM 推理
    response = generate(
        model, tokenizer,
        prompt=text,
        max_tokens=json_post_list.get('max_new_tokens', 2048),
        temp=json_post_list.get('temperature', 0.9),
        top_p=json_post_list.get('top_p', 0.95),
        verbose=False
    )
    reply = response.strip()

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

    # Qwen3-14b 强制使用本地 LoRA 以保持角色特色
    config = get_config()
    endpoint_url = config['endpoints']['ollama']
    response = requests.post(
        f"{endpoint_url}/api/chat",
        json={"model": "qwen3:14b", "messages": history,
              "stream": False, "options": {"keep_alive": -1}},
    )
    final_response = response.json()['message']['content']

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
        history = history + \
            [{'role': 'user', 'content': prompt, 'images': [image_url]}]
    else:
        history = history + [{'role': 'user', 'content': prompt}]

    config = get_config()

    if should_use_openrouter(config):
        # 使用 OpenRouter，支持图像输入
        api_key = config.get('openrouter_api_key', '')
        image_url = json_post_list.get('image') if "image" in json_post_list else None

        try:
            result = call_openrouter_api(
                api_key,
                "qwen/qwen-2.5-vl-7b-instruct",  # OpenRouter 视觉模型名称
                history,
                image_url=image_url
            )
            final_response = result['choices'][0]['message']['content']
        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            log_response(error_msg)
            return create_response(error_msg, history, status=500)
    else:
        # 使用本地 Ollama API
        endpoint_url = config['endpoints']['ollama']
        response = requests.post(
            f"{endpoint_url}/api/chat",
            json={"model": "qwen2.5vl:7b", "messages": history,
                  "stream": False, "options": {"keep_alive": -1}},
        )
        final_response = response.json()['message']['content']

    history = history + [{'role': 'assistant', 'content': final_response}]
    log_response(final_response)
    return create_response(final_response, history)


if __name__ == '__main__':
    model, tokenizer = load_model_and_tokenizer()
    # MLX 不使用 TextStreamer
    uvicorn.run(api, host='0.0.0.0', port=28565, workers=1)
