# 进度日志

## 当前已验证状态

- 仓库根目录：`G:\Memory-Series\Trace-Inhabit`（Monorepo：`trace/` + `inhabit/`）
- 标准启动路径：`bash harness/init.sh`；本仓库无独立服务进程，标准使用入口是
  `python inhabit/scripts/loader.py load <角色>`
- 标准验证路径：`python harness/verify.py`（全量）/ `--quick`（结构+语法）
- 当前最高优先级未完成功能：`runtime-001` 解耦平台相关的消息与定时机制
- 当前 blocker：无失败项。唯一 WARN 是「Git/未跟踪」中的 `harness/` 与
  `trace/output/Lucy/*`，那是**待维护者确认提交**的内容，属预期而非缺陷。

### 最近一次验证结果（Session 002 收尾，2026-09-13）

```
python harness/verify.py         →  FAIL 0   WARN 1   INFO 1   PASS 31   exit=0
python harness/verify.py --quick →  FAIL 0                                exit=0
```

通过的检查：结构必需文件、12 个 .py 语法、文本编码、harness 自身完整性、占位符实例化、
11 个模块导入、2 个 CLI 入口、8 个角色包完整性（4 角色 × personas/output，均为 pass）、
8 个 profile 字段完整性、output↔personas 同步（豁免 personas 侧独有媒体 38 个）、
89 个待提交文件的敏感信息扫描、4 类 Git 禁提交项、大文件规模。

Session 001 的 9 项 FAIL 已全部消除，明细见 `feature_list.json`。

## 会话记录

### Session 001

- 日期：2026-09-13
- 本轮目标：根据 `harness/` 模板，为当前项目搭建 harness 约束；完成项目自检；把
  「git commit/push 由用户决定」写入 harness。
- 已完成：
  - 通读 `harness/` 模板（AGENTS.md / feature_list.json / claude-progress.md /
    init.sh / session-handoff.md），确认其为占位符状态且默认假定 Node 项目。
  - 新增 `harness/verify.py`：本项目验证规则的唯一实现处。
  - 重写 `harness/init.sh`：Python 优先的解释器定位 + 验证编排 + 标准使用入口提示。
  - 实例化 `harness/feature_list.json`、`harness/claude-progress.md`、
    `harness/session-handoff.md`。
  - 改写 `harness/AGENTS.md`：适配本项目，新增「Git 提交与推送（硬性约束）」。
  - `CLAUDE.md` 新增「Harness（开发流程约束）」章节作为反向入口。
- 运行过的验证：
  - `python harness/verify.py` → FAIL 9 / WARN 4 / INFO 1 / PASS 21，exit=1
  - `python harness/verify.py --quick` → FAIL 0，exit=0
  - **故意制造 FAIL 的回归测试**：临时创建 `inhabit/personas/__verify_probe__`
    （仅含字段残缺的 profile.json）→ verify.py 报 FAIL 11，同时命中
    「SoulPod/完整性」与「SoulPod/profile 字段」，精确报出目录名，exit=1；
    删除探针后结果回归 FAIL 9，确认 FAIL 驱动非零退出码且定位准确
  - Git Bash（PortableGit 1.2.0）执行 `harness/init.sh` → 编排正确，exit=1 与
    verify.py 一致
  - `python trace/scripts/forge.py list`、`python inhabit/scripts/loader.py list` → exit=0
- 已记录证据：见 `feature_list.json` 中 `harness-001` 的 `evidence` 字段。
- 提交记录：待用户确认（未执行任何 git commit / push）
- 更新过的文件或工件：
  - `harness/verify.py`（新增）
  - `harness/init.sh`（重写）
  - `harness/feature_list.json`（实例化）
  - `harness/claude-progress.md`（实例化）
  - `harness/session-handoff.md`（实例化）
  - `harness/AGENTS.md`（改写）
  - `CLAUDE.md`（新增「Harness（开发流程约束）」章节，指向 harness 并写明
    commit/push 需维护者明确指示）
- 已知风险或未解决问题：见下方「仍未解决的风险」。

#### 相对 harness 模板的改动（需知悉）

1. **`init.sh` 不再 exec 常驻进程**。本项目是技能仓库，没有可启动的服务；
   `START_CMD` 降级为「标准使用入口」提示。
2. **`init.sh` 不依赖外部 `dirname`**。改用 shell 参数展开定位仓库根目录。
   原因：本机 Git-Bash 环境 coreutils 不完整，原模板 `$(dirname ...)` 会直接失败。
3. **新增 `verify.py`，验证规则与编排分离**。原模板的 `npm install` / `npm test`
   对本仓库无意义，故替换为 Python 验证入口。
4. **`AGENTS.md` 「收尾」第 4 条被改写**。原为「用清晰的提交信息提交」，现改为
   「先向用户提交建议的提交信息与变更清单，等用户明确指示后再提交」；并新增
   「Git 提交与推送（硬性约束）」章节。

### Session 002

- 日期：2026-09-13
- 本轮目标：按用户确认的 6 个决策点执行修复（「按建议执行」）；数据层、schema、
  忽略规则、文档一并收敛；git 仍只做只读操作。
- 本轮决策（用户确认）：

  | # | 决策点 | 采纳口径 |
  |---|--------|----------|
  | 1 | 两个空目录 `庄方宜/` | 删除（历史 commit `25916e8` 已明确移除该角色卡，本地只是残留） |
  | 2 | `trace/output/Lucy` | 从 `inhabit/personas/Lucy` 反向补齐，恢复「双线」约定 |
  | 3 | `gender` 放哪里 | 顶层为权威（与 `forge.py:379` 生成口径、`tts.py`/`imggen.py` 读取口径一致），`appearance.gender` 冗余副本 |
  | 4 | assets 命名冲突 | 改代码：`imggen.resolve_reference_image()` 同时接受 `assets/images/` 与 `assets/image/`，不迁移现有数据 |
  | 5 | 同步检查白名单 | 仅豁免「personas 侧独有的 `assets/` 媒体文件」；语义文件必须一致 |
  | 6 | `.workbuddy/` 与 gif | `.workbuddy/` 加入根 `.gitignore`；`personas/*/assets/gif/` 暂不纳入版本管理（无代码引用，可一行恢复） |

- 已完成：
  - **数据层**：删除 `inhabit/personas/庄方宜` 空目录树（实为 `assets/images/` 空嵌套，
    git 不跟踪空目录，删除对版本库无影响）；`trace/output/庄方宜` 本就不存在。
  - **数据层**：`trace/output/Lucy` 补齐 `profile.json`、`config.json`、
    `system_prompts.txt`、`memories/raw_memories.json`、`assets/source.txt`；
    `prompt/story_baseline.txt`（原 CRLF）与 `prompt/universal_prompt.txt` 覆盖为
    personas 侧内容（去掉行尾假差异）。
  - **数据层**：`trace/output/夏以昼/profile.json`、`assets/source.txt` 与
    `trace/output/叶修/profile.json` 对齐为 personas 侧内容。对齐方向为
    `output := personas`——personas 侧是超集（`source_type`/`source`/`appearance`/
    `occupation`/`hometown` 更完整），无信息丢失。
  - **数据层**：为 4 角色 × 2 侧共 8 个 `profile.json` 写入 `gender`
    （夏以昼/叶修/秦彻=male，Lucy=female），并同步写入 `appearance.gender`。
  - **代码层**：`inhabit/scripts/imggen.py` 的 `resolve_reference_image()` 改为依次
    尝试 `assets/images` 与 `assets/image`。
  - **验证层**：`harness/verify.py` 三项规则精化（见下）。
  - **忽略规则**：根 `.gitignore` 新增 `.workbuddy/`；`inhabit/.gitignore` 新增
    `personas/*/assets/gif/`，两处均附注释与恢复方式。
  - **文档层**：`CLAUDE.md`（SoulPod 字段口径 + 行尾约定 + 禁提交项）、
    `trace/SKILL.md`、`trace/README.md`、`inhabit/SKILL.md`、`inhabit/README.md`
    统一声明 gender 顶层权威 + appearance 冗余、参考图目录双命名兼容。
  - **Harness**：`feature_list.json` 更新为 8 项功能（5 项 passing，新增
    `hygiene-001`）；本文件与 `session-handoff.md` 更新。
- 运行过的验证：
  - 修复前：`python harness/verify.py` → FAIL 9 / WARN 4 / PASS 21，exit=1
  - 修复后：`python harness/verify.py` → **FAIL 0 / WARN 1 / INFO 1 / PASS 31，exit=0**
  - `python harness/verify.py --quick` → FAIL 0，exit=0
  - **TTS 性别回归**：`python inhabit/scripts/tts.py --persona <角色目录> --preview`
    → Lucy「性别: 女」+ 女声（xiaoxiao）；夏以昼/叶修/秦彻「性别: 男」+ 男声（yunjian）。
    修复前 Lucy 因 `gender` 缺失回退 male。
  - **参考图解析回归**：直接调用 `imggen.resolve_reference_image()` →
    叶修 命中 `personas/叶修/assets/image/叶修.jpg`；夏以昼 命中
    `personas/夏以昼/assets/image/夏以昼头像.jpeg`；Lucy/秦彻 无参考图返回 `None`（正确）。
    修复前只查 `assets/images/`，叶修与夏以昼均取不到。
  - `python inhabit/scripts/imggen.py prompt 叶修 "在房间里举着手机自拍"`
    → `include_appearance: True`，外观描述正常拼接。
- 已记录证据：见 `feature_list.json` 中 `base-001` / `base-002` / `base-003` /
  `schema-001` / `hygiene-001` / `harness-001` 的 `evidence` 字段。
- 提交记录：**待用户确认（本轮未执行任何 git commit / push）**
- 更新过的文件或工件：
  - `harness/verify.py`（三项规则精化）
  - `harness/feature_list.json`（重建为 8 项功能）
  - `harness/claude-progress.md`（本文件）
  - `harness/session-handoff.md`
  - `inhabit/scripts/imggen.py`（参考图双命名）
  - `.gitignore`、`inhabit/.gitignore`
  - `CLAUDE.md`、`trace/SKILL.md`、`trace/README.md`、`inhabit/SKILL.md`、
    `inhabit/README.md`
  - 数据：8 个 `profile.json`；`trace/output/Lucy/*`（7 个文件新增/覆盖）；
    `trace/output/夏以昼/{profile.json,assets/source.txt}`、
    `trace/output/叶修/profile.json`（对齐）
  - 删除：`inhabit/personas/庄方宜/`（空目录树）

#### Session 002 对 verify.py 的规则精化（3 项，需知悉）

1. **内容比对改为文本行尾归一化**（`sha256()`）。
   原因：本机 `core.autocrlf=true` 且仓库无 `.gitattributes`，工作区文本文件行尾被
   git 转换，`inhabit/personas/Lucy/prompt/story_baseline.txt` 曾因 CRLF/LF 差异被
   误判为「内容不同」——而两者在 git 对象库中本就相同。现文本文件先做 CRLF→LF
   归一化再哈希，二进制仍按原字节。这是**精度修正**，实质内容差异仍会报出。
2. **output↔personas 同步新增显式豁免规则**（`SYNC_ASSET_ALLOW_RE`）。
   仅豁免「仅 personas 侧存在的 `assets/` 媒体文件」（图片/动画/音频/字体）。
   媒体若只存在于 output 侧，或两侧同名媒体内容不同，仍照常报出。
   豁免范围在 CLAUDE.md 与两处 SKILL.md 有文字说明。
3. **profile 检查新增 gender 冗余一致性校验**。
   若顶层 `gender` 与 `appearance.gender` 同时存在且不一致 → WARN。
   用于守住 Session 002 决策 3 建立的「顶层权威 + appearance 冗余」不变式。

## 仍未解决的风险

1. **平台耦合（`runtime-001`）**：`sender.py` 的 `<qqmedia>` 与 `cleanup.py` 的
   openclaw cron，在当前 WorkBuddy 环境下无法直接工作。需维护者确认目标平台。
2. **人格推断与人工设定脱节（`quality-001`）**：夏以昼 profile.json 打分为
   开放性/外向性/宜人性/神经质均 0.8，关键词「思想开放/热情开朗/温和善良/敏感多思」，
   与人工设定「偏执腹黑、冷峻」相反。本轮未触碰评分与关键词。
3. **缺失的 TTS 配置字段**：`inhabit/personas/夏以昼/config.json` 缺
   `tts_provider` / `minimax_voice_id` / `voice_description` / `edge_voice`
   （秦彻、Lucy 有），仍走默认值。不在本轮决策范围，待维护者确认是否补齐。
4. **无 CI、无测试、无依赖清单**：`verify.py` 是唯一回归防线，其覆盖范围有限
   （不做对话质量与生成质量验证）。
5. **本机 shell 环境**：PATH 上的 `bash` 指向 WSL 启动器且被安全策略拦截；Git-Bash
   的 coreutils 缺失 `dirname`/`cat`/`tail`/`head`；PowerShell 输出可能不回显。
   所有验证与检查请优先走 `python harness/verify.py`，或使用 Git-Bash 绝对路径。
6. **建议但未执行**：新增 `.gitattributes`（如 `* text=auto eol=lf`）可从根上消除
   CRLF 假差异。该改动会触发全仓库重新检出，影响面较大，需维护者明确同意后再做。
