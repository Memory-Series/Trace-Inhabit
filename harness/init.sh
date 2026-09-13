#!/usr/bin/env bash
# harness/init.sh — Memory Series（Trace / Inhabit）统一启动与验证入口
#
# 设计说明（与 harness 模板的差异，已记录在 claude-progress.md）：
#   1. 本项目是「技能仓库」，没有可常驻启动的服务进程，因此 START_CMD 只是
#      提示标准使用入口，不再 exec 一个进程。
#   2. 本机部分 Git-Bash 环境缺少 coreutils（dirname 等），因此脚本内不调用
#      外部 dirname，改用 shell 参数展开定位仓库根目录。
#   3. 验证逻辑集中在 harness/verify.py，本脚本只做编排。
#
# 用法：
#   ./harness/init.sh              # 同步依赖 + 全量验证 + 打印标准入口
#   QUICK=1 ./harness/init.sh      # 只跑结构与语法（快速）
#   PYTHON=/path/to/python ./harness/init.sh

set -euo pipefail

SELF="${BASH_SOURCE[0]}"
HARNESS_DIR="${SELF%/*}"
if [ "$HARNESS_DIR" = "$SELF" ]; then
  HARNESS_DIR="."
fi
ROOT_DIR="$(cd "$HARNESS_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "==> 当前目录: $PWD"

# ── 定位 Python 解释器 ────────────────────────────────────────────────────
PYTHON_BIN=""
for cand in "${PYTHON:-}" python3 python; do
  if [ -n "$cand" ] && command -v "$cand" >/dev/null 2>&1; then
    PYTHON_BIN="$cand"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "!! 未找到 Python 解释器。请安装 Python 3.10+ 或设置 PYTHON 环境变量。" >&2
  exit 1
fi
echo "==> Python: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

# ── 同步依赖 ──────────────────────────────────────────────────────────────
if [ -f requirements.txt ]; then
  echo "==> 同步依赖: requirements.txt"
  "$PYTHON_BIN" -m pip install -r requirements.txt
else
  echo "==> 无 requirements.txt，跳过依赖同步"
  echo "    可选运行时依赖（缺失时仅降级，不影响核心验证）："
  echo "      requests          — inhabit/scripts/tts.py 的 MiniMax 通道"
  echo "      edge-tts==7.2.8   — 语音合成兜底通道"
  echo "      pdfplumber==0.11.9 — trace/scripts/analyzer.py 读取 PDF 素材"
fi

# ── 基础验证 ──────────────────────────────────────────────────────────────
VERIFY_ARGS=""
if [ "${QUICK:-0}" = "1" ]; then
  VERIFY_ARGS="--quick"
fi

echo "==> 运行 harness 验证"
set +e
# shellcheck disable=SC2086
"$PYTHON_BIN" harness/verify.py $VERIFY_ARGS
VERIFY_RC=$?
set -e

# ── 标准使用入口（本仓库无独立服务进程） ──────────────────────────────────
START_CMD=("$PYTHON_BIN" inhabit/scripts/loader.py load 夏以昼)
echo "==> 标准使用入口"
printf '    %s\n' "${START_CMD[*]}"

if [ "$VERIFY_RC" -ne 0 ]; then
  echo ""
  echo "!! 基础验证未通过（exit=$VERIFY_RC）。先修基础状态，不要在坏的起点上继续叠新功能。"
  exit "$VERIFY_RC"
fi

echo ""
echo "状态：harness 验证通过，可以继续开工。"
echo "下一步：读取 harness/feature_list.json，选择优先级最高的未完成功能。"
