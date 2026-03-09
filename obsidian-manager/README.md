# Obsidian Manager Skill

通过 Claude Code 对话式或 CLI 方式管理 iCloud 上的 Obsidian 知识库。

## 功能

- **日记管理**：自动从模板创建今日日记，追加内容到指定 section
- **Inbox 快速投递**：一句话把想法存入 Inbox
- **笔记 CRUD**：创建、读取、编辑、追加任意文件夹下的笔记
- **全文搜索**：标题 + 正文搜索，带上下文片段
- **列出笔记**：按修改时间倒序，支持按文件夹过滤

## 安装

```bash
bash obsidian-manager/install.sh
```

纯 Python 标准库，无需 pip。

## 使用方式

### 方式一：对话触发

在 Claude Code 对话中说出触发词，Claude 会自动调用 CLI 完成操作：

> "写日记" / "记一下 XXX" / "投到 Inbox" / "搜笔记 XXX" / "整理 Inbox"

### 方式二：直接调用 CLI

```bash
TOOL=~/.claude/skills/obsidian-manager/obsidian-tool

# 日记
$TOOL daily today --create                                         # 创建今日日记
$TOOL daily today --append "内容" --section "今天发生了什么"        # 追加到指定 section
$TOOL daily yesterday --create                                     # 昨日日记

# Inbox
$TOOL inbox --add "有个想法需要记下"                               # 快速投递
$TOOL inbox --list                                                 # 查看 Inbox
$TOOL inbox --move "笔记标题" --to Study                           # 移动到其他文件夹

# 笔记操作
$TOOL create "Python 异步编程" --folder Study                      # 创建笔记
$TOOL read "Python 异步编程"                                       # 读取笔记
$TOOL edit "Python 异步编程" --content "新的完整内容"              # 替换全文
$TOOL append "Python 异步编程" --content "补充内容" --section "实践" # 追加到 section

# 搜索 & 列出
$TOOL search "关键词" --limit 10                                   # 全文搜索
$TOOL list --folder Daily --recent 7                               # 最近 7 篇日记
```

所有命令输出 JSON，`ok: true` 表示成功。

## Vault 结构

```
我的个人知识库/
├── Daily/      # 日记，命名格式 YYYY-MM-DD.md
├── Inbox/      # 快速收集
├── Study/      # 学习笔记
├── Resource/   # 资源收藏
├── Canvas/     # 白板
└── _Templates/ # 模板
```

## 依赖

- Python 3.x（macOS 自带）
- iCloud 已同步 Obsidian vault 到本地
