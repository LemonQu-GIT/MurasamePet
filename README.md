# MurasamePet

https://www.bilibili.com/video/BV1vjeGzfE1w

## 部署 

### 安装包

```shell
pip install -r ./requirements.txt
```

### 安装 Ollama （非必须）

若没有云端可用的 OpenAI 可用（Qwen3:14b, Qwen2.5vl:7b)，那么这步是必须的（在本地运行所有模型）

在 https://ollama.com/download 下载 Ollama 并安装

```shell
ollama pull qwen3:14b
ollama pull qwen2.5vl:7b
```

等待下载完毕

### 下载微调模型（之后哪天放假我看看怎么合并模型）

```shell
python ./download.py
```

### 部署 GPT-SoVITS

https://github.com/RVC-Boss/GPT-SoVITS

运行 ./models/Murasame_SoVITS 中的两个模型

```shell
python api_v2.py
```

注意，`api_v2.py` 为 `GPT-SoVITS` Repository 中的文件 (https://github.com/RVC-Boss/GPT-SoVITS/blob/main/api_v2.py)

### 运行本地 API

```shell
python ./api.py
```

### 运行主程序

```shell
python ./pet.py
```

### 配置 OpenRouter（可选）

如果你想使用 OpenRouter 作为云端 API 提供商：

1. 在 https://openrouter.ai/ 注册并获取 API key
2. 修改 `./config.json` 中的配置：

```json
{
    "openrouter_api_key": "sk-or-v1-xxxxxxxxxxxxx",  // 填入你的 API key
    "endpoints": {
        //...(此部分修改在后文有讲)
    },
    // ... 其他配置
}
```

### macOS 权限配置

如果使用视觉功能，需要配置屏幕录制权限：

1. 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制
2. 点击 "+" 添加 Terminal 或 Python
3. 重启应用程序

权限不足时会看到相关错误提示，按照此教程给予权限后重启api服务即可

3. 重启 `api.py` 服务

### 注

根据你的部署情况，可能需要修改 `./config.json` 中的以下地址：

- **Ollama 地址** (`ollama`)：如果 Ollama 服务不在 `http://localhost:11434` 运行
- **GPT-SoVITS 地址** (`murasame-sovits`)：确认语音合成的 API 地址，通常是 `http://localhost:9880/tts`
- **本地 API 地址** (`qwen3`, `qwenvl`, `murasame`)：如果 `api.py` 不在 `http://localhost:28565` 运行

其他配置通常无需修改。

## 使用（？）

点击丛雨下半部分可以输入内容，长按鼠标按住丛雨的头部并左右移动可以摸头……
