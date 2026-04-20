# Memory Series

角色人格提取与对话系统。

## Projects

### [Trace](./trace/) — 人格提取工具
从素材（文本、对话记录等）提取角色人格，生成 SoulPod 包。

### [Inhabit](./inhabit/) — 角色加载对话
加载 SoulPod 包，以角色身份进行对话。

## 架构

```
素材 (Origin)
    ↓ Memory-Trace
SoulPod (profile.json + system_prompts.txt + memories)
    ↓ Memory-Inhabit
角色对话
```

更多信息请参考各项目目录下的 SKILL.md。