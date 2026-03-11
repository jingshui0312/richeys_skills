---
name: github-manager
description: Operate GitHub repositories using the gh CLI. Use this skill whenever the user wants to interact with GitHub — including viewing repo info, browsing files, reading file contents, creating or updating files, managing Issues (list, create, update, close), managing Pull Requests (list, create, review, merge), searching code, or any other GitHub repository task. Trigger whenever the user mentions GitHub, a GitHub URL, a repo they own or watch, issues, PRs, or wants to push/update code on GitHub. Even if they just say "check my repo" or "open a PR" — use this skill.
---

# GitHub Manager

帮助用户通过 `gh` CLI 操作 GitHub 仓库。支持仓库信息查看、文件浏览与编辑、Issues 管理、Pull Requests 管理。

## 环境准备

### Token 认证

优先从环境变量读取 Token：

```bash
echo $GITHUB_TOKEN
```

如果为空，提示用户：
> "请先设置 GitHub Token：`export GITHUB_TOKEN=your_token_here`，或者直接告诉我你的 Token，我会在本次会话中使用它。"

然后用以下方式在当前会话验证：

```bash
GH_TOKEN=$GITHUB_TOKEN gh auth status
```

### 确认 gh CLI 可用

```bash
gh version
```

如果不可用，告知用户安装方式：
- macOS: `brew install gh`
- Linux: `sudo apt install gh` 或查看 https://cli.github.com

---

## 解析仓库信息

用户提到仓库时，可能是以下几种格式，统一解析为 `owner/repo`：

- 完整 URL：`https://github.com/owner/repo` → `owner/repo`
- 简写：`owner/repo` → 直接使用
- 只说名字：询问用户完整仓库路径

所有命令中用 `GH_TOKEN=$GITHUB_TOKEN` 前缀确保 Token 生效（除非用户已经 `gh auth login`）。

---

## 功能操作指南

### 1. 查看仓库信息

```bash
GH_TOKEN=$GITHUB_TOKEN gh repo view owner/repo
```

获取详细 JSON（包括 stars、forks、语言、描述等）：

```bash
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo
```

列出仓库的分支：

```bash
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/branches --jq '.[].name'
```

---

### 2. 浏览文件与目录

列出根目录内容：

```bash
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/ --jq '[.[] | {name: .name, type: .type, size: .size}]'
```

列出子目录：

```bash
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/src --jq '[.[] | {name: .name, type: .type}]'
```

读取文件内容（自动解码 Base64）：

```bash
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/README.md --jq '.content' | base64 -d
```

---

### 3. 创建或更新文件

**创建新文件：**

```bash
CONTENT=$(echo -n "文件内容" | base64)
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/path/to/file.txt \
  -X PUT \
  -f message="feat: add new file" \
  -f content="$CONTENT"
```

**更新已有文件（需要当前文件的 SHA）：**

```bash
# 1. 获取当前文件 SHA
SHA=$(GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/path/to/file.txt --jq '.sha')

# 2. 更新文件
CONTENT=$(echo -n "新内容" | base64)
GH_TOKEN=$GITHUB_TOKEN gh api /repos/owner/repo/contents/path/to/file.txt \
  -X PUT \
  -f message="fix: update file content" \
  -f content="$CONTENT" \
  -f sha="$SHA"
```

**重要提示：**
- 文件内容必须是 Base64 编码
- 更新已有文件时 `sha` 字段是必须的，否则会报 422 错误
- `message` 是 commit message，保持简洁有意义

---

### 4. Issues 管理

**列出 Issues：**

```bash
# 列出所有 open issues
GH_TOKEN=$GITHUB_TOKEN gh issue list --repo owner/repo

# 按状态过滤
GH_TOKEN=$GITHUB_TOKEN gh issue list --repo owner/repo --state closed

# 按标签过滤
GH_TOKEN=$GITHUB_TOKEN gh issue list --repo owner/repo --label bug
```

**查看 Issue 详情：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh issue view 42 --repo owner/repo
```

**创建 Issue：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh issue create \
  --repo owner/repo \
  --title "Issue 标题" \
  --body "Issue 详细描述" \
  --label "bug"
```

**更新 Issue：**

```bash
# 修改标题和内容
GH_TOKEN=$GITHUB_TOKEN gh issue edit 42 \
  --repo owner/repo \
  --title "新标题" \
  --body "新描述"

# 添加标签
GH_TOKEN=$GITHUB_TOKEN gh issue edit 42 --repo owner/repo --add-label "enhancement"

# 指派负责人
GH_TOKEN=$GITHUB_TOKEN gh issue edit 42 --repo owner/repo --add-assignee username
```

**关闭 / 重开 Issue：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh issue close 42 --repo owner/repo
GH_TOKEN=$GITHUB_TOKEN gh issue reopen 42 --repo owner/repo
```

**添加评论：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh issue comment 42 --repo owner/repo --body "评论内容"
```

---

### 5. Pull Requests 管理

**列出 PR：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh pr list --repo owner/repo

# 包括已合并的
GH_TOKEN=$GITHUB_TOKEN gh pr list --repo owner/repo --state merged
```

**查看 PR 详情：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh pr view 15 --repo owner/repo
```

**创建 PR：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh pr create \
  --repo owner/repo \
  --title "PR 标题" \
  --body "## 改动说明\n\n- 修复了 XXX\n- 新增了 YYY" \
  --base main \
  --head feature-branch
```

**审查 PR（添加 Review 评论）：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh pr review 15 \
  --repo owner/repo \
  --comment \
  --body "LGTM！代码看起来不错。"
```

**合并 PR：**

```bash
# Merge commit
GH_TOKEN=$GITHUB_TOKEN gh pr merge 15 --repo owner/repo --merge

# Squash merge
GH_TOKEN=$GITHUB_TOKEN gh pr merge 15 --repo owner/repo --squash

# Rebase merge
GH_TOKEN=$GITHUB_TOKEN gh pr merge 15 --repo owner/repo --rebase
```

**关闭 PR（不合并）：**

```bash
GH_TOKEN=$GITHUB_TOKEN gh pr close 15 --repo owner/repo
```

---

## 错误处理

常见错误及解决方式：

| 错误 | 原因 | 解决 |
|------|------|------|
| `401 Unauthorized` | Token 无效或未设置 | 检查 `$GITHUB_TOKEN` 是否正确 |
| `403 Forbidden` | Token 权限不足 | 在 GitHub 设置中给 Token 增加权限（需要 `repo` scope）|
| `404 Not Found` | 仓库或文件路径不存在 | 检查 `owner/repo` 格式和路径是否正确 |
| `422 Unprocessable` | 更新文件时缺少 SHA | 先获取文件当前 SHA 再更新 |
| `gh: command not found` | gh CLI 未安装 | `brew install gh` 或参考官方文档 |

---

## 操作前确认原则

对于以下**写操作**，执行前必须向用户确认：
- 创建或更新文件（会产生 commit）
- 关闭 Issue 或 PR
- 合并 PR

给用户展示将要执行的命令，确认后再运行。对于只读操作（列出、查看），直接执行无需确认。

---

## 参考文档

更多 gh CLI 用法见 `references/gh-commands.md`（常用命令速查表）。
