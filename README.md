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

### 桌宠显示设置

桌宠支持多种显示模式，可根据屏幕大小和个人喜好选择。

#### 🎯 使用预设（推荐）

编辑 `config.json`，选择一个预设模式：

```json
{
    "display": {
        "preset": "balanced"
    }
}
```

**可用预设详情：**

<details>
<summary>📋 点击展开查看所有预设详情</summary>

#### 🎨 紧凑模式 (`compact`)
- **显示范围**: ⭐️ 头部+肩部 (35%)
- **适用场景**: 屏幕较小，需要最大限度节省空间
- **配置**: `{"display": {"preset": "compact"}}`

#### 🎨 平衡模式 (`balanced`) ⭐️ **默认推荐**
- **显示范围**: ⭐️ 上半身 (45%)
- **适用场景**: 推荐使用，平衡显示和空间
- **配置**: `{"display": {"preset": "balanced"}}`

#### 🎨 标准模式 (`standard`)
- **显示范围**: ⭐️⭐️ 到腰部 (60%)
- **适用场景**: 屏幕较大，喜欢看到更多内容
- **配置**: `{"display": {"preset": "standard"}}`

#### 🎨 完整显示 (`full`)
- **显示范围**: ⭐️⭐️⭐️⭐️ 整个桌宠 (100%)
- **适用场景**: 屏幕很大或想看完整立绘
- **配置**: `{"display": {"preset": "full"}}`

</details>

**预设对比表：**

| 预设名称 | 显示内容 | 占用空间 | 推荐场景 |
|---------|---------|---------|---------|
| `compact` | 头部+肩部 | ⭐️ | 小屏幕笔记本 |
| `balanced` ⭐️ | 上半身 | ⭐️⭐️ | 一般使用（默认）|
| `standard` | 到腰部 | ⭐️⭐️⭐️ | 大屏幕 |
| `full` | 完整桌宠 | ⭐️⭐️⭐️⭐️ | 超大屏幕 |

**快速切换示例：**
```json
// 小屏幕笔记本，最省空间
{"display": {"preset": "compact"}}

// 一般使用，推荐设置（默认）
{"display": {"preset": "balanced"}}

// 大屏幕，想看更多
{"display": {"preset": "standard"}}

// 超大屏幕，完整显示
{"display": {"preset": "full"}}
```

#### 🔧 自定义配置（高级）

如果预设不满足需求，可以使用自定义配置：

```json
{
    "display": {
        "preset": "custom",
        "custom": {
            "visible_ratio": 0.4,
            "text_x_offset": 140,
            "text_y_offset": 20
        }
    }
}
```

**参数说明：**
- `visible_ratio`: 桌宠可见高度比例（0.0-1.0）
- `text_x_offset`: 文字水平偏移（正值向右，负值向左）
- `text_y_offset`: 文字垂直偏移（正值向下，负值向上）

**交互区域自动适配：**
- **头部摸头区域**：可见区域的上半部分
- **输入区域**：可见区域的下半部分
- **中键拖动**：任意位置

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

### config.json 完整示例

```json
{
    "openrouter_api_key": "YOUR_OPENROUTER_API_KEY_HERE",
    "endpoints": {
        "ollama": "http://localhost:11434",
        "qwen3": "http://localhost:28565/qwen3",
        "qwenvl": "http://localhost:28565/qwenvl",
        "murasame": "http://localhost:28565/chat",
        "murasame-sovits": "http://127.0.0.1:9880/tts"
    },
    "enable_vl": true,
    "display": {
        "preset": "balanced",
        "custom": {
            "visible_ratio": 0.4,
            "text_x_offset": 140,
            "text_y_offset": 20
        }
    }
}
```

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
