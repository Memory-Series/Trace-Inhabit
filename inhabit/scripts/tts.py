#!/usr/bin/env python3
"""
Memory-Inhabit TTS — 语音消息生成器

用法：
  python3 tts.py "要转换的文字" -o output.mp3
  python3 tts.py "要转换的文字" --voice zh-CN-XiaoxiaoNeural
  python3 tts.py --list-voices
"""

import asyncio
import sys
import argparse
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("❌ 需要安装 edge-tts: pip3 install edge-tts")
    sys.exit(1)


# 可用中文语音
VOICES = {
    # 女声
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",   # 温暖，通用
    "xiaoyi": "zh-CN-XiaoyiNeural",       # 活泼，卡通
    # 男声
    "yunxi": "zh-CN-YunxiNeural",         # 阳光少年
    "yunjian": "zh-CN-YunjianNeural",     # 热情
    "yunyang": "zh-CN-YunyangNeural",     # 专业稳重
    "yunxia": "zh-CN-YunxiaNeural",       # 可爱
    # 方言
    "xiaobei": "zh-CN-liaoning-XiaobeiNeural",  # 东北话
    "xiaoni": "zh-CN-shaanxi-XiaoniNeural",     # 陕西话
}

DEFAULT_VOICE = "xiaoxiao"


async def generate_tts(text, output_path, voice_name=DEFAULT_VOICE, rate="+0%", volume="+0%"):
    """生成语音文件"""
    voice_id = VOICES.get(voice_name, voice_name)
    
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)
    await communicate.save(output_path)
    return output_path


async def list_voices():
    """列出所有可用语音"""
    voices = await edge_tts.list_voices()
    zh_voices = [v for v in voices if v["Locale"].startswith("zh")]
    
    print("🎤 可用中文语音：\n")
    for v in zh_voices:
        short = v["ShortName"].replace("zh-CN-", "").replace("zh-TW-", "")
        gender = "♀" if v["Gender"] == "Female" else "♂"
        styles = ", ".join(v.get("StyleList", [])) or "通用"
        print(f"  {gender} {short:<30} {styles}")


def main():
    parser = argparse.ArgumentParser(description="Memory-Inhabit TTS 语音生成")
    parser.add_argument("text", nargs="?", help="要转换的文字")
    parser.add_argument("-o", "--output", default="/tmp/mi_voice.mp3", help="输出文件路径")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, help=f"语音名称（默认: {DEFAULT_VOICE}）")
    parser.add_argument("-r", "--rate", default="+0%", help="语速调整，如 +20% 或 -10%")
    parser.add_argument("--volume", default="+0%", help="音量调整")
    parser.add_argument("--list-voices", action="store_true", help="列出可用语音")
    
    args = parser.parse_args()
    
    if args.list_voices:
        asyncio.run(list_voices())
        return
    
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    output = asyncio.run(generate_tts(args.text, args.output, args.voice, args.rate, args.volume))
    print(f"✅ 语音已生成: {output}")


if __name__ == "__main__":
    main()
