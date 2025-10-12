# GPT-SoVITS TTS 推理引擎 (精简版)

> 本目录是为 MurasamePet 项目精简的 GPT-SoVITS TTS 推理引擎，仅保留了 TTS 推理所需的核心功能。

## 📋 概述

此精简版本**仅用于 TTS (Text-to-Speech) 推理**，已移除所有训练、WebUI 和不必要的功能。

## 🎯 功能

- ✅ **TTS 推理 API** - 通过 HTTP API 进行文本转语音
- ✅ **多语言支持** - 支持中文、日文、英文、韩文等
- ✅ **情感控制** - 支持参考音频进行音色克隆
- ✅ **模型热切换** - 支持运行时切换 GPT 和 SoVITS 模型

## 🚀 快速开始

### 1. 安装依赖

#### 方式 1: 完整项目安装（推荐）

本项目作为 MurasamePet 的子模块，依赖由根项目统一管理：

```bash
# 在项目根目录
cd /path/to/MurasamePet-With-MPS
uv sync
```

#### 方式 2: 下载预训练模型

```bash
# 在 gpt_sovits 目录
cd gpt_sovits
bash install.sh --source ModelScope    # 国内推荐
# 或
bash install.sh --source HF            # 国外
```

这将下载 TTS 推理所需的预训练模型和数据文件。

### 2. 启动 TTS API 服务

```bash
# 方法 1: 使用项目的一键启动脚本（推荐）
python run_project.py

# 方法 2: 单独启动 TTS 服务
python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880 -c gpt_sovits/configs/tts_infer.yaml
```

服务将在 `http://127.0.0.1:9880` 启动。

## 📡 API 使用

### TTS 推理端点

**Endpoint:** `POST /tts`

**请求参数:**

```json
{
    "text": "要合成的文本",
    "text_lang": "ja",
    "ref_audio_path": "/path/to/reference/audio.wav",
    "prompt_text": "参考音频的文本",
    "prompt_lang": "ja",
    "top_k": 15,
    "top_p": 1,
    "temperature": 1,
    "speed_factor": 1.0
}
```

**响应:** WAV 音频流

### 示例调用

```python
import requests

params = {
    "text": "こんにちは、ムラサメです。",
    "text_lang": "ja",
    "ref_audio_path": "/absolute/path/to/reference.wav",
    "prompt_text": "参考音频的转写文本",
    "prompt_lang": "ja",
    "speed_factor": 1.0
}

response = requests.post("http://127.0.0.1:9880/tts", json=params)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

## 📁 目录结构

```
gpt_sovits/
├── api_v2.py                    # TTS API 服务主程序
├── install.sh / install.ps1     # 安装脚本
├── requirements.txt             # Python 依赖
├── configs/                     # 配置文件
│   └── tts_infer.yaml          # TTS 推理配置
├── GPT_SoVITS/                 # 核心模块
│   ├── TTS_infer_pack/         # TTS 推理包
│   │   ├── TTS.py              # TTS 主逻辑
│   │   ├── TextPreprocessor.py # 文本预处理
│   │   └── text_segmentation_method.py
│   ├── AR/                     # AR 模型（文本到语义）
│   │   ├── models/             # AR 模型定义
│   │   ├── modules/            # AR 模块
│   │   ├── text_processing/    # 文本处理
│   │   └── utils/              # 工具函数
│   ├── BigVGAN/                # 声码器
│   │   ├── bigvgan.py          # BigVGAN 模型
│   │   ├── configs/            # BigVGAN 配置
│   │   └── ...
│   ├── feature_extractor/      # 特征提取
│   │   ├── cnhubert.py         # CNHubert 提取器
│   │   └── whisper_enc.py      # Whisper 编码器
│   ├── module/                 # 核心模块
│   │   ├── models.py           # SynthesizerTrn 等模型
│   │   ├── mel_processing.py   # Mel 频谱处理
│   │   └── ...
│   ├── text/                   # 文本处理
│   │   ├── chinese.py          # 中文处理
│   │   ├── japanese.py         # 日文处理
│   │   ├── english.py          # 英文处理
│   │   └── ...
│   ├── eres2net/               # Speaker Verification
│   ├── sv.py                   # SV 模块
│   ├── process_ckpt.py         # 模型加载
│   ├── utils.py                # 工具函数
│   └── pretrained_models/      # 预训练模型（由 install.sh 下载）
└── tools/                      # 工具模块
    ├── i18n/                   # 国际化支持
    ├── audio_sr.py             # 音频超分辨率
    ├── AP_BWE_main/            # 音频带宽扩展
    └── my_utils.py             # 通用工具
```

## ⚙️ 配置说明

### TTS 推理配置 (`configs/tts_infer.yaml`)

```yaml
custom:
  device: auto                   # 设备: auto/cpu/cuda/mps (推荐使用 auto 自动检测)
  is_half: false                 # 是否使用半精度 (仅 CUDA 支持)
  version: v2                    # 模型版本
  t2s_weights_path: ...          # GPT 模型路径
  vits_weights_path: ...         # SoVITS 模型路径
  bert_base_path: ...            # BERT 模型路径
  cnhuhbert_base_path: ...       # CNHubert 模型路径
```

配置文件通常无需手动修改。

### 🚀 自动设备检测

本项目支持**自动检测最优推理设备**，检测优先级为：**MPS > CUDA > CPU**

#### 设备选项说明

- **`device: auto`** （推荐）
  - 自动检测并使用最佳设备
  - Apple Silicon Mac → **MPS** (Metal Performance Shaders)
  - NVIDIA GPU → **CUDA**
  - 其他 → **CPU**

- **手动指定设备**
  - `device: mps` - Apple Silicon GPU 加速
  - `device: cuda` - NVIDIA GPU 加速  
  - `device: cpu` - CPU 推理

#### 性能对比

| 设备 | 适用平台 | 相对性能 | 推荐度 |
|------|---------|---------|--------|
| **MPS** | Apple Silicon (M1/M2/M3/M4) | ⭐⭐⭐⭐ | 🟢 **强烈推荐** |
| **CUDA** | NVIDIA GPU | ⭐⭐⭐⭐⭐ | 🟢 **强烈推荐** |
| **CPU** | 所有平台 | ⭐⭐ | ⚪ 备选 |

#### 配置示例

**自动检测（推荐）**：
```yaml
custom:
  device: auto       # 自动选择最佳设备
  is_half: false
```

**Apple Silicon 用户**：
```yaml
custom:
  device: mps        # 或使用 auto 自动检测
  is_half: false     # MPS 不支持半精度
```

**NVIDIA GPU 用户**：
```yaml
custom:
  device: cuda       # 或使用 auto 自动检测
  is_half: true      # 启用半精度以提升性能
```

## 🔧 常见问题

### 1. 如何更换 TTS 模型？

使用 API 端点动态切换：

```bash
# 切换 GPT 模型
curl "http://127.0.0.1:9880/set_gpt_weights?weights_path=/path/to/gpt.ckpt"

# 切换 SoVITS 模型
curl "http://127.0.0.1:9880/set_sovits_weights?weights_path=/path/to/sovits.pth"
```

### 2. 支持哪些语言？

- 中文 (zh)
- 日文 (ja)
- 英文 (en)
- 韩文 (ko)
- 粤语 (yue)

### 3. 如何控制语速？

使用 `speed_factor` 参数：
- `1.0`: 正常语速
- `< 1.0`: 减速
- `> 1.0`: 加速

## 📝 与原版的区别

此精简版本从原始 GPT-SoVITS 项目中移除了：

- ❌ 所有训练相关代码和脚本
- ❌ WebUI 界面
- ❌ Gradio 界面
- ❌ CLI 工具
- ❌ Docker 配置
- ❌ Jupyter Notebooks
- ❌ 数据集准备工具
- ❌ ONNX 导出功能
- ❌ ASR/降噪等音频预处理工具
- ❌ 详细文档（保留了核心 README）

仅保留了 **TTS 推理的核心功能**，大幅减小了项目体积。

## 📚 参考资料

- 原始项目: [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- API 文档: 见 `api_v2.py` 文件头部注释

## 📄 许可证

本精简版本继承原项目的 MIT 许可证。详见 `LICENSE` 文件。

---

**维护说明:** 此目录为 MurasamePet 项目专用，如需完整功能请使用原始 GPT-SoVITS 项目。
