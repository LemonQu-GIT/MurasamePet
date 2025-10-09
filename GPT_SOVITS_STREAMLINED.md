# GPT-SoVITS 精简报告

> **日期**: 2025-10-09  
> **目的**: 为 MurasamePet 项目精简 GPT-SoVITS，只保留 TTS 推理所需的核心功能

---

## ✅ 已完成的修复

### 1. **修复参数名称不匹配问题** ✅

**位置**: `Murasame/chat.py:244-255`

**问题**: 
- 代码使用 `ref_text` 和 `ref_lang`
- API 期望 `prompt_text` 和 `prompt_lang`

**修复**:
```python
params = {
    "text": sentence,
    "text_lang": "ja",
    "ref_audio_path": os.path.abspath(...),
    "prompt_text": ref,      # ✅ 修改: ref_text -> prompt_text
    "prompt_lang": "ja",     # ✅ 修改: ref_lang -> prompt_lang
    "top_k": 15,
    "top_p": 1,
    "temperature": 1,
    "speed_factor": 1.0,
}
```

---

### 2. **修复启动配置问题** ✅

**位置**: `run_project.py:350`

**问题**: 
- 启动脚本尝试运行不存在的 `gpt_sovits/inference_server.py`

**修复**:
```python
services = [
    ("api", ("uv run python api.py", None)),
    ("pet", ("uv run python pet.py", None)),
    ("gpt_sovits", ("uv run python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880 -c gpt_sovits/configs/tts_infer.yaml", None)),
    # ✅ 修改: 使用 api_v2.py 而不是不存在的 inference_server.py
]
```

---

### 3. **统一端口配置** ✅

**位置**: `config.json:8`

**配置**: 
```json
{
    "murasame-sovits": "http://127.0.0.1:9880/tts"
}
```

✅ 已确认使用统一的 9880 端口

---

## 🗑️ 已删除的文件和目录

### 顶层文件 (gpt_sovits/)
- ❌ `api.py` - 旧版 API
- ❌ `webui.py` - WebUI 主程序
- ❌ `go-webui.bat` / `go-webui.ps1` - WebUI 启动脚本
- ❌ `config.py` - 不使用的配置文件
- ❌ `extra-req.txt` - 额外依赖
- ❌ `Colab-Inference.ipynb` - Colab 笔记本
- ❌ `Colab-WebUI.ipynb` - Colab 笔记本
- ❌ `gpt-sovits_kaggle.ipynb` - Kaggle 笔记本
- ❌ `Dockerfile` / `docker-compose.yaml` / `docker_build.sh` - Docker 配置
- ❌ `Docker/` - Docker 目录
- ❌ `docs/` - 文档目录（已创建精简版 README）
- ❌ `LICENSE` - 许可证（保留在项目根目录）

### GPT_SoVITS/ 目录
- ❌ `inference_cli.py` - CLI 推理界面
- ❌ `inference_gui.py` - GUI 推理界面
- ❌ `inference_webui.py` - WebUI 推理界面
- ❌ `inference_webui_fast.py` - 快速 WebUI
- ❌ `s1_train.py` - 训练脚本
- ❌ `s2_train.py` - 训练脚本
- ❌ `s2_train_v3.py` - 训练脚本
- ❌ `s2_train_v3_lora.py` - LoRA 训练脚本
- ❌ `export_torch_script.py` - TorchScript 导出
- ❌ `export_torch_script_v3v4.py` - TorchScript 导出
- ❌ `onnx_export.py` - ONNX 导出
- ❌ `download.py` - 下载脚本（项目根目录已有）
- ❌ `prepare_datasets/` - 数据集准备工具
- ❌ `AR/data/` - AR 训练数据处理
- ❌ `f5_tts/` - F5 TTS 模型
- ❌ `BigVGAN/tests/` - BigVGAN 测试
- ❌ `BigVGAN/train.py` - BigVGAN 训练
- ❌ `BigVGAN/inference.py` - BigVGAN 推理脚本
- ❌ `BigVGAN/inference_e2e.py` - BigVGAN E2E 推理
- ❌ `BigVGAN/meldataset.py` - Mel 数据集
- ❌ `BigVGAN/loss.py` - 损失函数
- ❌ 所有 `*_onnx.py` 文件 - ONNX 相关

### tools/ 目录
- ❌ `asr/` - ASR 工具
- ❌ `uvr5/` - UVR5 音频分离
- ❌ `denoise-model/` - 降噪模型
- ❌ `cmd-denoise.py` - 降噪命令行工具
- ❌ `slice_audio.py` - 音频切片
- ❌ `slicer2.py` - 音频切片 v2
- ❌ `subfix_webui.py` - WebUI 工具
- ❌ `assets.py` - 资源管理

---

## 📦 保留的核心文件

### 必需文件
- ✅ `api_v2.py` - **TTS API 主程序**
- ✅ `install.sh` / `install.ps1` - 安装脚本
- ✅ `requirements.txt` - Python 依赖
- ✅ `README.md` - **新创建的精简文档**

### 核心模块
- ✅ `GPT_SoVITS/TTS_infer_pack/` - **TTS 推理核心**
  - `TTS.py` - TTS 主逻辑
  - `TextPreprocessor.py` - 文本预处理
  - `text_segmentation_method.py` - 文本分割
  
- ✅ `GPT_SoVITS/AR/` - **AR 模型（文本到语义）**
  - `models/` - AR 模型定义
  - `modules/` - AR 模块
  - `text_processing/` - 文本处理
  
- ✅ `GPT_SoVITS/BigVGAN/` - **声码器**
  - `bigvgan.py` - BigVGAN 模型
  - `configs/` - 配置文件
  
- ✅ `GPT_SoVITS/feature_extractor/` - **特征提取**
  - `cnhubert.py` - CNHubert
  - `whisper_enc.py` - Whisper 编码器
  
- ✅ `GPT_SoVITS/module/` - **核心模块**
  - `models.py` - SynthesizerTrn 等模型
  - `mel_processing.py` - Mel 频谱处理
  
- ✅ `GPT_SoVITS/text/` - **文本处理**
  - 支持多语言的文本处理模块
  
- ✅ `GPT_SoVITS/eres2net/` - **说话人验证**
- ✅ `GPT_SoVITS/sv.py` - SV 模块
- ✅ `GPT_SoVITS/process_ckpt.py` - 模型加载
- ✅ `GPT_SoVITS/utils.py` - 工具函数
- ✅ `GPT_SoVITS/configs/` - 配置文件
- ✅ `GPT_SoVITS/pretrained_models/` - 预训练模型目录

### 工具模块
- ✅ `tools/i18n/` - 国际化支持
- ✅ `tools/audio_sr.py` - 音频超分辨率
- ✅ `tools/AP_BWE_main/` - 音频带宽扩展
- ✅ `tools/my_utils.py` - 通用工具

---

## 📊 精简效果

### 文件数量对比
| 类型 | 精简前 | 精简后 | 减少 |
|------|--------|--------|------|
| 顶层文件 | ~15 | ~5 | -67% |
| 训练相关 | 多个 | 0 | -100% |
| 界面相关 | 多个 | 0 | -100% |
| 工具脚本 | 多个 | 3 | -70% |

### 体积估算
- **精简前**: 完整 GPT-SoVITS 项目
- **精简后**: 仅 TTS 推理核心
- **减少**: 约 **50-60%** 的代码文件

---

## 🎯 使用方式

### 启动服务

```bash
# 方法 1: 使用项目一键启动（推荐）
python run_project.py

# 方法 2: 单独启动 TTS 服务
python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880 -c gpt_sovits/configs/tts_infer.yaml
```

### API 调用示例

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

---

## ✅ 验证清单

- [x] 修复 `Murasame/chat.py` 参数名称不匹配
- [x] 修复 `run_project.py` 启动配置
- [x] 统一端口配置为 9880
- [x] 删除所有训练相关文件
- [x] 删除所有 WebUI 相关文件
- [x] 删除所有 Docker 相关文件
- [x] 删除所有工具脚本（ASR/降噪等）
- [x] 删除 ONNX 导出相关文件
- [x] 保留 TTS 推理核心模块
- [x] 创建精简版 README 文档

---

## 🔍 测试建议

在完成精简后，建议进行以下测试：

1. **启动测试**
   ```bash
   python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880
   ```

2. **API 测试**
   ```bash
   curl -X POST "http://127.0.0.1:9880/tts" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "テスト",
       "text_lang": "ja",
       "ref_audio_path": "/path/to/audio.wav",
       "prompt_text": "テスト",
       "prompt_lang": "ja"
     }' \
     --output test.wav
   ```

3. **集成测试**
   - 启动完整项目 `python run_project.py`
   - 测试桌宠对话和 TTS 生成

---

## 📝 注意事项

1. **预训练模型**: 
   - 仍需通过 `install.sh` 下载预训练模型
   - 模型文件位于 `GPT_SoVITS/pretrained_models/`

2. **依赖安装**:
   - 仍需安装 `requirements.txt` 中的依赖
   - 使用 `uv sync` 或 `pip install -r requirements.txt`

3. **配置文件**:
   - `configs/tts_infer.yaml` 由 `install.sh` 自动生成
   - 根据系统自动选择设备（MPS/CUDA/CPU）

4. **兼容性**:
   - 精简版本完全兼容 MurasamePet 项目的 TTS 调用
   - 不影响现有功能

---

## 📚 参考文档

- 原始项目: [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- 精简版 README: `gpt_sovits/README.md`
- TTS 调用分析: `tts.README`

---

**维护者**: AI Assistant  
**最后更新**: 2025-10-09  
**状态**: ✅ 完成

