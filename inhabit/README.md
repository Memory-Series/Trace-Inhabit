# 入心（Memory-Inhabit）— 数字人格复刻

> 以记忆为核，入心而居。
> 在光标的闪烁中，见字如面，温润如初。

## 这是什么？

Memory-Inhabit 是一个**数字人格复刻**项目。通过 AI 技术，让你能够与特定人格进行日常对话。

核心理念：**解耦 + 资产化**

- **解耦**：将人的特质（记忆、性格、语气）从具体的 AI 模型中剥离
- **资产化**：将特质封装为标准化文件包，成为可永久保存、跨平台迁移的数字资产

## 快速开始

### 1. 查看示例人格包

```bash
cd ~/.openclaw/workspace-coding/skills/Memory-Inhabit
python3 scripts/loader.py list
python3 scripts/loader.py info 夏以昼
```

### 2. 创建你自己的人格包

复制 `personas/夏以昼/` 目录（或任意已有包），重命名为你想要的称呼：

```bash
cp -r personas/夏以昼 personas/dad
```

然后编辑里面的文件：
- `profile.json` — 填写人格画像
- `system_prompts.txt` — 编写行为规范
- `config.json` — 技术配置
- `memories/raw_memories.json` — 录入记忆条目

### 3. 加载 & 对话

对 AI 助手说：
> "我想和爸爸聊聊"

或手动加载：
```bash
python3 scripts/loader.py load dad
```

### 4. 卸载

对 AI 助手说：
> "回到正常模式"

## 项目结构

```
Memory-Inhabit/
├── SKILL.md               # 技能定义与触发规则
├── README.md              # 本文件
├── scripts/
│   ├── loader.py          # 人格加载器
│   ├── sender.py          # 伴侣模式消息发送
│   ├── memory.py          # 对话历史与记忆管理
│   ├── checker.py         # 主动消息频率控制
│   ├── cleanup.py         # 卸载清理
│   ├── deploy.py          # 部署为独立 Agent
│   └── tts.py             # TTS 语音生成
└── personas/              # 人格包目录（内置示例）
    └── 夏以昼/            # 示例人格，可自行添加更多
```

## 开发路线

| 阶段 | 状态 | 目标 |
|------|------|------|
| 骨架搭建 | ✅ | 目录结构、规范文档、加载器原型 |
| 基础加载 | 🔜 | profile 解析、System Prompt 拼装、人格切换 |
| 记忆检索 | 📋 | 关键词匹配 → 向量检索 |
| 多人格管理 | 📋 | 多人格包注册、切换、对话隔离 |
| 对话持久化 | 📋 | 跨会话对话历史 |
| 情感分析 | 📋 | 检测用户情绪，动态调整回复 |
| 语音克隆 | 🔮 | TTS 接入，模拟声音 |

## 设计哲学

1. **真实性优先**：宁可说"记不清了"，也不编造经历
2. **去 AI 化**：对话中绝不暴露 AI 身份
3. **情绪优先**：用户崩溃时，先陪伴，不讲道理
4. **模型无关**：人格包不绑定任何特定 AI 模型
