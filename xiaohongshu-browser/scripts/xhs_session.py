#!/usr/bin/env python3
"""
小红书 Playwright 会话管理器

功能：
  check   - 检查会话是否有效（12小时内）
  login   - 二维码扫码登录，通过状态文件与 Claude 通信
  browse  - 使用已保存的会话浏览页面
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

HOME = Path.home()
SESSION_DIR = HOME / ".xhs_session"
SESSION_FILE = SESSION_DIR / "session.json"
STATUS_FILE = Path("/tmp/xhs_login_status.json")
QR_CODE_FILE = Path("/tmp/xhs_qrcode.png")

SESSION_MAX_AGE = 12 * 3600  # 12小时

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
"""


# ─── 会话管理 ────────────────────────────────────────────────────────────────

def is_session_valid() -> bool:
    if not SESSION_FILE.exists():
        return False
    try:
        data = json.loads(SESSION_FILE.read_text())
        return time.time() - data.get("saved_at", 0) < SESSION_MAX_AGE
    except Exception:
        return False


def load_session_state() -> dict:
    data = json.loads(SESSION_FILE.read_text())
    # 去掉自定义字段，只保留 Playwright storage_state 结构
    return {k: v for k, v in data.items() if k not in ("saved_at", "expires_at")}


def write_status(status: dict):
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2))
    # 同时打印到 stdout 方便调试
    print(f"[STATUS] {json.dumps(status, ensure_ascii=False)}", flush=True)


# ─── 登录流程 ─────────────────────────────────────────────────────────────────

async def capture_qrcode(page) -> bool:
    """截取页面二维码，保存到 QR_CODE_FILE（带白边，方便扫码）"""
    # 优先用已知精确选择器，再依次 fallback
    selectors = [
        ".qrcode-img",           # 小红书已知选择器
        ".qrcode img",
        "[class*='qrcode'] img",
        "[class*='QRCode'] img",
        "img[src*='qrcode']",
        "[class*='qr-code'] img",
        "canvas[class*='qr']",
        ".login-container img",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=2000):
                # 截取二维码，加 20px padding 白边
                await el.screenshot(path=str(QR_CODE_FILE))
                _add_padding(QR_CODE_FILE, padding=20)
                return True
        except Exception:
            continue

    # 兜底：截取整个页面
    await page.screenshot(path=str(QR_CODE_FILE))
    return False


def _add_padding(img_path: Path, padding: int = 20):
    """给二维码截图加白色边框，让扫码更容易"""
    try:
        import struct, zlib, io

        # 只对 PNG 做简单处理；失败就跳过
        data = img_path.read_bytes()
        # 用 Pillow（如果有）
        try:
            from PIL import Image, ImageOps
            img = Image.open(str(img_path)).convert("RGBA")
            padded = ImageOps.expand(img, border=padding, fill=(255, 255, 255, 255))
            padded.save(str(img_path))
        except ImportError:
            pass  # Pillow 没装就算了，原图也能扫
    except Exception:
        pass


async def is_logged_in(page) -> bool:
    """检测是否已登录（二维码弹窗消失 + Cookie 或用户元素出现）"""
    try:
        result = await page.evaluate("""() => {
            // 登录弹窗消失是最可靠的信号
            const loginModal = document.querySelector(
                '.login-container, .login-wrapper, [class*="loginModal"], ' +
                '[class*="login-modal"], .qrcode-container'
            );
            if (loginModal && loginModal.getBoundingClientRect().height > 0) {
                // 弹窗还在，说明还没登录
                return false;
            }

            // 检查登录 Cookie（HttpOnly Cookie 在 JS 里看不到，但部分可以）
            if (document.cookie.includes('web_session') ||
                document.cookie.includes('customer-sso-sid') ||
                document.cookie.includes('xsecappid')) {
                return true;
            }

            // 检查用户头像等登录态 DOM 元素
            const loggedInSelectors = [
                '.user-info', '.avatar', '[class*="userAvatar"]',
                '[class*="user-avatar"]', 'a[href*="/user/profile"]',
                '.side-bar .user', '[data-type="me"]',
            ];
            return loggedInSelectors.some(sel => {
                const el = document.querySelector(sel);
                return el && el.getBoundingClientRect().width > 0;
            });
        }""")
        return bool(result)
    except Exception:
        return False


async def do_login(headed: bool = False):
    """打开浏览器，展示二维码，等待用户扫码，保存会话"""
    from playwright.async_api import async_playwright

    write_status({"status": "starting", "message": "正在启动浏览器..."})

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not headed,
            args=BROWSER_ARGS,
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=USER_AGENT,
        )
        await context.add_init_script(STEALTH_SCRIPT)
        page = await context.new_page()

        try:
            write_status({"status": "navigating", "message": "正在打开小红书..."})
            await page.goto(
                "https://www.xiaohongshu.com",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await page.wait_for_timeout(3000)

            # 尝试点击「二维码登录」标签（如果存在）
            qr_tab_selectors = [
                "text=扫码登录",
                "text=二维码登录",
                "[class*='qrcode-tab']",
                ".tab-item:has-text('扫码')",
            ]
            for sel in qr_tab_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1500):
                        await el.click()
                        await page.wait_for_timeout(1000)
                        break
                except Exception:
                    continue

            # 等待二维码出现，然后截图
            await page.wait_for_timeout(2000)
            found_qr = await capture_qrcode(page)

            write_status({
                "status": "qr_ready",
                "qr_path": str(QR_CODE_FILE),
                "found_qr_element": found_qr,
                "message": "请用小红书 App 扫描二维码登录",
            })

            # 轮询登录状态，最多等待 120 秒
            # 每 30 秒刷新一次二维码截图（二维码会过期）
            start = time.time()
            last_refresh = start

            while time.time() - start < 120:
                if await is_logged_in(page):
                    break

                # 每 30 秒重新截取二维码（防止过期）
                if time.time() - last_refresh >= 30:
                    await capture_qrcode(page)
                    write_status({
                        "status": "qr_ready",
                        "qr_path": str(QR_CODE_FILE),
                        "found_qr_element": found_qr,
                        "message": "二维码已刷新，请重新扫描",
                    })
                    last_refresh = time.time()

                await asyncio.sleep(2)
            else:
                write_status({"status": "timeout", "message": "登录超时（120秒），请重新运行 login"})
                print("登录超时", file=sys.stderr)
                return

            # ── 保存会话 ──────────────────────────────────────────────────────
            write_status({"status": "saving", "message": "正在保存会话..."})
            state = await context.storage_state()

            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            session_data = {
                **state,
                "saved_at": time.time(),
                "expires_at": time.time() + SESSION_MAX_AGE,
            }
            SESSION_FILE.write_text(
                json.dumps(session_data, ensure_ascii=False, indent=2)
            )

            write_status({
                "status": "logged_in",
                "message": "✅ 登录成功！会话已保存（有效期 12 小时）",
                "session_file": str(SESSION_FILE),
                "expires_in_hours": 12,
            })
            print("登录成功！会话已保存。")

        except Exception as e:
            write_status({"status": "error", "message": str(e)})
            print(f"错误: {e}", file=sys.stderr)
            raise
        finally:
            await browser.close()


# ─── 浏览页面 ─────────────────────────────────────────────────────────────────

async def do_browse(
    url: str,
    screenshot_path: str | None = None,
    extract_text: bool = False,
    js_eval: str | None = None,
    scroll_pages: int = 0,
    click_title: str | None = None,
    scroll_comment: int = 0,
):
    """使用已保存的会话浏览页面。

    click_title: 在搜索结果中找到标题含此字符串的笔记并点击（自动携带 xsec_token）
    scroll_comment: 滚动右侧评论面板 N 次（笔记详情页专用）
    """
    from playwright.async_api import async_playwright

    if not is_session_valid():
        print("❌ 没有有效的会话，请先执行 login 命令。", file=sys.stderr)
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await browser.new_context(
            storage_state=load_session_state(),
            viewport={"width": 1280, "height": 900},
            user_agent=USER_AGENT,
        )
        await context.add_init_script(STEALTH_SCRIPT)
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # 点击指定标题的笔记卡片（从搜索结果进入，自动携带 xsec_token）
            if click_title:
                cards = await page.query_selector_all('section.note-item')
                clicked = False
                for card in cards:
                    title_el = await card.query_selector('.title span')
                    if title_el:
                        text = await title_el.inner_text()
                        if click_title in text:
                            print(f"点击笔记: {text.strip()}")
                            await card.click()
                            await page.wait_for_timeout(4000)
                            clicked = True
                            break
                if not clicked:
                    print(f"⚠️ 未找到标题含「{click_title}」的笔记", file=sys.stderr)

            # 用 mouse.wheel 滚动主页面（搜索结果、信息流等）
            for _ in range(scroll_pages):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(1500)

            # 滚动右侧评论面板（笔记详情页专用，鼠标移到右侧面板区域）
            if scroll_comment > 0:
                await page.mouse.move(890, 400)
                await page.wait_for_timeout(300)
                for _ in range(scroll_comment):
                    await page.mouse.wheel(0, 500)
                    await page.wait_for_timeout(800)

            if screenshot_path:
                await page.screenshot(path=screenshot_path, full_page=False)
                print(f"截图已保存: {screenshot_path}")

            if extract_text:
                text = await page.evaluate("""() => {
                    document.querySelectorAll('script,style,nav,header,footer').forEach(el => el.remove());
                    return document.body.innerText.trim();
                }""")
                print("=== 页面文字内容 ===")
                print(text)

            if js_eval:
                result = await page.evaluate(js_eval)
                print("=== JS 执行结果 ===")
                print(json.dumps(result, ensure_ascii=False, indent=2))

            title = await page.title()
            print(f"页面标题: {title}")
            print(f"当前 URL: {page.url}")

        finally:
            await browser.close()


# ─── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="小红书 Playwright 会话管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # check
    sub.add_parser("check", help="检查会话是否有效")

    # login
    login_p = sub.add_parser("login", help="二维码扫码登录")
    login_p.add_argument(
        "--headed", action="store_true",
        help="有头模式（显示浏览器窗口），在本地终端直接运行时使用"
    )

    # browse
    browse_p = sub.add_parser("browse", help="用已保存会话浏览页面")
    browse_p.add_argument("url", help="要访问的 URL")
    browse_p.add_argument("--screenshot", metavar="PATH", help="截图保存路径")
    browse_p.add_argument("--text", action="store_true", help="提取页面文字")
    browse_p.add_argument("--js", metavar="EXPR", help="在页面执行 JS 表达式")
    browse_p.add_argument(
        "--scroll", type=int, default=0, metavar="N", help="向下滚动主页面 N 次（每次 600px）"
    )
    browse_p.add_argument(
        "--click-title", metavar="TITLE", help="点击搜索结果中标题含此字符串的笔记（自动携带 xsec_token）"
    )
    browse_p.add_argument(
        "--scroll-comment", type=int, default=0, metavar="N", help="滚动右侧评论面板 N 次（笔记详情页专用）"
    )

    args = parser.parse_args()

    if args.cmd == "check":
        if is_session_valid():
            data = json.loads(SESSION_FILE.read_text())
            remaining = SESSION_MAX_AGE - (time.time() - data["saved_at"])
            print(f"✅ 会话有效，还剩 {remaining / 3600:.1f} 小时")
            sys.exit(0)
        else:
            print("❌ 没有有效的会话")
            sys.exit(1)

    elif args.cmd == "login":
        asyncio.run(do_login(headed=args.headed))

    elif args.cmd == "browse":
        asyncio.run(
            do_browse(
                args.url,
                screenshot_path=args.screenshot,
                extract_text=args.text,
                js_eval=args.js,
                scroll_pages=args.scroll,
                click_title=args.click_title,
                scroll_comment=args.scroll_comment,
            )
        )


if __name__ == "__main__":
    main()
