#!/usr/bin/env python3
"""
Memory-Inhabit Image Generator — 文生图模块

通过 MiniMax API 生成图片，支持：
- 风景/场景图（文生图）
- 角色自拍（文生图版，等基准图做好后接入图生图）

用法：
  python3 imggen.py generate <persona> <scene_description> [--style virtual|real]
  python3 imggen.py prompt <persona> <scene_description>
  python3 imggen.py test <persona>
"""

import json
import os
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

PERSONAS_DIR = Path(__file__).parent.parent / "personas"
EXTERNAL_PERSONAS_DIR = Path.home() / ".openclaw" / "personas"

# MiniMax API 配置
MINIMAX_API_URL = "https://api.minimaxi.com/v1/image_generation"
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

# 风格层模板（已含禁止项）
STYLE_TEMPLATES = {
    "virtual": "anime style, illustration, vibrant colors, soft lighting, no watermark, no text, no logo, no AI artifacts",
    "real": "photo, realistic photography, natural lighting, no watermark, no text, no logo, no AI artifacts"
}

# 禁止项
FORBIDDEN = "no watermark, no text, no logo, no AI artifacts"


def resolve_persona_dir(persona_name):
    """找到人格包目录"""
    local = PERSONAS_DIR / persona_name
    external = EXTERNAL_PERSONAS_DIR / persona_name
    if local.exists():
        return local
    if external.exists():
        return external
    return None


def load_profile(persona_name):
    """加载 profile.json"""
    persona_dir = resolve_persona_dir(persona_name)
    if not persona_dir:
        raise FileNotFoundError(f"Persona '{persona_name}' not found")
    profile_path = persona_dir / "profile.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"profile.json not found for '{persona_name}'")
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def infer_source_type(profile):
    """从 profile.json 推断角色类型"""
    # 优先用 source_type 字段
    if profile.get("source_type"):
        return profile["source_type"]

    # 从 relation 判断
    relation = profile.get("relation", "")
    if "真实" in relation or "real" in relation.lower():
        return "real"

    # 有 source 字段 → 虚拟角色
    if profile.get("source"):
        return "virtual"

    # 从职业判断（游戏/小说角色 → 虚拟）
    occupation = profile.get("occupation", "")
    if occupation in ("荣耀职业选手",):
        return "virtual"

    # 默认虚拟
    return "virtual"


def infer_character_appearance(profile):
    """从 profile.json 提取角色外观描述"""
    appearance = profile.get("appearance", {})
    name = profile.get("name", "")

    parts = []

    # 性别（根据名字简单判断，中文语境）
    gender_hint = profile.get("gender", "")
    if not gender_hint:
        # 夏以昼 → male, 叶修 → male
        gender_hint = "male"

    # 发型发色
    hair = appearance.get("hair", "")
    if hair:
        parts.append(hair)

    # 五官/脸
    face = appearance.get("face", "")
    if face:
        parts.append(face)

    # 穿着风格
    style = appearance.get("style", "")
    if style:
        parts.append(style)

    # 体型
    body = appearance.get("body", "")
    if body:
        parts.append(body)

    return ", ".join(parts) if parts else ""


def build_prompt(profile, scene_description, source_type, include_appearance=False):
    """
    构建完整的文生图提示词

    结构：[场景描述] + [外观描述?] + [风格层] + [禁止项]
    - include_appearance=True 时才加入角色外观描述（自拍场景）
    - include_appearance=False 时只生成纯风景/场景图
    """
    parts = []

    # 场景描述
    if scene_description:
        parts.append(scene_description)

    # 外观描述（仅自拍等角色场景时加入）
    if include_appearance:
        appearance = infer_character_appearance(profile)
        if appearance:
            parts.append(appearance)

    # 风格层（已含禁止项）
    style_str = STYLE_TEMPLATES.get(source_type, STYLE_TEMPLATES["real"])
    parts.append(style_str)

    return ", ".join(parts)


def detect_include_appearance(scene_description):
    """
    根据场景描述判断是否需要包含角色外观

    包含自拍/人像类关键词 → 需要外观
    纯风景/场景类关键词 → 不需要外观
    """
    if not scene_description:
        return False

    # 自拍/人像类关键词
    selfie_keywords = ["自拍", "selfie", "人像", "portrait", "照片", "看看你", "给我看"]
    # 纯风景/场景类关键词
    scene_keywords = ["风景", "景色", "scene", "landscape", "view", "环境", "训练室", "房间", "窗外", "街道", "城市", "咖啡厅", " outdoor", " indoor"]

    desc_lower = scene_description.lower()

    # 先检查是否是纯风景
    is_scene = any(kw in desc_lower for kw in ["风景", "景色", "scene", "landscape", "view", "环境", "窗外", "街道", "城市"])
    has_selfie_kw = any(kw in desc_lower for kw in selfie_keywords)

    if has_selfie_kw:
        return True
    if is_scene:
        return False

    # 默认不含外观（纯风景优先）
    return False


def generate_image(prompt, model="image-01", aspect_ratio="16:9"):
    """
    调用 MiniMax 图文生成 API

    Returns: (image_url, revised_prompt)
    """
    if not MINIMAX_API_KEY:
        raise ValueError("MINIMAX_API_KEY not set in environment")

    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "n": 1
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MINIMAX_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"MiniMax API error {e.code}: {error_body}")

    # 解析返回 — MiniMax 图生图返回结构
    # 成功: { "data": { "image_urls": ["..."] }, "base_resp": { "status_code": 0 } }
    # 失败: { "base_resp": { "status_code": 非0, "status_msg": "..." } }
    base_resp = result.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        raise RuntimeError(f"MiniMax API error: {base_resp.get('status_msg', 'unknown')}")

    data = result.get("data", {})
    image_urls = data.get("image_urls", [])
    if not image_urls:
        raise RuntimeError(f"No image URL in response: {result}")

    image_url = image_urls[0]
    # MiniMax 图生图一般不返回 revised_prompt，取空字符串
    revised_prompt = prompt
    return image_url, revised_prompt


def download_image(url, save_dir=None):
    """
    下载图片到临时目录

    Returns: 本地文件路径
    """
    if save_dir is None:
        save_dir = tempfile.gettempdir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mi_imggen_{timestamp}.jpg"
    save_path = Path(save_dir) / filename

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(save_path, "wb") as out:
                out.write(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to download image: {e.code}")

    return str(save_path)


def cleanup_image(path):
    """删除临时图片"""
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def generate_and_save(persona_name, scene_description, aspect_ratio="16:9"):
    """
    完整流程：构建提示词 → 生成 → 下载 → 返回本地路径
    """
    # 1. 加载 profile
    profile = load_profile(persona_name)

    # 2. 推断风格
    source_type = infer_source_type(profile)

    # 3. 构建提示词
    include_app = detect_include_appearance(scene_description)
    prompt = build_prompt(profile, scene_description, source_type, include_appearance=include_app)

    # 4. 生成
    image_url, revised_prompt = generate_image(prompt, aspect_ratio=aspect_ratio)

    # 5. 下载
    local_path = download_image(image_url)

    return {
        "persona": persona_name,
        "source_type": source_type,
        "original_prompt": prompt,
        "revised_prompt": revised_prompt,
        "image_url": image_url,
        "local_path": local_path
    }


def cmd_generate(persona, scene, style_override=None):
    """generate 命令"""
    if not MINIMAX_API_KEY:
        print("Error: MINIMAX_API_KEY not set", file=sys.stderr)
        print("Set it with: export MINIMAX_API_KEY=your_key", file=sys.stderr)
        sys.exit(1)

    profile = load_profile(persona)
    source_type = style_override or infer_source_type(profile)
    include_app = detect_include_appearance(scene)
    prompt = build_prompt(profile, scene, source_type, include_appearance=include_app)

    print(f"[{persona}] generating image...")
    print(f"source_type: {source_type}")
    print(f"include_appearance: {include_app}")
    print(f"prompt: {prompt}")

    image_url, revised_prompt = generate_image(prompt)
    print(f"image_url: {image_url}")

    local_path = download_image(image_url)
    print(f"saved to: {local_path}")

    return local_path


def cmd_prompt(persona, scene):
    """prompt 命令：只输出提示词，不生成"""
    profile = load_profile(persona)
    source_type = infer_source_type(profile)
    include_app = detect_include_appearance(scene)
    prompt = build_prompt(profile, scene, source_type, include_appearance=include_app)
    print(f"[{persona}] prompt preview:")
    print(f"source_type: {source_type}")
    print(f"include_appearance: {include_app}")
    print(f"prompt: {prompt}")


def cmd_test(persona):
    """test 命令：用默认场景测试"""
    scenes = [
        "Indoor gaming training room, multiple computers on desk, Blue Light shielding cover visible",
        "Cozy cafe corner, warm afternoon sunlight, scattered books on table"
    ]
    for scene in scenes:
        print(f"\n{'='*50}")
        cmd_prompt(persona, scene)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "generate":
        if len(sys.argv) < 4:
            print("Usage: imggen.py generate <persona> <scene_description>")
            sys.exit(1)
        persona = sys.argv[2]
        scene = sys.argv[3]
        style_override = None
        for i, arg in enumerate(sys.argv):
            if arg == "--style" and i + 1 < len(sys.argv):
                style_override = sys.argv[i + 1]
        cmd_generate(persona, scene, style_override)

    elif cmd == "prompt":
        if len(sys.argv) < 4:
            print("Usage: imggen.py prompt <persona> <scene_description>")
            sys.exit(1)
        persona = sys.argv[2]
        scene = sys.argv[3]
        cmd_prompt(persona, scene)

    elif cmd == "test":
        persona = sys.argv[2] if len(sys.argv) > 2 else "叶修"
        cmd_test(persona)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
