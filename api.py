from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import requests
import json
import torch
from Murasame.utils import get_config
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.streamers import TextStreamer

api = FastAPI()

# 检测设备优先级：MPS > CUDA > CPU
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"
DEVICE_ID = "0"
CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}" if DEVICE_ID and DEVICE == "cuda" else DEVICE

adapter_path = "./models/Murasame"
max_seq_length = 2048
load_in_4bit = True


def load_model_and_tokenizer():
    print(f"Loading model and tokenizer from adapter path: {adapter_path}")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    model = AutoModelForCausalLM.from_pretrained(
        adapter_path,
        device_map=DEVICE if DEVICE != "cpu" else None,
        torch_dtype=torch.float16 if DEVICE in ["cuda", "mps"] else torch.float32,
        trust_remote_code=True,
        load_in_4bit=load_in_4bit,
    )
    print("Model prepared for inference.")
    return model, tokenizer


def torch_gc():
    if DEVICE == "cuda" and torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    elif DEVICE == "mps" and torch.backends.mps.is_available():
        torch.mps.empty_cache()


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
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Prompt: {prompt}')
    history = json_post_list.get('history')
    history = history + [{'role': 'user', 'content': prompt}]

    text = tokenizer.apply_chat_template(
        history,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)
    print("<<< ", end="", flush=True)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=json_post_list.get('max_new_tokens', 2048),
            temperature=json_post_list.get('temperature', 0.9),
            top_p=json_post_list.get('top_p', 0.95),
            top_k=json_post_list.get('top_k', 20),
            streamer=streamer,
            pad_token_id=tokenizer.eos_token_id
        )

    reply = tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()
    history.append({"role": "assistant", "content": reply})

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        "response": reply,
        "history": history,
        "status": 200,
        "time": time
    }
    print(f'[{time}] Final Response: {reply}')
    return answer


@api.post("/qwen3")
async def create_qwen3_chat(request: Request):
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    role = json_post_list.get('role', 'user')
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Prompt: {prompt}')
    history = json_post_list.get('history')
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
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        "response": final_response,
        "history": history,
        "status": 200,
        "time": time
    }
    print(f'[{time}] Final Response: {final_response}')
    return answer


@api.post("/qwenvl")
async def create_qwenvl_chat(request: Request):
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Prompt: {prompt}')
    history = json_post_list.get('history')

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
            return {
                "response": f"OpenRouter API error: {str(e)}",
                "history": history,
                "status": 500,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
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
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        "response": final_response,
        "history": history,
        "status": 200,
        "time": time
    }
    print(f'[{time}] Final Response: {final_response}')
    return answer


if __name__ == '__main__':
    model, tokenizer = load_model_and_tokenizer()
    streamer = TextStreamer(tokenizer, skip_prompt=True)
    uvicorn.run(api, host='0.0.0.0', port=28565, workers=1)
