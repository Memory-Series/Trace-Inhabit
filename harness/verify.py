#!/usr/bin/env python3
"""
harness/verify.py — Memory Series（Trace / Inhabit）harness 统一验证入口

这是 init.sh 背后的真实验证逻辑。它回答一个问题：
「当前仓库是否处于可以继续安全开工的状态？」

用法：
  python harness/verify.py            # 全量验证
  python harness/verify.py --quick    # 只跑结构与语法（快速）
  python harness/verify.py --json      # 机器可读输出

退出码：
  0  无 FAIL
  1  存在 FAIL

约定（详见 harness/AGENTS.md）：
  - verify.py 是验证规则的唯一实现处。修改验证规则必须改这个文件并记录在 claude-progress.md。
  - 不允许为了让结果变绿而放宽本文件的规则；遇到真实失败应修数据或修代码。
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Windows 控制台默认 GBK，强制 UTF-8 以正确输出中文
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

FAIL, WARN, INFO, PASS = "FAIL", "WARN", "INFO", "PASS"

# 项目结构必需文件（相对仓库根）
REQUIRED_FILES = [
    "CLAUDE.md",
    "README.md",
    "trace/SKILL.md",
    "inhabit/SKILL.md",
    "harness/AGENTS.md",
    "harness/feature_list.json",
    "harness/claude-progress.md",
    "harness/init.sh",
    "harness/verify.py",
]

# 语义层脚本（两个技能的运行时）
SCRIPT_DIRS = {
    "trace/scripts": ["analyzer", "forge"],
    "inhabit/scripts": ["checker", "cleanup", "deploy", "diary",
                        "imggen", "loader", "memory", "sender", "tts"],
}

# SoulPod 包必需 / 建议文件
POD_REQUIRED = [
    "profile.json",
    "system_prompts.txt",
    "config.json",
    "memories/raw_memories.json",
]
POD_EXPECTED = [
    "prompt/story_baseline.txt",
    "prompt/universal_prompt.txt",
]

# profile.json 必需字段（依据 inhabit/SKILL.md「profile.json 必需字段」）
PROFILE_REQUIRED = ["name", "source_type", "source", "gender", "appearance"]

# 外部可选依赖：缺失只报警告，不算 FAIL
OPTIONAL_DEPS = {"requests", "edge_tts", "pdfplumber"}

# 敏感信息模式
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "疑似 sk- 开头的 API Key"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]{30,}"), "疑似硬编码 Bearer Token"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"'\s]{16,}[\"']"),
     "疑似硬编码 key/secret"),
]

LARGE_FILE_BYTES = 5 * 1024 * 1024


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, check, message, detail=None):
        self.items.append({"level": level, "check": check,
                           "message": message, "detail": detail or []})

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)

    def ok(self):
        return self.count(FAIL) == 0


def run(cmd, cwd=None, timeout=90):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 1, f"{type(e).__name__}: {e}"


def git_lines(args):
    code, out = run(["git", *args], cwd=str(ROOT))
    if code != 0:
        return None
    return [l for l in out.splitlines() if l.strip()]


TEXT_EXT = {".json", ".txt", ".md", ".py", ".sh", ".yaml", ".yml", ".gitignore"}


def sha256(path):
    """比对用内容哈希。

    本机 git 配置为 `core.autocrlf=true`，工作区文本文件的行尾已被 git 转换
    （同一份内容可能呈现为 CRLF 或 LF）。直接按字节比对会产生大量假差异，
    因此文本文件先做 CRLF→LF 归一化后再哈希；二进制文件按原字节哈希。
    """
    data = Path(path).read_bytes()
    if path.suffix.lower() in TEXT_EXT or path.name == ".gitignore":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


# ── 检查项 ────────────────────────────────────────────────────────────────

def check_structure(r):
    missing = [f for f in REQUIRED_FILES if not (ROOT / f).exists()]
    if missing:
        r.add(FAIL, "结构/必需文件", f"缺少 {len(missing)} 个必需文件", missing)
    else:
        r.add(PASS, "结构/必需文件", f"{len(REQUIRED_FILES)} 个必需文件齐全")

    for base in ("trace/scripts", "inhabit/scripts"):
        d = ROOT / base
        if not d.is_dir():
            r.add(FAIL, "结构/脚本目录", f"{base} 目录不存在")
    for base in ("trace/output", "inhabit/personas"):
        if not (ROOT / base).is_dir():
            r.add(WARN, "结构/数据目录", f"{base} 目录不存在")


def check_python_syntax(r):
    bad = []
    files = [p for p in ROOT.rglob("*.py")
             if "__pycache__" not in p.parts]
    for p in files:
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except Exception as e:  # noqa: BLE001
            bad.append(f"{p.relative_to(ROOT)}: {type(e).__name__}: {e}")
    if bad:
        r.add(FAIL, "Python/语法", f"{len(bad)} 个文件语法错误", bad)
    else:
        r.add(PASS, "Python/语法", f"{len(files)} 个 .py 文件语法通过")


def check_null_bytes(r):
    """检测被写入 NUL 字节的文本文件（编码损坏的典型症状）"""
    bad = []
    for ext in ("*.py", "*.md", "*.json", "*.txt", "*.sh"):
        for p in ROOT.rglob(ext):
            if ".git" in p.parts or "__pycache__" in p.parts:
                continue
            try:
                head = p.read_bytes()[:65536]
            except OSError:
                continue
            if b"\x00" in head:
                bad.append(str(p.relative_to(ROOT)))
    if bad:
        r.add(FAIL, "文本/编码", f"{len(bad)} 个文本文件含 NUL 字节", bad)
    else:
        r.add(PASS, "文本/编码", "未发现 NUL 字节污染")


def check_imports(r):
    for rel, mods in SCRIPT_DIRS.items():
        d = ROOT / rel
        if not d.is_dir():
            continue
        hard, soft = [], []
        for m in mods:
            code, out = run([sys.executable, "-c", f"import {m}"], cwd=str(d))
            if code == 0:
                continue
            if any(dep in out for dep in OPTIONAL_DEPS) and "ModuleNotFoundError" in out:
                missing = re.findall(r"No module named '([^']+)'", out)
                soft.append(f"{m}: 缺依赖 {'/'.join(missing)}")
            else:
                tail = out.strip().splitlines()[-1] if out.strip() else "unknown"
                hard.append(f"{m}: {tail}")
        if hard:
            r.add(FAIL, f"导入/{rel}", f"{len(hard)} 个模块导入失败", hard)
        if soft:
            r.add(WARN, f"导入/{rel}", f"{len(soft)} 个模块缺可选依赖", soft)
        if not hard and not soft:
            r.add(PASS, f"导入/{rel}", f"{len(mods)} 个模块导入通过")


def check_cli_smoke(r):
    cases = [
        ("trace/scripts", ["forge.py", "list"], "forge list"),
        ("inhabit/scripts", ["loader.py", "list"], "loader list"),
    ]
    bad = []
    for rel, argv, label in cases:
        d = ROOT / rel
        if not (d / argv[0]).exists():
            bad.append(f"{label}: 脚本缺失")
            continue
        code, out = run([sys.executable, *argv], cwd=str(d))
        if code != 0:
            tail = out.strip().splitlines()[-1] if out.strip() else "no output"
            bad.append(f"{label}: exit={code} {tail}")
    if bad:
        r.add(FAIL, "冒烟/CLI", f"{len(bad)} 个入口无法运行", bad)
    else:
        r.add(PASS, "冒烟/CLI", f"{len(cases)} 个命令行入口可运行")


def collect_pods(base):
    d = ROOT / base
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_dir())


def check_pods(r):
    for base in ("inhabit/personas", "trace/output"):
        for pod in collect_pods(base):
            rel = f"{base}/{pod.name}"
            files = [p.relative_to(pod).as_posix()
                     for p in pod.rglob("*") if p.is_file()]
            if not files:
                r.add(FAIL, "SoulPod/完整性", f"{rel} 是空目录（残缺包不应提交）")
                continue
            missing = [f for f in POD_REQUIRED if f not in files]
            expected_missing = [f for f in POD_EXPECTED if f not in files]
            if missing:
                r.add(FAIL, "SoulPod/完整性",
                      f"{rel} 缺少必需文件", [f"缺 {m}" for m in missing])
            elif expected_missing:
                r.add(WARN, "SoulPod/完整性",
                      f"{rel} 缺建议文件", [f"缺 {m}" for m in expected_missing])
            else:
                r.add(PASS, "SoulPod/完整性", f"{rel} 文件齐全")

            # JSON 可解析
            for jf in ("profile.json", "config.json", "memories/raw_memories.json"):
                if jf not in files:
                    continue
                try:
                    json.loads((pod / jf).read_text(encoding="utf-8"))
                except Exception as e:  # noqa: BLE001
                    r.add(FAIL, "SoulPod/JSON", f"{rel}/{jf} 解析失败: {e}")


def check_profile_fields(r):
    for base in ("inhabit/personas", "trace/output"):
        for pod in collect_pods(base):
            p = pod / "profile.json"
            if not p.exists():
                continue
            rel = f"{base}/{pod.name}"
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            missing = [f for f in PROFILE_REQUIRED if not data.get(f)]
            app = data.get("appearance")
            mismatch = (isinstance(app, dict) and app.get("gender")
                        and data.get("gender") and app["gender"] != data["gender"])
            if missing or mismatch:
                detail = [f"缺字段 {m}" for m in missing]
                if "gender" in missing:
                    detail.append("gender 缺失会导致 tts.py / imggen.py 回退默认 male")
                if mismatch:
                    detail.append(
                        f"gender 冗余不一致：顶层 {data['gender']!r} vs "
                        f"appearance.gender {app['gender']!r}")
                r.add(FAIL if missing else WARN,
                      "SoulPod/profile 字段",
                      (f"{rel} profile.json 字段不完整" if missing
                       else f"{rel} profile.json gender 冗余字段不一致"),
                      detail)
            else:
                r.add(PASS, "SoulPod/profile 字段", f"{rel} 必需字段齐全")


# output↔personas 同步豁免规则
# 仅豁免「存在性」差异：以下路径允许只存在于 personas 侧。
# 理由：这些是运行时媒体资源（参考图 / 动画帧 / 音频），由 imggen.py 等脚本在
# personas 下就地生成或安装，要求同一份二进制在 output 再存一份会让仓库体积翻倍。
# 语义文件（profile.json / config.json / system_prompts.txt / memories/ / prompt/ /
# assets/source.txt）不在豁免范围内，必须内容一致。
# 注意：豁免只针对「仅 personas 有」；若媒体只存在于 output 侧（说明 install 未完成），
# 或两侧同名媒体内容不同，仍会报出。
SYNC_ASSET_ALLOW_RE = re.compile(
    r"^assets/.+\.(png|jpe?g|gif|webp|bmp|ico|svg|mp3|wav|ogg|m4a|flac|mp4|webm|mov|bin)$",
    re.I)


def check_output_personas_sync(r):
    pairs = []
    waived = 0
    personas = {p.name: p for p in collect_pods("inhabit/personas")}
    outputs = {p.name: p for p in collect_pods("trace/output")}
    for name in sorted(set(personas) & set(outputs)):
        a, b = outputs[name], personas[name]
        fa = {p.relative_to(a).as_posix(): p for p in a.rglob("*") if p.is_file()}
        fb = {p.relative_to(b).as_posix(): p for p in b.rglob("*") if p.is_file()}
        diffs = []
        for k in sorted(set(fa) & set(fb)):
            if sha256(fa[k]) != sha256(fb[k]):
                diffs.append(k)
        only_out = sorted(set(fa) - set(fb))
        only_per = sorted(set(fb) - set(fa))
        # 豁免：仅 personas 侧存在的媒体资源
        kept_only_per = []
        for k in only_per:
            if SYNC_ASSET_ALLOW_RE.match(k):
                waived += 1
            else:
                kept_only_per.append(k)
        only_per = kept_only_per
        if diffs or only_out or only_per:
            detail = ([f"内容不同: {d}" for d in diffs]
                      + [f"仅 output 有: {d}" for d in only_out]
                      + [f"仅 personas 有: {d}" for d in only_per])
            pairs.append((name, detail))
    if pairs:
        for name, detail in pairs:
            r.add(WARN, "同步/output↔personas",
                  f"{name} 的 output 与 personas 不一致（共 {len(detail)} 处）",
                  detail[:12])
    else:
        r.add(PASS, "同步/output↔personas",
              f"已比对角色两边一致（豁免 personas 侧独有媒体资源 {waived} 个）")


def check_secrets(r):
    hits = []
    # 扫描「可能被提交的文件」：已跟踪 + 未跟踪但未被 gitignore
    tracked = git_lines(["ls-files"])
    untracked = git_lines(["ls-files", "--others", "--exclude-standard"])
    if tracked is None:
        r.add(INFO, "安全/敏感信息", "无法读取 git 文件列表，已跳过")
        return
    candidates = sorted(set(tracked) | set(untracked or []))
    for rel in candidates:
        if rel.endswith(".env") or "/.env" in rel or rel.startswith(".env"):
            hits.append(f"{rel}: 疑似 .env 被跟踪")
            continue
        p = ROOT / rel
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        if p.suffix.lower() not in (".py", ".md", ".json", ".txt", ".sh", ".yaml", ".yml"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, label in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(f"{rel}: {label}")
    if hits:
        r.add(FAIL, "安全/敏感信息", f"{len(hits)} 处疑似敏感信息", hits)
    else:
        r.add(PASS, "安全/敏感信息", f"{len(candidates)} 个待提交文件未发现硬编码凭据")


def check_git_hygiene(r):
    tracked = git_lines(["ls-files"])
    if tracked is None:
        r.add(INFO, "Git/卫生", "无法读取 git 跟踪列表，已跳过")
        return

    bad_cache = [f for f in tracked if "__pycache__" in f or f.endswith((".pyc", ".pyo"))]
    bad_assets = [f for f in tracked
                  if re.search(r"origin/.*/assets/(images|audio)/", f)]
    bad_merged = [f for f in tracked if f.endswith("_merged_source.md")]
    bad_private = [f for f in tracked
                   if re.search(r"personas/[^/]+/memories/(diary|history)/", f)]

    for label, bad in (("缓存产物 __pycache__/*.pyc", bad_cache),
                       ("origin 下的二进制素材", bad_assets),
                       ("forge 本地合并产物 _merged_source.md", bad_merged),
                       ("私密日记/对话流水", bad_private)):
        if bad:
            r.add(FAIL, "Git/禁提交项", f"{label}: {len(bad)} 个文件被跟踪", bad[:10])
        else:
            r.add(PASS, "Git/禁提交项", f"{label}: 未被跟踪")

    large = []
    for rel in tracked:
        p = ROOT / rel
        if p.is_file() and p.stat().st_size > LARGE_FILE_BYTES:
            large.append(f"{rel} ({p.stat().st_size / 1048576:.1f} MB)")
    if large:
        r.add(WARN, "Git/大文件", f"{len(large)} 个被跟踪文件超过 5MB", large)
    else:
        r.add(PASS, "Git/大文件", "无被跟踪的超大文件")


def check_untracked(r):
    out = git_lines(["status", "--porcelain"])
    if out is None:
        return
    untracked = [l[3:].strip('"') for l in out if l.startswith("??")]
    if untracked:
        r.add(WARN, "Git/未跟踪", f"{len(untracked)} 项未跟踪内容需人工判断", untracked[:12])
    else:
        r.add(PASS, "Git/未跟踪", "工作区无未跟踪内容")


def check_harness(r):
    """harness 自身的完整性：feature_list 结构与状态合法性、模板占位符是否已实例化"""
    fl_path = ROOT / "harness" / "feature_list.json"
    if not fl_path.exists():
        r.add(FAIL, "Harness/完整性", "harness/feature_list.json 不存在")
        return
    try:
        fl = json.loads(fl_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        r.add(FAIL, "Harness/完整性", f"feature_list.json 解析失败: {e}")
        return

    feats = fl.get("features") or []
    if not feats:
        r.add(FAIL, "Harness/完整性", "feature_list.json 没有任何 feature")
        return

    legend = fl.get("status_legend") or {}
    need = ["id", "priority", "area", "title", "user_visible_behavior",
            "status", "verification", "evidence"]
    bad, in_progress, no_evidence = [], [], []
    ids = set()
    for f in feats:
        fid = f.get("id", "?")
        miss = [k for k in need if k not in f]
        if miss:
            bad.append(f"{fid}: 缺字段 {'/'.join(miss)}")
        if fid in ids:
            bad.append(f"{fid}: id 重复")
        ids.add(fid)
        if legend and f.get("status") not in legend:
            bad.append(f"{fid}: 非法 status {f.get('status')!r}")
        if f.get("status") == "in_progress":
            in_progress.append(fid)
        if f.get("status") == "passing" and not f.get("evidence"):
            no_evidence.append(fid)

    if bad:
        r.add(FAIL, "Harness/完整性", f"feature_list.json 有 {len(bad)} 处结构问题", bad)
    else:
        r.add(PASS, "Harness/完整性",
              f"feature_list.json 结构合法（{len(feats)} 个功能）")

    if len(in_progress) > 1:
        r.add(FAIL, "Harness/完整性",
              f"违反 single_active_feature：{len(in_progress)} 个 in_progress",
              in_progress)
    elif in_progress:
        r.add(PASS, "Harness/完整性", f"当前进行中功能：{in_progress[0]}")
    else:
        r.add(INFO, "Harness/完整性", "当前没有 in_progress 功能")

    if no_evidence:
        r.add(FAIL, "Harness/完整性",
              f"违反 passing_requires_evidence：{len(no_evidence)} 个 passing 功能无证据",
              no_evidence)

    # 模板占位符残留检测
    # 通用占位符：任何 harness 文件中出现都说明尚未实例化
    generic = ["替换成你的项目名", "YYYY-MM-DD", "按你的项目实际情况替换"]
    # init.sh 专属：模板默认的 Node 命令，说明 init.sh 还是未改的模板
    init_only = ["npm install", "npm test", "npm run dev"]
    leftover = []
    # 不扫描 verify.py 本身：它正是这些模式的定义处
    for name in ("AGENTS.md", "feature_list.json", "claude-progress.md",
                 "init.sh", "session-handoff.md"):
        p = ROOT / "harness" / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for ph in generic:
            if ph in text:
                leftover.append(f"{name}: 残留占位符 {ph!r}")
        if name == "init.sh":
            for ph in init_only:
                if ph in text:
                    leftover.append(f"{name}: 残留模板命令 {ph!r}")
    if leftover:
        r.add(WARN, "Harness/实例化", f"{len(leftover)} 处模板占位符未替换", leftover)
    else:
        r.add(PASS, "Harness/实例化", "所有占位符已替换为本项目内容")


# ── 主流程 ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Memory Series harness 验证入口")
    ap.add_argument("--quick", action="store_true", help="只跑结构与语法检查")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    r = Report()
    check_structure(r)
    check_python_syntax(r)
    check_null_bytes(r)
    check_harness(r)
    if not args.quick:
        check_imports(r)
        check_cli_smoke(r)
        check_pods(r)
        check_profile_fields(r)
        check_output_personas_sync(r)
        check_secrets(r)
        check_git_hygiene(r)
        check_untracked(r)

    if args.json:
        print(json.dumps({
            "root": str(ROOT),
            "summary": {lv: r.count(lv) for lv in (FAIL, WARN, INFO, PASS)},
            "items": r.items,
        }, ensure_ascii=False, indent=2))
    else:
        order = {FAIL: 0, WARN: 1, INFO: 2, PASS: 3}
        mark = {FAIL: "✗", WARN: "!", INFO: "i", PASS: "✓"}
        print(f"harness 验证 — {ROOT}")
        print("=" * 72)
        for item in sorted(r.items, key=lambda i: order[i["level"]]):
            print(f"  {mark[item['level']]} [{item['check']}] {item['message']}")
            for d in item["detail"]:
                print(f"      - {d}")
        print("=" * 72)
        print(f"结果：FAIL {r.count(FAIL)}   WARN {r.count(WARN)}   "
              f"PASS {r.count(PASS)}")
        if r.ok():
            print("状态：可以继续开工（无 FAIL）。")
        else:
            print("状态：存在 FAIL，先修基础状态，不要在坏的起点上继续叠新功能。")

    return 0 if r.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
