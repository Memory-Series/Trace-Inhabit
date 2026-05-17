# Memory Series — 协同开发规范

本仓库采用 Monorepo 结构，包含两个独立项目。

## 目录结构

```
memory-series/
├── CLAUDE.md        # 本文件
├── README.md
├── trace/           # Memory-Trace — 人格提取工具
└── inhabit/         # Memory-Inhabit — 角色加载对话
```

## 开发原则

- Trace 是生产端，Inhabit 是消费端
- SoulPod 格式必须兼容两个项目
- 修改跨项目接口（如 SoulPod 结构）需同步更新两边的 SKILL.md

## SoulPod 结构（两项目共享）

```
profile.json        # 基础身份
system_prompts.txt  # 说话风格
config.json         # 运行时配置
memories/
  └── raw_memories.json
prompt/
  ├── universal_prompt.txt   # 供普通 LLM 直接使用
  └── story_baseline.txt     # 故事基线（当前主线与对话倾向）
assets/
  └── source.txt
```

## 路径约定（仅以 Monorepo 为准）

| 类型 | 路径 |
|------|------|
| 原始素材 | `trace/origin/<游戏>/<角色名>/` |
| Trace 输出 | `trace/output/<角色名>/` |
| Inhabit 加载 | `inhabit/personas/<角色名>/` |

说明与细则见 `trace/origin/README.md`。

## 角色维护：三线 vs 双线

### 新角色（推荐「三线」）

1. **origin** — 搜集的原始 `*.md` 与可选 `assets/images`、`assets/audio`
2. **output** — `forge.py create --from-origin <游戏>/<角色名>` 生成 SoulPod
3. **personas** — `forge.py install <角色名>` 同步到 Inhabit

`forge` 会自动合并 origin 下 md、将 `origin/assets` 复制到 `output/assets`（`assets/source.txt` 仍为分析片段备份，不替代 origin）。

### 遗留内置角色（「双线」）

夏以昼、叶修、庄方宜、戴安娜、秦彻、拓跋玉儿、Lucy：**不补齐** `trace/origin/`，仅以 `trace/output/` + `inhabit/personas/` 维护。若从 origin 重新复刻，则走三线并 `install` 同步。

## 原始素材与 Git（trace/origin）

| 内容 | Git |
|------|-----|
| `origin/**/*.md` | 跟踪提交 |
| `origin/**/assets/images/**`、`origin/**/assets/audio/**` | **不提交**（见 `trace/.gitignore`） |
| `origin/**/_merged_source.md` | **不提交**（forge 本地合并产物） |

## 角色包版本管理（output + personas）

本仓库为 **开箱即用 Demo 分发**：内置角色的 SoulPod **纳入 Git 跟踪**。

| 目录 | 用途 |
|------|------|
| `trace/output/<角色名>/` | Trace 生成产物 |
| `inhabit/personas/<角色名>/` | Inhabit 加载副本 |

**同步约定：** 更新 SoulPod 后执行 `forge.py install <角色名>` 或手动对齐 `output/` 与 `personas/`，再提交。残缺包（缺 `profile.json` 等）不应提交。

## 禁止提交

- `__pycache__/`、`*.pyc`、`*.pyo`
- `.pytest_cache/`、`*.egg-info/`、`dist/`、`build/`
- 编辑器目录（`.vscode/`、`.idea/`）与 OS 垃圾文件（`.DS_Store` 等）
- 任何 `.env` 或含 API Key、Token 等敏感信息的文件
- `trace/origin/**/assets/images/`、`trace/origin/**/assets/audio/`、`_merged_source.md`（见 `trace/.gitignore`）
- `inhabit/personas/*/memories/diary/`、`inhabit/personas/*/memories/history/`（私密日记与对话流水，见 `inhabit/.gitignore`）
