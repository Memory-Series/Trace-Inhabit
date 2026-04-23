#!/usr/bin/env python3
"""
Memory-Inhabit TTS — 语音消息生成器（智能匹配版）

支持 edge-tts 和 MiniMax TTS，根据 SoulPod profile.json 自动匹配音色。

用法：
  python3 tts.py "要转换的文字" -o output.mp3
  python3 tts.py "要转换的文字" -o output.mp3 --provider minimax
  python3 tts.py --list-voices
"""

import asyncio
import sys
import argparse
import json
import os
import requests
from pathlib import Path

# Edge-TTS 可用性检查
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# MiniMax TTS 配置
MINIMAX_API_URL = "https://api.minimaxi.com/v1/t2a_v2"

# MiniMax 中文男声音色库（按性格+年龄分类）
MINIMAX_VOICES = {
    # 年轻-阳光/不羁
    "young_unrestrained": "Chinese (Mandarin)_Unrestrained_Young_Man",
    # 年轻-温润/磁性
    "young_gentle": "Chinese (Mandarin)_Gentleman",
    # 年轻-抒情/温柔
    "young_lyrical": "Chinese (Mandarin)_Lyrical_Voice",
    # 年轻-清爽/清澈
    "young_pure": "Chinese (Mandarin)_Pure-hearted_Boy",
    # 年轻-率真
    "young_straightforward": "Chinese (Mandarin)_Straightforward_Boy",
    # 中年-沉稳/高管
    "middle_reliable": "Chinese (Mandarin)_Reliable_Executive",
    # 中年-播报/磁性
    "middle_announcer": "Chinese (Mandarin)_Male_Announcer",
    # 中年-商务/专业
    "middle_professional": "Chinese (Mandarin)_Radio_Host",
    # 老年-幽默
    "elder_humorous": "Chinese (Mandarin)_Humorous_Elder",
    # 通用 fallback
    "default_male": "male-qn-qingse",
}

# MiniMax 默认音色
DEFAULT_MINIMAX_VOICE = "young_unrestrained"

# Edge-TTS 中文语音
EDGE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",   # 温暖女声
    "xiaoyi": "zh-CN-XiaoyiNeural",       # 活泼女声
    "yunxi": "zh-CN-YunxiNeural",         # 阳光少年男声
    "yunjian": "zh-CN-YunjianNeural",     # 热情男声
    "yunyang": "zh-CN-YunyangNeural",     # 专业稳重男声
    "yunxia": "zh-CN-YunxiaNeural",       # 可爱男声
    "xiaobei": "zh-CN-liaoning-XiaobeiNeural",  # 东北话
    "xiaoni": "zh-CN-shaanxi-XiaoniNeural",     # 陕西话
}

# Edge-TTS 性格映射
EDGE_VOICE_MOOD = {
    "young_unrestrained": "yunxi",     # 阳光不羁
    "young_gentle": "yunxi",           # 温柔
    "young_lyrical": "yunjian",        # 抒情
    "young_pure": "yunxia",            # 清澈可爱
    "young_straightforward": "yunyang", # 率真
    "middle_reliable": "yunyang",      # 沉稳
    "middle_announcer": "yunyang",      # 播音
    "middle_professional": "yunjian",   # 专业
    "elder_humorous": "xiaobei",        # 幽默老年
}

DEFAULT_EDGE_VOICE = "yunxi"


def load_profile(persona_path=None):
    """加载 SoulPod profile.json"""
    if persona_path is None:
        # 查找最近的 persona 目录
        candidates = [
            Path(__file__).parent.parent / "personas",
            Path.home() / ".openclaw" / "workspace" / "skills" / "memory-inhabit" / "personas",
            Path.home() / ".openclaw" / "workspace-coding" / "skills" / "Memory-Inhabit" / "personas",
            Path.home() / ".openclaw" / "workspace-roleplay" / "skills" / "memory-inhabit" / "personas",
        ]
        for cand in candidates:
            if cand.exists():
                # 找第一个有 profile.json 的子目录
                for sub in cand.iterdir():
                    if sub.is_dir() and (sub / "profile.json").exists():
                        persona_path = sub
                        break
                break
    
    if persona_path and (Path(persona_path) / "profile.json").exists():
        with open(Path(persona_path) / "profile.json") as f:
            return json.load(f)
    return {}


def load_config(persona_path=None):
    """加载 config.json"""
    if persona_path is None:
        candidates = [
            Path(__file__).parent.parent / "personas",
            Path.home() / ".openclaw" / "workspace" / "skills" / "memory-inhabit" / "personas",
            Path.home() / ".openclaw" / "workspace-coding" / "skills" / "Memory-Inhabit" / "personas",
            Path.home() / ".openclaw" / "workspace-roleplay" / "skills" / "memory-inhabit" / "personas",
        ]
        for cand in candidates:
            if cand.exists():
                for sub in cand.iterdir():
                    if sub.is_dir() and (sub / "config.json").exists():
                        with open(sub / "config.json") as f:
                            return json.load(f)
                break
    return {}


def infer_voice_mood(profile):
    """根据 profile.json 推断音色类型"""
    keywords = profile.get("personality", {}).get("keywords", [])
    occupation = profile.get("occupation", "")
    age_estimate = infer_age(profile)
    
    # 合并关键词用于分析
    text = " ".join(keywords).lower()
    text += " " + occupation.lower()
    
    # 冷漠/霸道/强势 → 冷峻型
    cold_keywords = ["霸道", "冷漠", "强势", "冷酷", "严肃", "冷淡", "高冷", "独断"]
    # 温柔/善良/体贴 → 温柔型
    warm_keywords = ["温柔", "善良", "体贴", "温暖", "柔和", "关怀", "善解"]
    # 阳光/开朗/活泼 → 阳光型
    sunny_keywords = ["开朗", "阳光", "活泼", "乐观", "热情", "积极", "外向"]
    # 深沉/内敛/忧郁 → 抒情型
    deep_keywords = ["深沉", "内敛", "忧郁", "敏感", "细腻", "思考"]
    # 幽默/风趣 → 幽默型
    humor_keywords = ["幽默", "风趣", "诙谐", "搞笑"]
    
    mood_counts = {
        "cold": sum(1 for k in cold_keywords if k in text),
        "warm": sum(1 for k in warm_keywords if k in text),
        "sunny": sum(1 for k in sunny_keywords if k in text),
        "deep": sum(1 for k in deep_keywords if k in text),
        "humor": sum(1 for k in humor_keywords if k in text),
    }
    
    # 主导情绪
    dominant = max(mood_counts, key=mood_counts.get)
    
    # 年龄 + 情绪 → 音色
    if age_estimate >= 50:
        return "elder_humorous"
    elif age_estimate >= 35:
        # 中年
        if dominant == "cold":
            return "middle_reliable"
        elif dominant == "warm":
            return "middle_announcer"
        elif dominant == "sunny":
            return "middle_professional"
        else:
            return "middle_reliable"
    else:
        # 青年
        if dominant == "cold":
            return "young_unrestrained"
        elif dominant == "warm":
            return "young_gentle"
        elif dominant == "sunny":
            return "young_unrestrained"
        elif dominant == "deep":
            return "young_lyrical"
        elif dominant == "humor":
            return "young_pure"
        else:
            return "young_unrestrained"


def infer_age(profile):
    """推断年龄阶段"""
    # 尝试从 birth_year 推断
    birth_year = profile.get("birth_year")
    if birth_year:
        try:
            age = 2026 - int(birth_year)
            if age < 25:
                return 20
            elif age < 40:
                return 30
            else:
                return 50
        except:
            pass
    
    # 从职业/身份推断
    occupation = profile.get("occupation", "")
    relation = profile.get("relation", "")
    
    # 学生/少年/年轻人
    student_keywords = ["学生", "少年", "青年", "新手", "学员"]
    # 中年/资深
    mid_keywords = ["队长", "主管", "长官", "资深", "老练"]
    # 老年
    elder_keywords = ["爷爷", "老人", "长辈"]
    
    text = occupation + relation
    for k in elder_keywords:
        if k in text:
            return 60
    for k in mid_keywords:
        if k in text:
            return 40
    for k in student_keywords:
        if k in text:
            return 20
    
    return 30  # 默认青年


def get_minimax_api_key():
    """获取 MiniMax API Key，优先从环境变量，再从 models.json"""
    key = os.environ.get("MINIMAX_API_KEY", "")
    if key:
        return key
    
    models_path = Path.home() / ".openclaw" / "agents" / "coding" / "agent" / "models.json"
    if models_path.exists():
        try:
            with open(models_path) as f:
                data = json.load(f)
            return data.get("providers", {}).get("minimax", {}).get("apiKey", "")
        except Exception:
            pass
    return ""


async def generate_edge_tts(text, output_path, voice_key, rate="+0%", volume="+0%"):
    """使用 Edge-TTS 生成语音"""
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("edge-tts 未安装")
    
    voice_id = EDGE_VOICES.get(voice_key, EDGE_VOICES[DEFAULT_EDGE_VOICE])
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)
    await communicate.save(output_path)
    return output_path


async def list_edge_voices():
    """列出 Edge-TTS 可用语音"""
    if not EDGE_TTS_AVAILABLE:
        print("❌ edge-tts 未安装")
        return
    
    voices = await edge_tts.list_voices()
    zh_voices = [v for v in voices if v["Locale"].startswith("zh")]
    
    print("🎤 Edge-TTS 可用中文语音：\n")
    for v in zh_voices:
        short = v["ShortName"].replace("zh-CN-", "").replace("zh-TW-", "")
        gender = "♀" if v["Gender"] == "Female" else "♂"
        styles = ", ".join(v.get("StyleList", [])) or "通用"
        print(f"  {gender} {short:<30} {styles}")


def generate_minimax_tts(text, output_path, voice_key, speed=1, pitch=0, vol=1, emotion="calm"):
    """使用 MiniMax TTS 生成语音"""
    api_key = get_minimax_api_key()
    if not api_key:
        raise RuntimeError("MiniMax API Key 未配置")
    
    voice_id = MINIMAX_VOICES.get(voice_key, MINIMAX_VOICES[DEFAULT_MINIMAX_VOICE])
    
    payload = {
        "model": "speech-2.8-hd",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "pitch": pitch,
            "vol": vol,
            "emotion": emotion,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
        "output_format": "hex",
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    resp = requests.post(MINIMAX_API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    
    data = resp.json()
    audio_hex = data.get("data", {}).get("audio", "")
    if not audio_hex:
        raise RuntimeError(f"MiniMax TTS 失败: {data.get('base_resp', {}).get('status_msg', 'unknown')}")
    
    audio_bytes = bytes.fromhex(audio_hex)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Memory-Inhabit TTS（智能匹配版）")
    parser.add_argument("text", nargs="?", help="要转换的文字")
    parser.add_argument("-o", "--output", default="/tmp/mi_voice.mp3", help="输出文件路径")
    parser.add_argument("-p", "--provider", choices=["edge", "minimax"], default=None,
                        help="TTS 提供者（默认从 config.json 读取）")
    parser.add_argument("--voice-key", default=None, help="强制指定音色 key")
    parser.add_argument("-r", "--rate", default="+0%", help="语速调整（仅 edge）")
    parser.add_argument("--volume", default="+0%", help="音量调整（仅 edge）")
    parser.add_argument("--emotion", default="calm", help="情感（minimax：happy/sad/calm）")
    parser.add_argument("--persona", default=None, help="指定角色目录路径")
    parser.add_argument("--list-voices", action="store_true", help="列出可用音色")
    parser.add_argument("--preview", action="store_true", help="预览音色匹配结果")
    
    args = parser.parse_args()
    
    # 加载 profile 和 config
    profile = load_profile(args.persona)
    config = load_config(args.persona)
    
    if args.list_voices:
        print("📋 MiniMax 音色库：")
        for k, v in MINIMAX_VOICES.items():
            print(f"  {k}: {v}")
        print()
        if EDGE_TTS_AVAILABLE:
            asyncio.run(list_edge_voices())
        else:
            print("⚠️ Edge-TTS 未安装")
        return
    
    if args.preview:
        mood = infer_voice_mood(profile)
        age = infer_age(profile)
        print(f"👤 角色: {profile.get('name', '未知')}")
        print(f"📅 推断年龄阶段: {age}")
        print(f"🎭 推断音色类型: {mood}")
        print(f"🔊 推荐 MiniMax 音色: {MINIMAX_VOICES.get(mood, DEFAULT_MINIMAX_VOICE)}")
        edge_key = EDGE_VOICE_MOOD.get(mood, DEFAULT_EDGE_VOICE)
        print(f"🔊 推荐 Edge-TTS 音色: {EDGE_VOICES.get(edge_key, EDGE_VOICES[DEFAULT_EDGE_VOICE])}")
        return
    
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    # 确定 provider
    provider = args.provider or config.get("tts_provider", "minimax")
    
    # 确定音色 key
    if args.voice_key:
        voice_key = args.voice_key
    else:
        voice_key = infer_voice_mood(profile)
    
    try:
        if provider == "minimax":
            emotion = {"happy": "happy", "sad": "sad", "calm": "calm", "angry": "angry"}.get(args.emotion, "calm")
            generate_minimax_tts(args.text, args.output, voice_key, emotion=emotion)
            print(f"✅ MiniMax TTS 已生成: {args.output}")
            print(f"   音色: {MINIMAX_VOICES.get(voice_key, voice_key)}")
        else:
            if not EDGE_TTS_AVAILABLE:
                print("⚠️ edge-tts 未安装，切换到 minimax...")
                generate_minimax_tts(args.text, args.output, voice_key)
                print(f"✅ MiniMax TTS（备用）已生成: {args.output}")
                return
            edge_key = EDGE_VOICE_MOOD.get(voice_key, DEFAULT_EDGE_VOICE)
            asyncio.run(generate_edge_tts(args.text, args.output, edge_key, args.rate, args.volume))
            print(f"✅ Edge-TTS 已生成: {args.output}")
            print(f"   音色: {EDGE_VOICES.get(edge_key, edge_key)}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()