# gh CLI 常用命令速查

## 认证

```bash
# 使用 Token 认证（推荐）
export GITHUB_TOKEN=ghp_xxx
GH_TOKEN=$GITHUB_TOKEN gh auth status

# 交互式登录
gh auth login
```

## 仓库

```bash
gh repo view owner/repo                    # 查看仓库概要
gh repo clone owner/repo                   # 克隆仓库
gh repo fork owner/repo                    # Fork 仓库
gh api /repos/owner/repo                   # 获取完整 JSON 信息
gh api /repos/owner/repo/branches          # 列出分支
gh api /repos/owner/repo/releases          # 列出 releases
gh api /repos/owner/repo/tags              # 列出 tags
```

## 文件操作

```bash
# 列出目录
gh api /repos/owner/repo/contents/path

# 读取文件（解码）
gh api /repos/owner/repo/contents/path/to/file --jq '.content' | base64 -d

# 创建文件
gh api /repos/owner/repo/contents/path/to/file \
  -X PUT -f message="commit msg" -f content="$(echo -n 'content' | base64)"

# 获取文件 SHA（更新前需要）
gh api /repos/owner/repo/contents/path/to/file --jq '.sha'

# 更新文件
gh api /repos/owner/repo/contents/path/to/file \
  -X PUT -f message="commit msg" \
  -f content="$(echo -n 'new content' | base64)" \
  -f sha="<current-sha>"

# 删除文件
gh api /repos/owner/repo/contents/path/to/file \
  -X DELETE -f message="remove file" -f sha="<current-sha>"
```

## Issues

```bash
gh issue list --repo owner/repo                      # 列出 open issues
gh issue list --repo owner/repo --state all          # 所有状态
gh issue list --repo owner/repo --label bug          # 按标签
gh issue list --repo owner/repo --assignee @me       # 我的 issues
gh issue view 42 --repo owner/repo                   # 查看详情
gh issue create --repo owner/repo --title "" --body ""
gh issue edit 42 --repo owner/repo --title "" --body ""
gh issue close 42 --repo owner/repo
gh issue reopen 42 --repo owner/repo
gh issue comment 42 --repo owner/repo --body ""
gh issue pin 42 --repo owner/repo                    # 置顶
```

## Pull Requests

```bash
gh pr list --repo owner/repo                         # 列出 open PR
gh pr list --repo owner/repo --state merged          # 已合并
gh pr view 15 --repo owner/repo                      # 查看详情
gh pr diff 15 --repo owner/repo                      # 查看 diff
gh pr create --repo owner/repo --title "" --body "" --base main --head branch
gh pr edit 15 --repo owner/repo --title "" --body ""
gh pr merge 15 --repo owner/repo --merge             # merge commit
gh pr merge 15 --repo owner/repo --squash            # squash
gh pr merge 15 --repo owner/repo --rebase            # rebase
gh pr close 15 --repo owner/repo
gh pr reopen 15 --repo owner/repo
gh pr review 15 --repo owner/repo --approve          # 批准
gh pr review 15 --repo owner/repo --request-changes --body "需要修改..."
gh pr review 15 --repo owner/repo --comment --body "评论"
gh pr checks 15 --repo owner/repo                    # 查看 CI 状态
```

## 搜索

```bash
gh search repos "keyword" --owner username
gh search issues "keyword" --repo owner/repo
gh search code "keyword" --repo owner/repo
```

## 其他

```bash
gh gist list                                         # 列出 gists
gh release list --repo owner/repo                    # 列出 releases
gh release create v1.0.0 --repo owner/repo           # 创建 release
gh workflow list --repo owner/repo                   # 列出 workflows
gh run list --repo owner/repo                        # 列出 workflow runs
```
