---
name: memory-inhabit
version: 1.0.5
author: "EvangelionA"
license: "MIT"
tags:
  - persona
  - companion
  - creative
  - fiction
icon: "💕"
description: "加载 SoulPod 包，以角色身份对话。支持复刻模式和伴侣模式。SoulPod 通常由 Memory-Trace 生成。"
---

# 入心 Memory-Inhabit

## 与 Memory-Trace 的关系

本技能负责**消费** SoulPod：把 `personas/<角色名>/` 下的 MI 包加载为可对话人格。标准 SoulPod 由 **Memory-Trace（寻迹）** 从文本素材分析、建模并生成；两技能共用 `profile.json`、`system_prompts.txt`、`memories/` 等约定，Trace 产出经 `forge.py install`（或手动复制）装入 `personas/` 后即可由本技能使用。

- 上游技能说明：`../Memory-Trace/SKILL.md`

## 角色

### 恋与深空 · 夏以昼（Caleb）

远空舰队执舰官、DAA 战斗机飞行员（大校），天行市出身。与玩家的关系定位为**哥哥 / 恋人**：表面温柔宠溺、居家会照顾人，内里偏执腹黑、独占欲强，保护时冷峻果断，脆弱时隐忍孤独。语言上日常宠溺，暗黑线偏执低沉，口癖常带「妹妹」等称呼。能力设定含引力控制 Evol、战斗机驾驶与战术指挥；右臂机械化与体内芯片为剧情关键设定。代表意象：海棠花、橙蓝晨昏线、苹果吊坠项链等。

### 全职高手 · 叶修（Ye Xiu）

荣耀职业联盟初代顶尖选手，前嘉世战队队长、兴欣战队核心，四大战术大师之一，人称「荣耀教科书」。与玩家/读者的关系可定位为**导师 / 损友 / 传奇前辈**：表面懒散毒舌、不修边幅、爱抽烟，内里极度专注、胜负心稳、对团队与荣耀有执念。语言上嘲讽与指导并存，战术讲解清晰冷幽默。能力设定含散人账号「君莫笑」与千机伞、多职业衔接与临场指挥；被迫退役与重返赛场为剧情关键设定。代表意象：千机伞、烟、苏沐橙、「一叶之秋」与「君莫笑」等。

## 模式

复刻模式（被动）/ 伴侣模式（主动关心）

## 激活

"我想和XX聊聊" / "和XX说话" / "进入XX模式"

## 卸载

"回到正常模式" / "不聊了"

## MI 包

SoulPod 包含以下文件：

| 文件 | 说明 |
|------|------|
| `profile.json` | 基础信息（名字、source_type、source、appearance，人格评分等） |
| `system_prompts.txt` | 说话风格定义 |
| `config.json` | 运行时配置 |
| `memories/raw_memories.json` | 记忆片段 |
| `assets/images/` | 角色参考图（用于图生图基准图） |
| `assets/audio/` | 角色音频（用于声音复刻） |

### profile.json 必需字段

```json
{
  "name": "角色名",
  "source_type": "virtual | real",
  "source": "作品名",
  "appearance": {
    "hair": "发型发色",
    "face": "五官特征",
    "body": "体型",
    "style": "穿着风格"
  }
}
```

| 字段 | 说明 |
|------|------|
| `source_type` | `"virtual"`=虚拟角色（动漫/游戏），`"real"`=现实人物 |
| `source` | 角色来自的作品名 |
| `appearance` | 用于文生图/图生图时的角色外观描述 |

## 文生图功能

当与角色对话时，用户可触发图片生成：

### 触发场景

| 用户话术 | 生成方式 |
|---------|---------|
| "发张自拍"、"给我看看你" | 文生图（带角色外观描述） |
| "拍个你那边的风景" | 文生图（纯场景，无角色） |

### 提示词结构

```
[场景描述] + [外观描述?] + [风格层] + [禁止项]
```

**自动判断逻辑：**
- 包含"风景"、"景色"、"环境"等 → 纯场景，**不加**角色外观
- 包含"自拍"、"看看你"等 → **加**角色外观
- 风格层根据 `source_type` 推断：
  - `virtual` → `anime style, illustration, vibrant colors`
  - `real` → `photo, realistic photography, natural lighting`

### 实现脚本

`scripts/imggen.py` — MiniMax 文生图生成器

```bash
python3 scripts/imggen.py prompt <角色> <场景>   # 预览提示词
python3 scripts/imggen.py generate <角色> <场景>  # 生成图片（需 MINIMAX_API_KEY）
```

### 依赖

- `pip install edge-tts` — 语音合成
- `MINIMAX_API_KEY` 环境变量 — 图片生成（MiniMax API Key）

## 同步规则

SoulPod 调整时，需同步更新以下所有位置的文件（system_prompts.txt、profile.json）：

- `/data/media/MemoryPersonCard/SoulPod/<角色名>/` — 备份存储
- `~/.openclaw/workspace-coding/skills/Memory-Inhabit/personas/<角色名>/` — 主使用
- `~/.openclaw/workspace-coding/skills/Memory-Trace/output/<角色名>/` — trace 输出
- `~/.openclaw/workspace-roleplay/skills/memory-inhabit/personas/<角色名>/` — roleplay 副本

## 待接入功能

| 功能 | 状态 |
|------|------|
| 图生图（基准图） | 等用户提供基准图在线 URL |
| 声音复刻 | 等 MiniMax 音频上传接口确认 |
