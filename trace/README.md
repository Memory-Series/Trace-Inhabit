# Memory-Trace — 人格复刻工坊

> 从文字的碎片中，铸一个灵魂的模。
> 将故事里的人、记忆里的人，复刻为可触碰的存在。

## 这是什么？

Memory-Trace（寻迹）是 SoulPod 生态的**生产端**。它负责从各种素材中分析、提取、建模一个人的人格特征，并自动生成标准 SoulPod Digital Twin Package。

| 技能 | 职责 | 关系 |
|------|------|------|
| **寻迹（Memory-Trace）** | 工厂 — 生产 SoulPod 包 | 上游 |
| **入心（Memory-Inhabit）** | 播放器 — 加载并复现人格 | 下游 |

## 支持的输入

| 格式 | 示例 |
|------|------|
| 📄 纯文本 (.txt/.md) | 回忆录、日记、小说片段 |
| 📑 PDF (.pdf) | 剧本、小说、传记 |
| 💬 JSON (.json) | 聊天记录导出 |
| 📋 自由文本 | 你写的任何关于这个人的描述 |

## 快速开始

### 1. 从剧本复刻角色

```bash
cd ~/.openclaw/workspace-coding/skills/Memory-Trace

# 第一步：识别所有角色
python3 scripts/analyzer.py characters samples/thunderstorm.txt

# 第二步：对指定角色进行人格建模
python3 scripts/analyzer.py model samples/thunderstorm.txt -c "周朴园"

# 第三步：完整流程生成 SoulPod 包
python3 scripts/forge.py create --source samples/thunderstorm.txt --character "周朴园"

# 第四步：预览生成结果
python3 scripts/forge.py preview 周朴园

# 第五步：安装到 Memory-Inhabit（入心）技能
python3 scripts/forge.py install 周朴园
```

### 2. 从回忆文字复刻亲人

```bash
# 把你写的关于亲人的文字保存为 txt 文件
# 然后直接生成 SoulPod 包
python3 scripts/forge.py create --source my_dad.txt --character "爸爸" -o dad

# 安装后即可使用 Memory-Inhabit（入心）技能对话
python3 scripts/forge.py install dad
```

### 3. 对 AI 助手说

> "这个 PDF 是《雷雨》的剧本，帮我复刻繁漪的人格"

AI 助手会自动执行整个流程。

## 项目结构

```
Memory-Trace/
├── SKILL.md              # 技能定义
├── README.md             # 本文件
├── scripts/
│   ├── analyzer.py       # 分析引擎（角色识别、人格建模、语言风格、记忆提取）
│   └── forge.py          # 主控脚本（完整流程、安装、验证）
├── samples/              # 示例输入素材
└── output/               # 生成的 SoulPod 包
```

## 分析引擎能力

### 角色识别（4种策略）

1. **剧本对白格式** — `角色名：对白`
2. **对话引用格式** — `某某说/道/问/答`
3. **关系描述** — `某某的父亲/母亲/...`
4. **频率统计** — 按出现次数排序

### 人格建模（Big Five 推断）

从文本行为和语言模式推断：
- 开放性、责任心、外向性、宜人性、神经质
- 性格关键词

### 语言风格提取

- 高频用语/口头禅
- 语气词偏好
- 语调特征（强烈/反问/含蓄/简练）

### 记忆提取（3类）

- 事实记忆 — 从叙述和行为中提取
- 价值观记忆 — 从信条性语句中提取
- 情感记忆 — 从他人评价中提取

## 开发路线

| 阶段 | 状态 | 目标 |
|------|------|------|
| 骨架搭建 | ✅ | 目录结构、分析器、主控脚本 |
| 文本分析 | ✅ | 角色识别 + 人格推断 + 记忆提取 |
| PDF 解析 | ✅ | 通过 pdfplumber 支持 |
| 多角色管理 | 📋 | 批量复刻、角色关系图 |
| 聊天记录处理 | 📋 | 微信导出格式解析 |
| 向量记忆检索 | 📋 | RAG 升级 |
| 语音/图像输入 | 🔮 | 多模态素材支持 |

## 与 Memory-Inhabit 的协作

```
素材 → [Memory-Trace] → SoulPod 包 → [Memory-Inhabit] → 人格对话
                              ↑                         ↓
                          标准规范                 用户说"聊聊"
```

产出物严格遵循 SoulPod 包规范，无需任何转换即可被 Memory-Inhabit（入心）技能直接加载。
