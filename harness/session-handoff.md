# 会话交接

## 当前已验证

- 现在明确可用的部分：
  - `python harness/verify.py` 可复现地给出仓库健康报告（十类检查，退出码语义明确）
  - `bash harness/init.sh` 可完成编排（需 Git-Bash 绝对路径，见下方风险）
  - 12 个 Python 脚本语法与导入全部通过；`forge.py list` / `loader.py list` 可运行
  - 4 个内置角色在 `inhabit/personas/` 与 `trace/output/` **两侧**的包均完整
    （`trace/output/Lucy` 已补齐）
  - 4 个角色的 `profile.json` 含 `gender`，TTS 音色匹配实测正确
    （Lucy=女声，夏以昼/叶修/秦彻=男声）
  - `imggen` 参考图解析对叶修、夏以昼可命中实际路径（`assets/image/` 双命名兼容）
- 这轮实际跑过的验证：
  - `python harness/verify.py` → **FAIL 0 / WARN 1 / INFO 1 / PASS 31，exit=0**
  - `python harness/verify.py --quick` → FAIL 0，exit=0
  - `python inhabit/scripts/tts.py --persona <角色> --preview` → 4 角色性别与音色均正确
  - 直接调用 `imggen.resolve_reference_image()` → 叶修/夏以昼 命中，Lucy/秦彻 返回 None
  - `python inhabit/scripts/imggen.py prompt 叶修 "..."` → 外观描述正常拼接

## 本轮改动

- 新增了哪些代码或行为：
  - `inhabit/scripts/imggen.py`：`resolve_reference_image()` 同时接受
    `assets/images/` 与 `assets/image/`
  - `.gitignore`：新增 `.workbuddy/`；`inhabit/.gitignore`：新增
    `personas/*/assets/gif/`
- 数据发生了哪些变化：
  - 删除 `inhabit/personas/庄方宜/`（空目录树）；`trace/output/庄方宜` 本就不存在
  - `trace/output/Lucy` 补齐 7 个文件（与 personas 侧一致）
  - `trace/output/夏以昼/{profile.json,assets/source.txt}`、
    `trace/output/叶修/profile.json` 对齐为 personas 侧内容
  - 8 个 `profile.json` 写入 `gender` 与 `appearance.gender`
- 基础设施或 harness 发生了哪些变化：
  - `verify.py` 三项规则精化：文本行尾归一化哈希、output↔personas 显式豁免规则、
    gender 冗余一致性校验（详见 `claude-progress.md` Session 002）
  - `feature_list.json` 重建为 8 项功能：`harness-001`、`base-001`、`base-002`、
    `base-003`、`schema-001`、`hygiene-001` 为 passing；`runtime-001`、`quality-001`
    为 not_started（**本轮没有 in_progress 功能**）
  - `CLAUDE.md` 新增「行尾约定（Windows）」与 SoulPod「字段口径」说明
  - `AGENTS.md` 的 Git 硬性约束未变：commit / push 必须由维护者明确指示

## 仍损坏或未验证

- 已知缺陷：无 FAIL。`runtime-001`（平台耦合）与 `quality-001`（人格推断与人工设定
  脱节）仍是未开始的功能项；`inhabit/personas/夏以昼/config.json` 缺 4 个 TTS 字段
  （不在本轮决策范围）
- 未验证路径：对话质量、人格保真度、TTS/图生图的实际出图出音质量
  （缺 API Key，且无测试）
- 下一轮会话需要注意的风险：
  - 唯一 WARN 是 `harness/` 与 `trace/output/Lucy/*` 尚未提交——需维护者确认后提交
  - 本仓库无 CI、无测试、无依赖清单，`verify.py` 是唯一回归防线
  - 本机 `core.autocrlf=true`，工作区行尾不可直接比对（`verify.py` 已做归一化）
  - 建议但未执行：新增 `.gitattributes`（影响面较大，需维护者同意）

## 下一步最佳动作

- 最高优先级未完成功能：`runtime-001` 解耦平台相关的消息与定时机制
- 为什么它是下一步：数据层与 schema 层缺口已全部收敛，剩下两项未开始功能中
  `runtime-001` 直接决定伴侣模式在当前环境能否实际工作
- 什么结果才算 passing：确认 `sender.py` 输出可在当前环境被消费（或参数化多平台），
  且 `cleanup.py` 的定时清理改由 WorkBuddy automation 承载
- 这一步中哪些东西不要动：不要放宽 `verify.py` 的规则；不要回退 Session 002 建立的
  gender 顶层权威口径与 assets 双命名兼容；不要把已对齐的语义文件重新改回单侧

## 命令

- 启动命令：`bash harness/init.sh`（或 `python harness/verify.py`）
- 验证命令：`python harness/verify.py`；快速：`python harness/verify.py --quick`
- 定向调试命令：
  - 单角色包详情：`python inhabit/scripts/loader.py info <角色>`
  - 音色/性别预览：`python inhabit/scripts/tts.py --persona <角色目录> --preview`
  - 生成包完整性：`python trace/scripts/forge.py validate <角色>`
