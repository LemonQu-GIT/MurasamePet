#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MurasamePet 一键运行项目脚本
跨平台Python脚本，用于检测环境、配置依赖和运行MurasamePet项目
"""

import os
import sys
import platform
import subprocess
import json
import shutil
import datetime
import time

# 确保标准输出使用 UTF-8 编码，防止中文乱码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def log(message, level="INFO"):
    """日志输出"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 根据日志级别添加表情符号
    emoji_map = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍",
    }
    emoji = emoji_map.get(level, "📝")
    
    print(f"{emoji} [{timestamp}] [{level}] {message}")

def run_command(cmd, cwd=None, shell=False, capture_output=False, check=True):
    """运行命令"""
    try:
        log(f"🔧 执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}", "DEBUG")
        result = subprocess.run(cmd, cwd=cwd, shell=shell, capture_output=capture_output, text=True, check=check)
        if capture_output:
            return result.stdout.strip(), result.stderr.strip()
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        log(f"命令执行失败: {e}", "ERROR")
        if capture_output:
            return "", str(e)
        return False

def get_system_info():
    """获取系统信息"""
    system = platform.system()
    machine = platform.machine()
    processor = platform.processor()
    # 内存信息
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_info = f"{memory.total // (1024**3)}GB"
    except ImportError:
        # 如果没有psutil，使用系统命令
        if system == "Darwin":
            try:
                result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
                memory_bytes = int(result.stdout.strip())
                memory_info = f"{memory_bytes // (1024**3)}GB"
            except:
                memory_info = "未知"
        elif system == "Windows":
            try:
                result = subprocess.run(["wmic", "computersystem", "get", "totalphysicalmemory"], capture_output=True, text=True)
                memory_bytes = int(result.stdout.strip().split('\n')[1])
                memory_info = f"{memory_bytes // (1024**3)}GB"
            except:
                memory_info = "未知"
        else:
            memory_info = "未知"

    # Windows显卡
    gpu_info = ""
    if system == "Windows":
        try:
            result = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"], capture_output=True, text=True)
            gpus = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith("Name")]
            gpu_info = ", ".join(gpus)
        except:
            gpu_info = "未知"

    return system, machine, processor, memory_info, gpu_info

def check_config():
    """检查config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        api_key = config.get("openrouter_api_key")
        endpoints = config.get("endpoints", {})
        murasame_endpoint = endpoints.get("murasame", "")
        is_murasame_local = any(local in murasame_endpoint for local in ["127.", "localhost", "fe80", "::1"])
        all_endpoints_local = all(
            any(local in ep for local in ["127.", "localhost", "fe80", "::1"])
            for ep in endpoints.values()
        )
        return api_key, is_murasame_local, all_endpoints_local
    except Exception as e:
        log(f"读取config.json失败: {e}", "ERROR")
        return None, False, False

def check_homebrew():
    """检查macOS Homebrew"""
    try:
        result = subprocess.run(["brew", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_cuda():
    """检查Windows CUDA"""
    try:
        result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_uv():
    """检查uv"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_python_version():
    """获取Python版本"""
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"

def check_python_version():
    """检查Python版本 == 3.10"""
    version = sys.version_info
    return (version.major, version.minor) == (3, 10)

def check_download_executed():
    """检查download.py是否执行"""
    return os.path.exists("models") and os.listdir("models")

def check_install_executed():
    """检查install.sh/ps1是否执行"""
    system = platform.system()
    if system == "Darwin":
        # 检查gpt_sovits/pretrained_models/sv
        if not os.path.exists("gpt_sovits/pretrained_models/sv"):
            return False
        # 检查NLTK数据
        try:
            import sys
            py_prefix = sys.prefix
            if not os.path.exists(os.path.join(py_prefix, "nltk_data")):
                return False
        except:
            pass
        # 检查Open JTalk Dic
        try:
            import pyopenjtalk
            pyopenjtalk_prefix = os.path.dirname(pyopenjtalk.__file__)
            if not os.path.exists(os.path.join(pyopenjtalk_prefix, "open_jtalk_dic_utf_8-1.11")):
                return False
        except:
            pass
        return True
    elif system == "Windows":
        return os.path.exists("GPT_SoVITS/pretrained_models/sv")
    return False

def install_homebrew():
    """安装Homebrew"""
    log("安装Homebrew...")
    cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    if run_command(cmd, shell=True):
        log("Homebrew安装成功")
        # 设置环境变量
        zshrc = os.path.expanduser("~/.zshrc")
        lines = [
            'eval "$(/opt/homebrew/bin/brew shellenv)"'
        ]
        with open(zshrc, "a") as f:
            f.write("\n".join(lines) + "\n")
        log("Homebrew环境变量已添加到~/.zshrc")
    else:
        log("Homebrew安装失败", "ERROR")
        sys.exit(1)

def install_uv_macos():
    """macOS安装uv"""
    log("使用Homebrew安装uv...")
    if run_command(["brew", "install", "uv"]):
        log("uv安装成功")
    else:
        log("uv安装失败", "ERROR")
        sys.exit(1)

    # 安装python和mecab
    if run_command(["brew", "install", "python", "mecab"]):
        log("Python和mecab安装成功")
    else:
        log("Python和mecab安装失败", "ERROR")
        sys.exit(1)


def install_python310_macos():
    """macOS安装Python 3.10"""
    log("使用Homebrew安装Python 3.10...")
    if run_command(["brew", "install", "python@3.10"]):
        log("Python 3.10安装成功")
        # 取消链接Python 3.13，如果存在
        run_command(["brew", "unlink", "python@3.13"])
        # 链接Python 3.10
        if run_command(["brew", "link", "python@3.10", "--force"]):
            log("Python 3.10已链接为默认python3")
        else:
            log("链接Python 3.10失败，尝试设置PATH")
            # 设置环境变量
            zshrc = os.path.expanduser("~/.zshrc")
            lines = [
                'export PATH="/opt/homebrew/opt/python@3.10/libexec/bin:$PATH"'
            ]
            with open(zshrc, "a") as f:
                f.write("\n".join(lines) + "\n")
            log("Python 3.10环境变量已添加到~/.zshrc")
        log("请重新启动终端或运行 'source ~/.zshrc' 以应用更改")
    else:
        log("Python 3.10安装失败", "ERROR")
        sys.exit(1)

def uninstall_pip_uv():
    """卸载pip安装的uv"""
    log("卸载pip安装的uv...")
    run_command([sys.executable, "-m", "pip", "uninstall", "uv", "-y"])

def run_download():
    """运行download.py"""
    log("添加modelscope依赖...")
    if not run_command(["uv", "add", "modelscope"]):
        log("uv add modelscope失败", "ERROR")
        sys.exit(1)
    log("运行download.py...")
    if run_command([sys.executable, "download.py"]):
        log("download.py执行成功")
    else:
        log("download.py执行失败", "ERROR")
        sys.exit(1)

def run_install():
    """运行install.sh或install.ps1"""
    system = platform.system()
    if system == "Darwin":
        log("macOS: 安装wget...")
        if run_command(["brew", "install", "wget"]):
            log("wget安装成功")
        else:
            log("wget安装失败", "ERROR")
            sys.exit(1)

        log("运行install.sh...")
        # 修改install.sh中的python为python3
        try:
            with open("gpt_sovits/install.sh", "r") as f:
                content = f.read()
            content = content.replace("python ", "python3 ")
            content = content.replace(" pip ", " pip3 ")
            with open("gpt_sovits/install.sh", "w") as f:
                f.write(content)
            log("已修改install.sh中的python为python3")
        except Exception as e:
            log(f"修改install.sh失败: {e}", "ERROR")
        # 需要参数，假设默认值
        cmd = ["bash", "gpt_sovits/install.sh", "--device", "MPS", "--source", "ModelScope", "--download-uvr5"]
        if run_command(cmd):
            log("install.sh执行成功")
            # 创建配置文件
            create_tts_config()
        else:
            log("install.sh执行失败", "ERROR")
            sys.exit(1)
    elif system == "Windows":
        log("运行install.ps1...")
        # 修改install.ps1中的python为python
        try:
            with open("gpt_sovits/install.ps1", "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("python ", "python ")
            # Windows可能需要python3，但通常是python
            with open("gpt_sovits/install.ps1", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            log(f"修改install.ps1失败: {e}", "ERROR")
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", "gpt_sovits/install.ps1", "-Device", "CPU", "-Source", "HF", "-DownloadUVR5"]
        if run_command(cmd):
            log("install.ps1执行成功")
            # 创建配置文件
            create_tts_config()
        else:
            log("install.ps1执行失败", "ERROR")
            sys.exit(1)

def create_tts_config():
    """创建TTS配置文件"""
    config_path = "gpt_sovits/configs/tts_infer.yaml"
    pretrained_dir = os.path.abspath("gpt_sovits/GPT_SoVITS/pretrained_models")

    # 根据平台和硬件设置设备
    system = platform.system()
    if system == "Darwin":
        device = "mps"  # macOS 使用 MPS
    elif system == "Windows" and check_cuda():
        device = "cuda"  # Windows 有 CUDA 使用 CUDA
    else:
        device = "cpu"  # 其他情况使用 CPU

    # 创建包含 custom 键的配置，这样 TTS_Config 会优先使用它
    content = f"""custom:
  device: {device}
  is_half: false
  version: v2
  t2s_weights_path: {pretrained_dir}/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
  vits_weights_path: {pretrained_dir}/s2G488k.pth
  bert_base_path: {pretrained_dir}/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: {pretrained_dir}/chinese-hubert-base
"""
    with open(config_path, "w") as f:
        f.write(content)
    log(f"已创建TTS配置文件: {config_path} (设备: {device})")

def run_services():
    """运行服务端"""
    log("🌟 开始启动所有服务...")

    # 创建log目录
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        log(f"📁 创建日志目录: {log_dir}")

    services = [
        ("api", ("uv run python api.py", None)),
        ("pet", ("uv run python pet.py", None)),
        ("gpt_sovits", ("uv run python gpt_sovits/api_v2.py -a 0.0.0.0 -p 9880 -c gpt_sovits/configs/tts_infer.yaml", None)),
    ]

    processes = []
    for name, (cmd, cwd_path) in services:
        service_log_dir = os.path.join(log_dir, name)
        if not os.path.exists(service_log_dir):
            os.makedirs(service_log_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(service_log_dir, f"{timestamp}.log")

        log(f"🚀 启动服务: {name}", "SUCCESS")
        log(f"   📄 日志文件: {log_file}")

        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(cmd, shell=True, stdout=f, stderr=f, cwd=cwd_path)
            processes.append((name, process))

    print()
    log("✅ 所有服务已启动！", "SUCCESS")
    log(f"📂 日志保存在 {log_dir} 目录下")
    log("⚠️ 按 Ctrl+C 可停止所有服务", "WARNING")
    print("=" * 70)

    try:
        while True:
            all_running = True
            for name, process in processes:
                if process.poll() is not None:
                    log(f"❌ 服务 {name} 已崩溃 (退出码: {process.returncode})", "ERROR")
                    log("正在停止所有服务...", "WARNING")
                    all_running = False
                    break
            if not all_running:
                break
            time.sleep(10)  # 检查间隔
    except KeyboardInterrupt:
        print()
        log("🛑 收到停止信号，正在关闭所有服务...", "WARNING")
    finally:
        for name, process in processes:
            if process.poll() is None:
                log(f"⏹️ 正在停止服务: {name}")
                process.terminate()
        # 等待进程结束
        for name, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log(f"⚠️ 强制终止服务: {name}", "WARNING")
                process.kill()
        print()
        log("✅ 所有服务已停止", "SUCCESS")
        print("=" * 70)

def main():
    print("=" * 70)
    print("🚀 MurasamePet 一键运行项目脚本")
    print("=" * 70)
    log("开始检测和配置环境...")

    # 1. 检测环境
    log("📋 正在读取配置文件...")
    api_key, is_murasame_local, all_endpoints_local = check_config()
    skip_device_check_23 = False
    if api_key and not is_murasame_local:
        skip_device_check_23 = True
        log("🌐 根据配置，该项目所有模型运行在云端", "SUCCESS")
    elif not api_key and not all_endpoints_local:
        skip_device_check_23 = True
        log("⚡ 根据配置，该项目部分模型运行在本地，请注意内存消耗", "WARNING")
    else:
        log("🏠 根据配置，该项目部分模型运行在本地，请注意内存消耗", "WARNING")

    # 2. 检测设备
    log("💻 正在检测系统信息...")
    system, machine, processor, memory, gpu = get_system_info()
    log(f"🖥️ 系统: {system}")
    log(f"🏗️ 架构: {machine}")
    log(f"⚙️ 处理器: {processor}")
    log(f"💾 内存: {memory}")
    if gpu:
        log(f"🎮 显卡: {gpu}")

    if not skip_device_check_23:
        # 检查是否需要结束脚本
        if system == "Darwin" and "Intel" in processor:
            log("使用Intel CPU的macOS设备，MLX框架和PyTorch框架均不兼容，无法运行AI模型", "ERROR")
            log("脚本结束")
            sys.exit(1)
        elif system == "Linux":
            log("使用Linux系统的设备，未对该平台进行适配", "ERROR")
            log("如果你是开发者并有兴趣进行适配，可fork该仓库并提交PR，或向270598250@qq.com邮箱发送邮件以获得具体的要求和技术支持")
            log("脚本结束")
            sys.exit(1)
        elif system == "Windows" and gpu and "NVIDIA" not in gpu:
            log("使用Windows系统但非NVIDIA显卡，GPT-SoVITS模型不支持CUDA外的其它加速方式", "ERROR")
            log("请安装CUDA: https://www.cnblogs.com/AirCL/p/16963463.html")
            log("脚本结束")
            sys.exit(1)

    # 3. 检测是否需要配置环境
    need_config = False
    config_reasons = []

    if system == "Darwin":
        if not check_homebrew():
            need_config = True
            config_reasons.append("macOS未安装ARM架构的Homebrew")
    elif system == "Windows":
        if not check_cuda():
            need_config = True
            config_reasons.append("Windows未安装CUDA")

    if not check_uv():
        need_config = True
        config_reasons.append("未安装uv")

    if not check_python_version():
        need_config = True
        config_reasons.append("Python版本 != 3.10")

    if not check_download_executed():
        need_config = True
        config_reasons.append("download.py未执行")

    if not check_install_executed():
        need_config = True
        config_reasons.append("install.sh/ps1未执行")

    if need_config:
        log("⚙️ 环境存在问题，需要配置:", "WARNING")
        for reason in config_reasons:
            log(f"  ⚠️ {reason}", "WARNING")

        # 5. 配置环境
        if system == "Darwin":
            if not check_homebrew():
                install_homebrew()
            if not check_python_version():
                install_python310_macos()
            if not check_uv():
                install_uv_macos()
                if check_uv():  # 如果pip安装了uv，卸载
                    uninstall_pip_uv()

        elif system == "Windows":
            if not check_cuda():
                log("请安装CUDA: https://www.cnblogs.com/AirCL/p/16963463.html", "ERROR")
                sys.exit(1)
            if not check_uv() or not check_python_version():
                log("请安装uv和Python >= 3.10", "ERROR")
                sys.exit(1)

        if not check_download_executed():
            run_download()

        if not check_install_executed():
            # 先uv sync安装依赖
            log("执行uv sync以安装依赖...")
            if not run_command(["uv", "sync"]):
                log("uv sync失败", "ERROR")
                sys.exit(1)
            log("uv sync成功")
            run_install()

    else:
        log("✅ 环境检查通过，无需配置", "SUCCESS")

    # 6. 运行项目
    print()
    print("=" * 70)
    log("🚀 开始运行项目...")
    print("=" * 70)

    # uv sync
    log("📦 正在执行 uv sync 同步依赖...")
    if not run_command(["uv", "sync"]):
        log("uv sync 失败", "ERROR")
        sys.exit(1)
    log("✅ uv sync 成功", "SUCCESS")

    # 运行服务端
    print()
    run_services()

if __name__ == "__main__":
    main()