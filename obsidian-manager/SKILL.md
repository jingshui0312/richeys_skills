# Obsidian Manager Skill

管理存储在 iCloud 上的 Obsidian 知识库，支持 CLI 和对话两种模式。

**触发词**：写日记、记一下、记到 Obsidian、存到知识库、搜笔记、投到 Inbox、整理 Inbox、查笔记、Obsidian、PKM、记笔记、笔记、daily note、日记

---

## Vault 信息

- **路径**：`/Users/richey.li/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的个人知识库/`
- **文件夹**：`Daily/`、`Inbox/`、`Study/`、`Resource/`、`Canvas/`
- **日记命名**：`YYYY-MM-DD.md`（如 `2026-03-09.md`）
- **默认日记 section**：`今天发生了什么`
- **iCloud 同步**：文件写入后自动同步，`.icloud` 后缀文件为占位符，跳过不读

---

## Workflow — 根据可用工具选择路径

### Path 1：CLI 模式（Bash 工具可用，优先使用）

调用 `obsidian-tool` CLI，解析 JSON 输出，向用户汇报结果。

CLI 路径：`~/.claude/skills/obsidian-manager/obsidian-tool`（使用全路径，无需 PATH 配置）

```bash
# 写今日日记（不存在则自动从模板创建）
~/.claude/skills/obsidian-manager/obsidian-tool daily today --create

# 追加内容到日记指定 section
~/.claude/skills/obsidian-manager/obsidian-tool daily today --append "完成了项目部署" --section "今天发生了什么"

# 快速投递到 Inbox
~/.claude/skills/obsidian-manager/obsidian-tool inbox --add "有个想法：考虑用 Rust 重写性能瓶颈"

# 列出 Inbox
~/.claude/skills/obsidian-manager/obsidian-tool inbox --list

# 把 Inbox 笔记移到 Study
~/.claude/skills/obsidian-manager/obsidian-tool inbox --move "想法标题" --to Study

# 创建学习笔记
~/.claude/skills/obsidian-manager/obsidian-tool create "Python 异步编程" --folder Study --content "# Python 异步编程\n\n## 概念\n"

# 读取笔记
~/.claude/skills/obsidian-manager/obsidian-tool read "Python 异步编程" --folder Study

# 替换笔记全文
~/.claude/skills/obsidian-manager/obsidian-tool edit "笔记标题" --content "新的完整内容"

# 追加到任意笔记的指定 section
~/.claude/skills/obsidian-manager/obsidian-tool append "笔记标题" --content "新内容" --section "section名"

# 全文搜索
~/.claude/skills/obsidian-manager/obsidian-tool search "关键词" --limit 10

# 列出最近 7 条笔记
~/.claude/skills/obsidian-manager/obsidian-tool list --folder Daily --recent 7
```

**处理 JSON 输出**：
- `ok: true` → 操作成功，从 `path`、`content`、`notes` 等字段读取结果
- `ok: false` → 操作失败，从 `error` 字段读取原因，向用户说明

---

### Path 2：对话模式（无 Bash 工具）

直接用 Read/Write/Glob/Grep 工具操作 vault，不调用 CLI。

**Vault 根路径**（变量名：`VAULT`）：
```
/Users/richey.li/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的个人知识库
```

**写今日日记**：
1. 计算今天日期 → 文件路径：`VAULT/Daily/YYYY-MM-DD.md`
2. Glob 检查是否存在
3. 不存在：Read `VAULT/_Templates/Daily Note.md`，替换 `{{date:YYYY-MM-DD}}` → 实际日期，Write 到 Daily/
4. 存在且需追加：Read 现有内容 → 找到 `## 今天发生了什么` 后插入 `- 内容` → Write 回去

**快速 Inbox**：
1. Write 到 `VAULT/Inbox/标题.md`，内容：`# 标题\n\n- 想法内容\n`

**全文搜索**：
1. Grep 在 `VAULT/` 下搜索关键词，过滤 `.md` 文件

---

## 场景手册

### 写今日日记

用户说："写日记"、"写今天的日记"、"记录一下今天"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool daily today --create
```

汇报：日记已创建/已存在，路径为 `Daily/YYYY-MM-DD.md`。展示现有内容供用户查看。

---

### 追加日记内容

用户说："把 XXX 加到今天日记里"、"记一下今天：XXX"、"写到日记"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool daily today --append "用户内容" --section "今天发生了什么"
```

如用户指定 section（如"加到心情那一栏"），映射到对应标题：
- 今天发生了什么 / 发生了什么 → `今天发生了什么`
- 心情 / 想法 → `今天的心情 / 想法`
- 高光 / 亮点 → `今天的微小高光`
- 明天 / 待办 → `明天想做的事`

---

### 快速 Inbox

用户说："记一下"、"投到 Inbox"、"先存着"、"有个想法"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool inbox --add "用户的想法内容"
```

汇报：已存入 Inbox，文件名为 `XXX.md`。

---

### 整理 Inbox

用户说："整理 Inbox"、"看看 Inbox 有什么"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool inbox --list
```

展示列表，让用户决定哪些需要处理、移动或删除。
移动：`~/.claude/skills/obsidian-manager/obsidian-tool inbox --move "标题" --to Study`

---

### 搜索笔记

用户说："搜一下 XXX"、"找找关于 XXX 的笔记"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool search "关键词" --limit 10
```

展示匹配文件列表，带上下文片段。用户要查看全文：
```bash
~/.claude/skills/obsidian-manager/obsidian-tool read "笔记标题"
```

---

### 创建学习/资源笔记

用户说："新建一篇笔记"、"记录一下 XXX 的学习笔记"

```bash
~/.claude/skills/obsidian-manager/obsidian-tool create "笔记标题" --folder Study --content "# 标题\n\n## 概念\n\n## 实践\n"
```

---

## 注意事项

1. **优先使用 CLI**：Path 1 更可靠，减少路径拼写错误风险
2. **日记自动创建**：`--append` 时若日记不存在会自动从模板创建，无需单独 `--create`
3. **Inbox 快速投递**：`--add` 不指定 `--title` 时自动取内容前 30 字作为文件名
4. **iCloud 占位符**：`.icloud` 文件跳过，不读不写
5. **无 frontmatter**：保持轻量风格，创建的笔记不添加 frontmatter
6. **中文路径安全**：Python 天然支持，无需转义
7. **今日日期**：始终从系统获取，不要用固定值
