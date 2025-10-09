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
    if torch.backends.mps.is_available():
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
        if not os.path.exists(adapter_path):
            print(f"❌ 严重错误：未找到合并模型 {adapter_path}")
            print("💡 请先运行 download.py 下载合并模型")
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
            print("🔄 正在从磁盘读取模型文件...")
            model, tokenizer = load(adapter_path)
            print("✅ LoRA 模型加载成功！")
            print(f"   📍 模型路径: {adapter_path}")
            print(f"   🏷️ 模型类型: PyTorch LoRA")
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


def should_use_openrouter(config):
    """检测是否应该使用 OpenRouter"""
    api_key = config.get('openrouter_api_key', '')
    return bool(api_key.strip())  # 有非空值就使用 OpenRouter


def call_openrouter_api(api_key, model, messages, image_url=None, max_tokens=2048):
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
    print("💬 使用 MLX 引擎进行推理...")
    print(f"📊 最大生成长度: {json_post_list.get('max_new_tokens', 2048)} tokens")
    
    text = tokenizer.apply_chat_template(
        history,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    print("✅ 聊天模板应用完成")

    # MLX LM 推理
    print("🤖 正在生成回复...")
    response = generate(
        model, tokenizer,
        prompt=text,
        max_tokens=json_post_list.get('max_new_tokens', 2048),
        verbose=False
    )
    reply = response.strip()
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

    if should_use_openrouter(config):
        # 优先使用 OpenRouter 的 qwen3-235b 模型
        print("🌐 使用 OpenRouter API (qwen3-235b-a22b 模型)...")
        api_key = config.get('openrouter_api_key', '')
        try:
            print("🔄 正在调用 OpenRouter API...")
            result = call_openrouter_api(
                api_key,
                "qwen/qwen3-235b-a22b",  # 用户指定的模型
                history,
                max_tokens=4096  # 辅助功能可能需要更多 tokens
            )
            final_response = result['choices'][0]['message']['content']
            print("✅ OpenRouter API 调用成功")
        except Exception as e:
            print(f"⚠️ OpenRouter API 调用失败，回退到 Ollama: {e}")
            # 回退到 Ollama
            print("🔄 正在切换到本地 Ollama 服务...")
            endpoint_url = config['endpoints']['ollama']
            response = None
            try:
                print(f"📡 正在调用 Ollama API ({endpoint_url})...")
                response = requests.post(
                    f"{endpoint_url}/api/chat",
                    json={"model": "qwen3:14b", "messages": history,
                          "stream": False, "options": {"keep_alive": -1}},
                )
                print(f"📊 Ollama 响应状态: {response.status_code}")
                print(f"📋 Ollama 响应头: {response.headers}")
                print(f"📄 Ollama 响应内容 (前500字符): {response.text[:500]}")
                final_response = response.json()['message']['content']
                print("✅ Ollama API 调用成功")
            except requests.exceptions.JSONDecodeError as e:
                print(f"❌ Ollama JSON 解析错误: {e}")
                if response:
                    print(f"响应状态: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    raise Exception(f"Ollama API 返回了无效的 JSON。状态: {response.status_code}, 响应: {response.text[:500]}")
                else:
                    raise Exception("Ollama API 返回了无效的 JSON。未收到响应。")
            except Exception as e:
                print(f"❌ 调用 Ollama API 时出错: {e}")
                raise
    else:
        # 使用 Ollama
        print("🏠 使用本地 Ollama API (qwen3:14b 模型)...")
        endpoint_url = config['endpoints']['ollama']
        response = None
        try:
            print(f"📡 正在调用 Ollama API ({endpoint_url})...")
            response = requests.post(
                f"{endpoint_url}/api/chat",
                json={"model": "qwen3:14b", "messages": history,
                      "stream": False, "options": {"keep_alive": -1}},
            )
            print(f"📊 Ollama 响应状态: {response.status_code}")
            print(f"📋 Ollama 响应头: {response.headers}")
            print(f"📄 Ollama 响应内容 (前500字符): {response.text[:500]}")
            final_response = response.json()['message']['content']
            print("✅ Ollama API 调用成功")
        except requests.exceptions.JSONDecodeError as e:
            print(f"❌ Ollama JSON 解析错误: {e}")
            if response:
                print(f"响应状态: {response.status_code}")
                print(f"响应内容: {response.text}")
                raise Exception(f"Ollama API 返回了无效的 JSON。状态: {response.status_code}, 响应: {response.text[:500]}")
            else:
                raise Exception("Ollama API 返回了无效的 JSON。未收到响应。")
        except Exception as e:
            print(f"❌ 调用 Ollama API 时出错: {e}")
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
        history = history + \
            [{'role': 'user', 'content': prompt, 'images': [image_url]}]
    else:
        print("📝 纯文本模式（无图像输入）")
        history = history + [{'role': 'user', 'content': prompt}]

    config = get_config()

    if should_use_openrouter(config):
        # 使用 OpenRouter，支持图像输入
        print("🌐 使用 OpenRouter API (qwen-2.5-vl-7b-instruct 视觉模型)...")
        api_key = config.get('openrouter_api_key', '')
        image_url = json_post_list.get('image') if "image" in json_post_list else None

        try:
            print("🔄 正在调用 OpenRouter 视觉 API...")
            result = call_openrouter_api(
                api_key,
                "qwen/qwen-2.5-vl-7b-instruct",  # OpenRouter 视觉模型名称
                history,
                image_url=image_url
            )
            final_response = result['choices'][0]['message']['content']
            print("✅ OpenRouter 视觉 API 调用成功")
        except Exception as e:
            error_msg = f"OpenRouter API 错误: {str(e)}"
            print(f"❌ {error_msg}")
            log_response(error_msg)
            return create_response(error_msg, history, status=500)
    else:
        # 使用本地 Ollama API
        print("🏠 使用本地 Ollama API (qwen2.5vl:7b 视觉模型)...")
        endpoint_url = config['endpoints']['ollama']
        print(f"📡 正在调用 Ollama 视觉 API ({endpoint_url})...")
        response = requests.post(
            f"{endpoint_url}/api/chat",
            json={"model": "qwen2.5vl:7b", "messages": history,
                  "stream": False, "options": {"keep_alive": -1}},
        )
        final_response = response.json()['message']['content']
        print("✅ Ollama 视觉 API 调用成功")

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
