# AGENTS.md

这个仓库面向长时运行的 coding agent 工作流。目标不是尽可能快地产出代码，而是让每一轮会话结束后，下一个会话仍然能无猜测地继续工作。

适用项目：**Memory Series — Trace / Inhabit**（Monorepo：`trace/` 生产 SoulPod，`inhabit/` 消费 SoulPod）。
领域约定（SoulPod 结构、路径、禁提交项）见仓库根目录 `CLAUDE.md`，本文件只负责流程约束。

## 开工流程

写代码前先做这些事：

1. 用 `pwd` 确认当前目录是仓库根（`trace/` 与 `inhabit/` 的同级）。
2. 读取 `harness/claude-progress.md`，了解最新已验证状态和下一步。
3. 读取 `harness/feature_list.json`，选择优先级最高的未完成功能。
4. 用 `git log --oneline -5` 看最近提交。
5. 运行 `bash harness/init.sh`（或 `python harness/verify.py`）。
6. 在开始新功能前，先跑必需的 smoke test：`python harness/verify.py --quick`。

如果基础验证一开始就失败，先修基础状态，不要在坏的起点上继续叠新功能。
注意：本仓库的合法基线是 **`FAIL 0`**。若出现 WARN，先确认它是「已记录的预期项」
（例如待维护者确认提交的未跟踪内容），再继续开工；不要把 WARN 当成可忽略的背景噪音。

## 工作规则

- 一次只做一个功能。
- 不要因为"代码已经写了"就把功能标记为完成。
- 除非为了消除当前 blocker 的窄范围修复，否则不要扩大到其他功能。
- 实现过程中不要悄悄改弱验证规则。
- 优先依赖仓库里的持久化文件，而不是聊天记录。
- **验证规则的唯一实现处是 `harness/verify.py`。** 修改判定口径必须同时更新该文件、
  `feature_list.json` 中受影响功能的 `verification`、以及 `claude-progress.md`。
- **改 SoulPod 的 JSON 数据时用「文本级插入」，不要用 `json.dump` 整体回写。**
  `json.dump(..., indent=2)` 会把内联数组（如 `"alias": ["Sylus"]`）展开成多行，
  制造与语义无关的大量 diff。需要在原文基础上加字段时，先 `git show HEAD:<path>`
  取出原文，再按行插入新字段。

## 必需文件

- `feature_list.json`：功能状态的唯一事实来源
- `claude-progress.md`：会话进度和当前已验证状态
- `init.sh`：统一的启动与验证入口
- `verify.py`：验证规则的唯一实现处
- `session-handoff.md`：较长会话可选的交接摘要

## 完成定义

一个功能只有在以下条件都满足时才算完成：

- 目标行为已经实现
- 要求的验证真的跑过
- 证据记录在 `feature_list.json` 或 `claude-progress.md`
- 仓库仍然能按标准启动路径重新开始工作

## Git 提交与推送（硬性约束）

**本仓库的 `git commit` 与 `git push` 必须由用户明确指示后才可执行。**

agent 可以做的事：

- 只读操作：`git status`、`git diff`、`git log`、`git show`、`git stash list`
- 起草提交信息，并列出建议纳入本次提交的变更清单
- 在用户明确要求时执行 `git add`

agent 不可以做的事（除非用户在当前轮明确指示）：

- `git commit`、`git push`、`git commit --amend`
- `git push --force`、`git reset --hard`、`git checkout --`、`git clean -fd`
- 任何改写历史或丢弃工作区变更的操作

收尾时如果工作区存在未提交变更，在 `claude-progress.md` 的「提交记录」中写明
**待用户确认**，并给出建议的提交信息；不要留空，也不要代为提交。

## 环境约束（Windows / 当前运行环境）

1. **PATH 上的 `bash` 不可用**：在 Windows 上它解析到 `C:\Windows\system32\bash.EXE`
   （WSL 启动器），可能被安全策略拦截。需要 shell 时请使用 Git-Bash 的绝对路径，
   或直接调用 `python harness/verify.py`。
2. **Git-Bash 的 coreutils 可能不完整**：已观察到 `dirname`、`cat`、`tail`、`head`
   缺失。因此 `init.sh` 不调用外部 `dirname`，只用 shell 参数展开。
3. **PowerShell 的输出可能无法回显**。需要捕获命令输出时，优先使用 Python
   `subprocess`，而不是依赖 shell 管道。
4. **不要用 shell 管道做检查**（`| head`、`| tail` 等会因 coreutils 缺失而失败）。
   检查逻辑写进 `verify.py`。

## 收尾

结束会话前：

1. 更新 `claude-progress.md`
2. 更新 `feature_list.json`
3. 记录仍未解决的风险或 blocker
4. **不要自动提交。** 向用户提交「建议的提交信息 + 变更清单」，等用户明确指示后
   再执行 `git commit` / `git push`（见「Git 提交与推送（硬性约束）」）
5. 保证下一轮会话可以直接运行 `bash harness/init.sh`
