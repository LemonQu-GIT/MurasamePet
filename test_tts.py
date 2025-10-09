#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS TTS API 测试脚本
用于验证精简后的 TTS 服务是否正常工作
"""

import requests
import os
import sys
import time

def test_tts_api():
    """测试 TTS API"""
    print("=" * 60)
    print("🧪 GPT-SoVITS TTS API 测试")
    print("=" * 60)
    
    # 配置
    api_url = "http://127.0.0.1:9880/tts"
    emotion = "平静"  # 测试情感
    ref_audio_dir = "./models/Murasame_SoVITS/reference_voices"
    
    # 检查服务是否运行
    print("\n1️⃣  检查 TTS 服务状态...")
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=2)
        print("   ✅ TTS 服务正在运行")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ TTS 服务未运行: {e}")
        print("\n💡 请先启动 TTS 服务:")
        print("   python gpt_sovits/api_v2.py -a 127.0.0.1 -p 9880")
        return False
    
    # 检查参考音频目录
    print(f"\n2️⃣  检查参考音频目录...")
    emotion_dir = f"{ref_audio_dir}/{emotion}"
    if not os.path.exists(emotion_dir):
        print(f"   ❌ 参考音频目录不存在: {emotion_dir}")
        print("\n💡 请确保已运行 install.sh 下载参考音频")
        return False
    
    # 获取参考音频
    audio_files = [f for f in os.listdir(emotion_dir) if f.endswith('.wav')]
    if not audio_files:
        print(f"   ❌ 未找到参考音频文件")
        return False
    
    print(f"   ✅ 找到参考音频: {audio_files[0]}")
    
    # 读取参考文本
    asr_file = f"{emotion_dir}/asr.txt"
    if not os.path.exists(asr_file):
        print(f"   ❌ ASR 文本文件不存在: {asr_file}")
        return False
    
    with open(asr_file, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()
    
    print(f"   ✅ 参考文本: {prompt_text[:30]}...")
    
    # 准备测试参数
    print(f"\n3️⃣  准备 TTS 请求参数...")
    params = {
        "text": "こんにちは、ご主人。吾輩はムラサメです。",
        "text_lang": "ja",
        "ref_audio_path": os.path.abspath(f"{emotion_dir}/{audio_files[0]}"),
        "prompt_text": prompt_text,
        "prompt_lang": "ja",
        "top_k": 15,
        "top_p": 1,
        "temperature": 1,
        "speed_factor": 1.0
    }
    
    print(f"   ✅ 文本: {params['text']}")
    print(f"   ✅ 语言: {params['text_lang']}")
    print(f"   ✅ 参考音频: {audio_files[0]}")
    
    # 调用 TTS API
    print(f"\n4️⃣  调用 TTS API...")
    try:
        start_time = time.time()
        response = requests.post(api_url, json=params, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"   ✅ API 调用成功 ({elapsed_time:.2f}秒)")
            
            # 保存音频
            output_file = "test_output.wav"
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024  # KB
            print(f"   ✅ 音频已保存: {output_file} ({file_size:.1f} KB)")
            
            # macOS 自动播放
            if sys.platform == "darwin":
                print("\n5️⃣  播放测试音频...")
                os.system(f"afplay {output_file}")
                print("   ✅ 音频播放完成")
            else:
                print(f"\n💡 请手动播放音频文件: {output_file}")
            
            return True
        else:
            print(f"   ❌ API 调用失败: HTTP {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时 (30秒)")
        print("   💡 TTS 生成可能需要更长时间，请检查服务日志")
        return False
    except Exception as e:
        print(f"   ❌ 发生错误: {e}")
        return False

def main():
    """主函数"""
    success = test_tts_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TTS API 测试通过！")
        print("=" * 60)
        print("\n💡 下一步:")
        print("   - 启动完整项目: python run_project.py")
        print("   - 测试桌宠对话功能")
    else:
        print("❌ TTS API 测试失败")
        print("=" * 60)
        print("\n💡 故障排查:")
        print("   1. 确保 TTS 服务已启动")
        print("   2. 检查参考音频目录是否存在")
        print("   3. 查看服务日志输出")
        print("   4. 验证预训练模型是否已下载")
    
    print()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

