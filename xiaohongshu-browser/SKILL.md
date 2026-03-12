---
name: xiaohongshu-browser
description: >
  使用 Playwright 浏览小红书（Xiaohongshu / 小红书 / RED）。自动处理登录：截取二维码并展示给用户，用户用手机扫码完成登录，会话保持 12 小时。
  支持搜索笔记、查看帖子、截图、提取文字内容等操作。
  当用户提到小红书、xhs、xiaohongshu、RED App，或想要浏览/搜索/抓取小红书内容时，务必使用本 skill。
  即使用户只说"帮我看看小红书上的XXX"或"搜一下小红书"，也要触发本 skill。
---

# 小红书浏览器 Skill

通过 Playwright 操控浏览器访问小红书，支持二维码扫码登录和 12 小时会话保持。

## 前置检查

首先确认 Playwright 已安装：

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('ok')" 2>/dev/null || \
  (pip3 install playwright --break-system-packages && playwright install chromium)
```

---

## 完整工作流

### 第一步：检查会话

```bash
python3 <skill-path>/scripts/xhs_session.py check
```

- 退出码 `0` → 会话有效，直接跳到**浏览页面**
- 退出码 `1` → 需要登录，继续第二步

### 第二步：二维码登录

> **重要**：登录脚本需要在后台运行，同时轮询状态展示二维码。使用 shell `&` 后台运行（兼容所有 AI 驱动环境）。

**2a. 后台启动登录 + 等待二维码就绪（一条命令完成）：**

```bash
# 清理旧状态文件，后台启动登录脚本，等待二维码就绪
rm -f /tmp/xhs_login_status.json /tmp/xhs_qrcode.png
python3 <skill-path>/scripts/xhs_session.py login > /tmp/xhs_login.log 2>&1 &
echo $! > /tmp/xhs_login.pid
python3 -c "
import json, time, sys
for _ in range(30):
    try:
        d = json.loads(open('/tmp/xhs_login_status.json').read())
        if d.get('status') in ('qr_ready', 'logged_in', 'error', 'timeout'):
            print(json.dumps(d, ensure_ascii=False))
            sys.exit(0)
    except: pass
    time.sleep(2)
print('timeout waiting for qr_ready')
sys.exit(1)
"
```

**2b. 展示二维码给用户：**

当上一步状态为 `qr_ready` 时，使用 **Read 工具**读取并展示图片：
- 图片路径：`/tmp/xhs_qrcode.png`
- 告诉用户：**"请打开小红书 App，点击右上角扫一扫，扫描上方二维码完成登录"**

**2c. 轮询等待登录完成：**

```bash
python3 -c "
import json, time, sys
for _ in range(60):
    try:
        d = json.loads(open('/tmp/xhs_login_status.json').read())
        status = d.get('status', '')
        print(f'状态: {status}', flush=True)
        if status == 'logged_in':
            print('登录成功！')
            sys.exit(0)
        if status in ('error', 'timeout'):
            print('登录失败:', d.get('message'))
            sys.exit(1)
        # qr_ready 说明还在等待扫码，继续等待，不要重启登录流程
    except: pass
    time.sleep(3)
print('等待超时')
sys.exit(1)
"
```

> **注意**：看到 `qr_ready` 状态时**不要重启登录**，这是正常的等待扫码状态（二维码每 30 秒自动刷新）。
> 若用户说二维码过期，重新用 Read 工具读取 `/tmp/xhs_qrcode.png` 展示最新二维码即可。

### 第三步：浏览页面

```bash
# 截图
python3 <skill-path>/scripts/xhs_session.py browse "https://www.xiaohongshu.com" \
    --screenshot /tmp/xhs_page.png

# 搜索并截图
python3 <skill-path>/scripts/xhs_session.py browse \
    "https://www.xiaohongshu.com/search_result?keyword=穿搭&type=normal" \
    --screenshot /tmp/xhs_search.png --scroll 2

# 提取页面文字
python3 <skill-path>/scripts/xhs_session.py browse \
    "https://www.xiaohongshu.com/search_result?keyword=美食" \
    --text

# 截图 + 提取文字
python3 <skill-path>/scripts/xhs_session.py browse "<url>" \
    --screenshot /tmp/xhs_result.png --text
```

截图完成后，**用 Read 工具读取 PNG 文件展示给用户**。

### 打开笔记详情

> **重要**：小红书笔记详情页需要 `xsec_token` 参数，直接访问 `/explore/<id>` 会被重定向。
> 必须先进入搜索结果页，再用 `--click-title` 点击笔记卡片，浏览器自动携带 token。

```bash
# 搜索后点击指定笔记（--click-title 支持模糊匹配标题关键词）
python3 <skill-path>/scripts/xhs_session.py browse \
    "https://www.xiaohongshu.com/search_result?keyword=MacBook&type=normal" \
    --click-title "粉色" \
    --screenshot /tmp/xhs_note.png --text

# 打开笔记后滚动评论区（--scroll-comment 滚动右侧评论面板）
python3 <skill-path>/scripts/xhs_session.py browse \
    "https://www.xiaohongshu.com/search_result?keyword=MacBook&type=normal" \
    --click-title "粉色" \
    --screenshot /tmp/xhs_note.png \
    --scroll-comment 5
```

**标准流程**：
1. 先搜索（不带 `--click-title`），看清标题
2. 再搜索 + `--click-title 关键词` 打开目标笔记
3. 如需查看更多评论，加 `--scroll-comment N`

---

## 常用 URL 格式

| 操作 | URL |
|------|-----|
| 首页 | `https://www.xiaohongshu.com` |
| 搜索笔记 | `https://www.xiaohongshu.com/search_result?keyword=<关键词>&type=normal` |
| 搜索用户 | `https://www.xiaohongshu.com/search_result?keyword=<关键词>&type=user` |
| 用户主页 | `https://www.xiaohongshu.com/user/profile/<user-id>` |
| 发现页 | `https://www.xiaohongshu.com/explore` |

---

## 会话信息

- 会话文件：`~/.xhs_session/session.json`
- 有效期：12 小时（从登录成功起计算）
- 会话过期后，重新执行登录流程即可

---

## 常见问题处理

**二维码截图不清晰 / 找不到二维码元素**
→ 重新运行步骤 2a，或直接读取 `/tmp/xhs_qrcode.png` 检查是否已更新（脚本每 30 秒刷新）

**登录超时（120秒内未扫码）**
→ 重新运行 `login` 命令

**会话失效（小红书服务端踢出）**
→ 运行 `check` 确认，然后重新 `login`

**页面内容加载不完整**
→ 使用 `--scroll N` 参数向下滚动 N 屏以触发懒加载
