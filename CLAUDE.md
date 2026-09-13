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

**字段口径（`harness/verify.py` 会校验）：**

- `profile.json` 的 `gender` 为**顶层权威字段**（`tts.py` / `imggen.py` 读顶层）；
  `appearance.gender` 是冗余副本，必须与顶层一致。
- 参考图目录同时接受 `assets/images/`（文档与 `forge.py` 约定）与 `assets/image/`（早期落盘数据）。
- `trace/output/<角色>/` 与 `inhabit/personas/<角色>/` 的**语义文件**（`profile.json`、
  `config.json`、`system_prompts.txt`、`memories/`、`prompt/`、`assets/source.txt`）
  必须内容一致；**仅 `assets/` 下的媒体文件**允许只存在于 personas 侧。

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

夏以昼、叶修、秦彻、Lucy：**不补齐** `trace/origin/`，仅以 `trace/output/` + `inhabit/personas/` 维护。若从 origin 重新复刻，则走三线并 `install` 同步。

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
- `inhabit/personas/*/assets/gif/`（本地生成的 GIF 帧序列，当前无代码引用，见 `inhabit/.gitignore`）
- `.workbuddy/`（WorkBuddy agent 会话状态目录，非项目产物，见根 `.gitignore`）

## 行尾约定（Windows）

本机 git 配置为 `core.autocrlf=true`，且仓库无 `.gitattributes`：提交时 CRLF 归一化为 LF，
检出到工作区时又还原为 CRLF。因此**工作区文件的行尾不具可比性**。
`harness/verify.py` 的内容比对已对文本文件做 CRLF→LF 归一化，避免假差异。

## Harness（开发流程约束）

本仓库的长时运行 agent 工作流约束位于 `harness/`，与本文件的领域约定互补：

| 文件 | 作用 |
|------|------|
| `harness/AGENTS.md` | 开工流程、工作规则、完成定义、收尾、Git 硬性约束 |
| `harness/feature_list.json` | 功能状态的唯一事实来源 |
| `harness/claude-progress.md` | 会话进度与当前已验证状态 |
| `harness/init.sh` | 统一启动与验证入口 |
| `harness/verify.py` | 验证规则的唯一实现处 |
| `harness/session-handoff.md` | 较长会话的交接摘要 |

**标准验证命令：** `python harness/verify.py`（全量）/ `--quick`（结构+语法）。

**改动约束：** 修改 SoulPod 结构、路径约定或禁提交项时，必须同步更新本文件与
`harness/verify.py` 中对应的检查；不得为让验证变绿而放宽 `verify.py` 的规则。

**Git 约束：** `git commit` 与 `git push` 必须由维护者明确指示后才可执行，详见
`harness/AGENTS.md`。

