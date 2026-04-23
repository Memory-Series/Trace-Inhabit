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
assets/
  └── source.txt
```

## 禁止提交

- `trace/output/` — 生成的 SoulPod 包
- `inhabit/personas/` — 加载的角色数据
- `__pycache__/`、`.pyc`
- 任何 `.env` 或含敏感信息的文件

## 角色部署路径（TOOLS.md 约定）

| 类型 | 路径 |
|------|------|
| Origin 素材 | `/data/media/MemoryPersonCard/Origin/<游戏>/<角色名>/` |
| Trace 输出 | `~/.openclaw/workspace-coding/skills/Memory-Trace/output/<角色名>/` |
| Inhabit 加载 | `~/.openclaw/workspace-roleplay/skills/memory-inhabit/personas/<角色名>/` |

注意：部署后 Inhabit 的实际路径在 `workspace-roleplay` 下，技能内 `personas/` 目录仅用于本地开发测试。