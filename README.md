# MurasamePet

一个基于AI的桌面宠物项目，使用GPT-SoVITS进行语音合成，支持对话和交互。

**视频演示**: https://www.bilibili.com/video/BV1vjeGzfE1w

## 🚀 快速开始

### 一键运行（推荐）

```bash
python run_project.py
```

该脚本会自动：
- ✅ 检测系统环境（macOS/Windows）
- ✅ 检测Python 3.10是否存在
- ✅ 安装必要的依赖
- ✅ 下载预训练模型
- ✅ 启动所有服务

### 系统要求

- **Python**: 3.10（必须）
- **macOS**: Apple Silicon (M1/M2/M3/M4) 推荐，Intel不支持
- **Windows**: 需要NVIDIA显卡和CUDA
- **内存**: 建议16GB以上

> 💡 **提示**: 运行 `run_project.py` 本身可以使用任何Python版本，脚本会自动检测系统中是否存在Python 3.10。服务将通过`uv`使用Python 3.10运行。详见 [PYTHON_VERSION_DETECTION.md](PYTHON_VERSION_DETECTION.md)

## 📦 手动部署

如果你想手动控制部署过程：

### 1. 安装依赖

```bash
uv sync
```

### 2. 下载微调模型

```bash
python download.py
```

这将从ModelScope下载Murasame的微调模型。

### 3. 下载预训练模型

```bash
cd gpt_sovits
bash install.sh --source ModelScope  # macOS/Linux
# 或
powershell install.ps1               # Windows
cd ..
```

### 4. 启动服务

#### 方式一：单独启动各个服务

```bash
# 终端1: 启动本地API
uv run python api.py

# 终端2: 启动TTS服务
uv run python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880 -c gpt_sovits/configs/tts_infer.yaml

# 终端3: 启动桌宠
uv run python pet.py
```

#### 方式二：使用一键启动脚本（推荐）

```bash
python run_project.py
```

所有服务将在后台启动，日志保存在 `log/` 目录下。按 `Ctrl+C` 可停止所有服务。

## ⚙️ 配置说明

### OpenRouter（可选）

如果你想使用OpenRouter作为云端API提供商：

1. 在 https://openrouter.ai/ 注册并获取API key
2. 修改 `config.json`：

```json
{
    "openrouter_api_key": "sk-or-v1-xxxxxxxxxxxxx",
    "endpoints": {
        "qwen3": "https://openrouter.ai/api/v1/chat/completions",
        "qwenvl": "https://openrouter.ai/api/v1/chat/completions",
        "murasame": "https://openrouter.ai/api/v1/chat/completions"
    }
}
```

### Ollama（本地部署可选）

如果没有云端API，可以使用Ollama在本地运行模型：

```bash
# 1. 安装Ollama
# 访问 https://ollama.com/download 下载并安装

# 2. 下载模型
ollama pull qwen3:14b
ollama pull qwen2.5vl:7b

# 3. 确认config.json配置
{
    "endpoints": {
        "ollama": "http://localhost:11434"
    }
}
```

### 端点配置

根据你的部署情况，可能需要修改 `config.json` 中的端点地址：

- `ollama`: Ollama服务地址（默认 `http://localhost:11434`）
- `murasame-sovits`: TTS服务地址（默认 `http://127.0.0.1:9880/tts`）
- `qwen3`, `qwenvl`, `murasame`: 本地API或云端API地址

### macOS权限配置

如果使用视觉功能（截图分析），需要配置屏幕录制权限：

1. 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制
2. 点击"+"添加Terminal或Python
3. 重启 `api.py` 服务

## 💬 使用方法

- **对话**: 点击丛雨下半部分可以输入文本内容
- **摸头**: 长按鼠标拖动丛雨的头部左右移动

## 📁 项目结构

```
MurasamePet-With-MPS/
├── api.py              # 本地API服务（视觉、翻译等）
├── pet.py              # 桌宠主程序
├── config.json         # 配置文件
├── download.py         # 模型下载脚本
├── run_project.py      # 一键启动脚本
├── Murasame/           # 聊天逻辑
│   ├── chat.py
│   ├── generate.py
│   └── utils.py
├── gpt_sovits/         # TTS服务（精简版）
│   ├── api_v2.py       # TTS API
│   ├── install.sh      # 预训练模型下载脚本
│   └── GPT_SoVITS/     # TTS核心模块
├── models/             # 微调模型
│   ├── Murasame/       # LLM模型
│   └── Murasame_SoVITS/  # 语音模型和参考音频
├── voices/             # 生成的语音缓存
└── log/                # 服务日志
```

## 🛠️ TTS快速测试

启动TTS服务后，可以使用以下命令测试：

```bash
# 健康检查
curl http://127.0.0.1:9880/

# 测试TTS（需要替换音频路径）
curl -X POST "http://127.0.0.1:9880/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "こんにちは、ムラサメです。",
    "text_lang": "ja",
    "ref_audio_path": "/absolute/path/to/reference.wav",
    "prompt_text": "参考音频文本",
    "prompt_lang": "ja"
  }' \
  --output test.wav
```

## 🔧 故障排查

### Python版本问题

如果遇到Python版本相关问题，请参考 [PYTHON_VERSION_DETECTION.md](PYTHON_VERSION_DETECTION.md)

### 服务启动失败

1. 检查日志文件：`log/api/`, `log/pet/`, `log/gpt_sovits/`
2. 确认所有依赖已安装：`uv sync`
3. 确认预训练模型已下载：`bash gpt_sovits/install.sh`

### TTS调用失败

1. 确认TTS服务正在运行：`curl http://127.0.0.1:9880/`
2. 检查 `config.json` 中的端点配置
3. 确认参考音频路径为绝对路径

### macOS权限问题

如果出现权限错误，参考上面的"macOS权限配置"章节。

## 📖 技术文档

- [Python版本检测优化说明](PYTHON_VERSION_DETECTION.md)
- [GPT-SoVITS README](gpt_sovits/README.md)

## 📄 许可证

见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - TTS语音合成
- [Ollama](https://ollama.com/) - 本地LLM运行
- [OpenRouter](https://openrouter.ai/) - 云端API服务

---

**维护者**: MurasamePet Team  
**最后更新**: 2025-10
