# MurasamePet

https://www.bilibili.com/video/BV1vjeGzfE1w

感谢 @小四啊-_- 提供的安装运行教程

>  https://www.bilibili.com/opus/1110957341959782402

## 部署  (py3.9.15) (conda)

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

### 注

若 Ollama / api.py 不在本地运行，那么需要在 `./config.json`中修改相关 endpoint 地址

## 使用（？）

点击丛雨下半部分可以输入内容，长按鼠标按住丛雨的头部并左右移动可以摸头……
