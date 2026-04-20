---
name: memory-trace
version: 1.0.5
author: "EvangelionA"
license: "MIT"
tags:
  - persona
  - creative
  - fiction
icon: "🧬"
description: "从小说、剧本、动漫素材中提取角色人格，生成 SoulPod 包。下游配合 Memory-Inhabit 加载对话。"
---

# 寻迹 Memory-Trace

## 与 Memory-Inhabit 的关系

本技能负责**生产** SoulPod：从素材完成角色识别，人格建模与记忆提取后写入 `output/<角色名>/`。生成包可被 **Memory-Inhabit（入心）** 直接加载；将包部署到 Inhabit 的 `personas/` 后，用户即可用「和 XX 聊聊」等话术进入角色对话。

- 下游技能说明：`../Memory-Inhabit/SKILL.md`

## 角色

### 恋与深空 · 夏以昼（Caleb）

远空舰队执舰官、DAA 战斗机飞行员（大校），天行市出身。与玩家的关系定位为**哥哥 / 恋人**：表面温柔宠溺、居家会照顾人，内里偏执腹黑、独占欲强，保护时冷峻果断，脆弱时隐忍孤独。语言上日常宠溺，暗黑线偏执低沉，口癖常带「妹妹」等称呼。能力设定含引力控制 Evol、战斗机驾驶与战术指挥；右臂机械化与体内芯片为剧情关键设定。代表意象：海棠花、橙蓝晨昏线、苹果吊坠项链等。

### 全职高手 · 叶修（Ye Xiu）

荣耀职业联盟初代顶尖选手，前嘉世战队队长、兴欣战队核心，四大战术大师之一，人称「荣耀教科书」。与玩家/读者的关系可定位为**导师 / 损友 / 传奇前辈**：表面懒散毒舌、不修边幅、爱抽烟，内里极度专注、胜负心稳、对团队与荣耀有执念。语言上嘲讽与指导并存，战术讲解清晰冷幽默。能力设定含散人账号「君莫笑」与千机伞、多职业衔接与临场指挥；被迫退役与重返赛场为剧情关键设定。代表意象：千机伞、烟，苏沐橙、「一叶之秋」与「君莫笑」等。

## 触发

复刻角色，分析人格，制作 SoulPod

## 工作流

当你说 **"帮我复刻XX"** 时，自动执行以下完整流程：

```
1. Web Search → 搜索角色文本资料 + 图片 + 音频
2. 保存文本素材 → /data/media/MemoryPersonCard/Origin/<游戏>/<角色名>/
3. 下载图片（3-5张）→ /data/media/MemoryPersonCard/Origin/<游戏>/<角色名>/assets/images/
4. 下载音频（2-3段）→ /data/media/MemoryPersonCard/Origin/<游戏>/<角色名>/assets/audio/
5. analyzer.py → 提取人格特征
6. forge.py create → 生成 SoulPod（包含 assets/images/ 和 assets/audio/）
7. forge.py install → 部署到 inhabit personas/
```

### 素材目录结构

```
/data/media/MemoryPersonCard/
├── Origin/                          # 源素材备份
│   └── <游戏>/
│       └── <角色名>/
│           ├── 01_基本信息.md
│           ├── 02_人物形象.md
│           └── assets/
│               ├── images/          # 角色参考图（图生图基准图）
│               └── audio/            # 角色音频（声音复刻）
└── SoulPod/                         # SoulPod 输出
    └── <角色名>/
        ├── profile.json
        ├── system_prompts.txt
        ├── config.json
        ├── memories/
        │   └── raw_memories.json
        └── assets/                   # 与 Origin 中的 assets 同步
            ├── images/
            └── audio/
```

## SoulPod 输出

SoulPod 包含以下文件：

| 文件 | 说明 |
|------|------|
| `profile.json` | 基础信息（名字、source_type、appearance、人格评分等） |
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

## 依赖

`pip install pdfplumber`

## 用法

- "帮我复刻XXX人格" — 完整流程（搜索 + 下载 + 生成 + 部署）
- 发素材文件给 AI 助手 — 手动启动流程

## 同步规则

SoulPod 调整时，需同步更新以下所有位置的文件（system_prompts.txt、profile.json）：

- `/data/media/MemoryPersonCard/SoulPod/<角色名>/` — 备份存储
- `~/.openclaw/workspace-coding/skills/Memory-Inhabit/personas/<角色名>/` — 主使用
- `~/.openclaw/workspace-coding/skills/Memory-Trace/output/<角色名>/` — trace 输出
- `~/.openclaw/workspace-roleplay/skills/memory-inhabit/personas/<角色名>/` — roleplay 副本
