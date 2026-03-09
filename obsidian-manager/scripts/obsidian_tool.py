#!/usr/bin/env python3
"""
Obsidian Manager CLI Tool
Pure Python stdlib — no pip dependencies required.
"""

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

VAULT_PATH = Path("/Users/richey.li/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的个人知识库")

FOLDERS = {
    "Daily": VAULT_PATH / "Daily",
    "Inbox": VAULT_PATH / "Inbox",
    "Study": VAULT_PATH / "Study",
    "Resource": VAULT_PATH / "Resource",
    "Canvas": VAULT_PATH / "Canvas",
}

TEMPLATE_PATH = VAULT_PATH / "_Templates" / "Daily Note.md"
DEFAULT_DAILY_SECTION = "今天发生了什么"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def out(data: dict):
    """Print JSON output."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def err(msg: str, code: int = 1):
    out({"ok": False, "error": msg})
    sys.exit(code)


def sanitize_filename(s: str, max_len: int = 40) -> str:
    """Turn arbitrary text into a safe filename (no extension)."""
    # Remove characters that are problematic in filenames
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    s = s.strip()
    return s[:max_len] if s else "untitled"


def resolve_date(spec: str) -> date:
    """Parse 'today', 'yesterday', or YYYY-MM-DD."""
    today = date.today()
    if spec in ("today", ""):
        return today
    if spec == "yesterday":
        return today - timedelta(days=1)
    try:
        return date.fromisoformat(spec)
    except ValueError:
        err(f"Invalid date '{spec}'. Use today/yesterday/YYYY-MM-DD.")


def render_template(tpl: str, note_date: date = None, title: str = "") -> str:
    """Render Obsidian template variables: {{date:YYYY-MM-DD}}, {{title}}, etc."""
    target_date = note_date or date.today()

    def replace_date(m):
        fmt = m.group(1)
        # Convert Obsidian format to strftime
        fmt2 = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        return target_date.strftime(fmt2)

    result = re.sub(r'\{\{date:([^}]+)\}\}', replace_date, tpl)
    result = result.replace("{{title}}", title)
    return result


def parse_frontmatter(content: str) -> tuple:
    """Return (frontmatter_dict, body_str). Vaults without frontmatter return ({}, content)."""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fm_text = content[4:end]
            body = content[end + 5:]
            fm = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    fm[k.strip()] = v.strip()
            return fm, body
    return {}, content


# ─── Path Resolution ──────────────────────────────────────────────────────────

def resolve_note(title_or_path: str, folder: str = None) -> Path | None:
    """
    Find a note by title or path.
    Search order:
      1. Exact path (absolute or relative to vault)
      2. Exact filename match in specified folder
      3. Title substring match in specified folder
      4. Recursive search across whole vault
    Skips iCloud placeholder files (.icloud suffix).
    """
    # 1. Try as absolute or vault-relative path
    p = Path(title_or_path)
    if p.is_absolute() and p.exists():
        return p
    vault_rel = VAULT_PATH / title_or_path
    if vault_rel.exists():
        return vault_rel

    name = title_or_path
    if not name.endswith(".md"):
        name_md = name + ".md"
    else:
        name_md = name

    # Search in specified folder first
    search_dirs = []
    if folder and folder in FOLDERS:
        search_dirs.append(FOLDERS[folder])
    search_dirs.extend(f for k, f in FOLDERS.items() if f not in search_dirs)

    # 2 & 3: Exact then substring match
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.md"):
            if f.suffix == ".icloud":
                continue
            if f.name == name_md:
                return f

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.md"):
            if f.suffix == ".icloud":
                continue
            if name.lower() in f.stem.lower():
                return f

    return None


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_note(title: str, folder: str, content: str = "") -> dict:
    folder_path = FOLDERS.get(folder)
    if folder_path is None:
        err(f"Unknown folder '{folder}'. Valid: {list(FOLDERS.keys())}")

    folder_path.mkdir(parents=True, exist_ok=True)
    note_path = folder_path / (sanitize_filename(title) + ".md")

    if note_path.exists():
        return {"ok": False, "error": f"Note already exists: {note_path.name}", "path": str(note_path)}

    note_path.write_text(content, encoding="utf-8")
    return {"ok": True, "action": "created", "path": str(note_path), "title": title}


def read_note(title_or_path: str, folder: str = None) -> dict:
    p = resolve_note(title_or_path, folder)
    if p is None:
        return {"ok": False, "error": f"Note not found: {title_or_path}"}
    content = p.read_text(encoding="utf-8")
    _, body = parse_frontmatter(content)
    return {
        "ok": True,
        "path": str(p),
        "title": p.stem,
        "folder": p.parent.name,
        "content": body,
        "size": len(content),
    }


def edit_note(title_or_path: str, content: str, folder: str = None) -> dict:
    p = resolve_note(title_or_path, folder)
    if p is None:
        return {"ok": False, "error": f"Note not found: {title_or_path}"}
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "action": "edited", "path": str(p), "title": p.stem}


def append_to_note(title_or_path: str, text: str, section: str = None, folder: str = None) -> dict:
    """
    Append text to a note.
    If section is specified, insert after the matching ## heading.
    Otherwise append at end.
    """
    p = resolve_note(title_or_path, folder)
    if p is None:
        return {"ok": False, "error": f"Note not found: {title_or_path}"}

    content = p.read_text(encoding="utf-8")

    if section:
        # Find section heading and insert after it (and its immediate list items)
        pattern = re.compile(r'^(#{1,6}\s+' + re.escape(section) + r'\s*$)', re.MULTILINE)
        m = pattern.search(content)
        if m:
            insert_pos = m.end()
            # Skip blank line immediately after heading if present
            remainder = content[insert_pos:]
            # Append the new item as a list item on a new line
            new_item = f"\n- {text}"
            content = content[:insert_pos] + new_item + remainder
        else:
            # Section not found — append at end
            content = content.rstrip() + f"\n\n- {text}\n"
    else:
        content = content.rstrip() + f"\n\n- {text}\n"

    p.write_text(content, encoding="utf-8")
    return {"ok": True, "action": "appended", "path": str(p), "title": p.stem, "section": section}


# ─── Daily ────────────────────────────────────────────────────────────────────

def cmd_daily(args) -> dict:
    date_spec = args.date or "today"
    target_date = resolve_date(date_spec)
    filename = target_date.strftime("%Y-%m-%d") + ".md"
    note_path = FOLDERS["Daily"] / filename

    # Read or create
    if not note_path.exists():
        if args.create or args.append:
            # Auto-create from template
            if TEMPLATE_PATH.exists():
                tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
                content = render_template(tpl, note_date=target_date)
            else:
                content = f"# {target_date.isoformat()} 日记\n\n## {DEFAULT_DAILY_SECTION}\n- \n\n## 今天的心情 / 想法\n- \n\n## 今天的微小高光\n- \n\n## 明天想做的事\n- [ ] \n"
            FOLDERS["Daily"].mkdir(parents=True, exist_ok=True)
            note_path.write_text(content, encoding="utf-8")
            result = {"ok": True, "action": "created", "path": str(note_path), "date": target_date.isoformat()}
        else:
            return {"ok": False, "error": f"Daily note not found: {filename}. Use --create to create it."}
    else:
        result = {"ok": True, "action": "read", "path": str(note_path), "date": target_date.isoformat()}

    # Append content if requested
    if args.append:
        section = args.section or DEFAULT_DAILY_SECTION
        append_result = append_to_note(str(note_path), args.append, section=section)
        result.update({"action": "appended", "section": section, "appended": args.append})
        result["ok"] = append_result["ok"]

    # Return content unless write-only op
    content = note_path.read_text(encoding="utf-8")
    result["content"] = content
    return result


# ─── Inbox ────────────────────────────────────────────────────────────────────

def cmd_inbox(args) -> dict:
    inbox_dir = FOLDERS["Inbox"]
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # --add: quick capture
    if args.add:
        title = args.title if args.title else sanitize_filename(args.add, max_len=30)
        note_path = inbox_dir / (title + ".md")
        # If file exists, append; else create
        if note_path.exists():
            content = note_path.read_text(encoding="utf-8")
            content = content.rstrip() + f"\n- {args.add}\n"
            note_path.write_text(content, encoding="utf-8")
            return {"ok": True, "action": "appended", "path": str(note_path), "title": title}
        else:
            note_path.write_text(f"# {title}\n\n- {args.add}\n", encoding="utf-8")
            return {"ok": True, "action": "created", "path": str(note_path), "title": title}

    # --list: show all inbox notes
    if args.list:
        notes = sorted(
            [f for f in inbox_dir.rglob("*.md") if not f.name.endswith(".icloud")],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        items = []
        for f in notes:
            content = f.read_text(encoding="utf-8")
            preview = content.strip().splitlines()
            # Skip H1 title line for preview
            preview_lines = [l for l in preview if not l.startswith("# ")]
            items.append({
                "title": f.stem,
                "path": str(f),
                "preview": preview_lines[0] if preview_lines else "",
                "lines": len(preview),
            })
        return {"ok": True, "count": len(items), "notes": items}

    # --move: move note to another folder
    if args.move:
        dest_folder = args.to
        if dest_folder not in FOLDERS:
            err(f"Unknown destination folder '{dest_folder}'. Valid: {list(FOLDERS.keys())}")
        src = resolve_note(args.move, folder="Inbox")
        if src is None:
            return {"ok": False, "error": f"Note not found in Inbox: {args.move}"}
        dest_dir = FOLDERS[dest_folder]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / src.name
        src.rename(dest_path)
        return {"ok": True, "action": "moved", "from": str(src), "to": str(dest_path)}

    return {"ok": False, "error": "inbox requires --add, --list, or --move"}


# ─── Search ───────────────────────────────────────────────────────────────────

def cmd_search(args) -> dict:
    query = args.query.lower()
    limit = args.limit or 10
    context_lines = args.context or 2
    folder = args.folder

    search_dirs = []
    if folder and folder in FOLDERS:
        search_dirs = [FOLDERS[folder]]
    else:
        search_dirs = list(FOLDERS.values())

    results = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.md"):
            if f.name.endswith(".icloud"):
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except Exception:
                continue

            title_match = query in f.stem.lower()
            content_lower = content.lower()
            content_match = query in content_lower

            if not (title_match or content_match):
                continue

            # Collect matching lines with context
            lines = content.splitlines()
            matches = []
            seen_ranges = set()
            for i, line in enumerate(lines):
                if query in line.lower():
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    range_key = (start, end)
                    if range_key not in seen_ranges:
                        seen_ranges.add(range_key)
                        snippet = "\n".join(lines[start:end])
                        matches.append({"line": i + 1, "snippet": snippet})

            score = (2 if title_match else 0) + len(matches)
            results.append({
                "title": f.stem,
                "path": str(f),
                "folder": f.parent.name,
                "score": score,
                "match_count": len(matches),
                "matches": matches[:5],  # cap per-file matches
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:limit]

    return {"ok": True, "query": args.query, "count": len(results), "results": results}


# ─── List ─────────────────────────────────────────────────────────────────────

def cmd_list(args) -> dict:
    folder = args.folder
    recent = args.recent or 0

    search_dirs = []
    if folder and folder in FOLDERS:
        search_dirs = [FOLDERS[folder]]
    else:
        search_dirs = list(FOLDERS.values())

    notes = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.md"):
            if f.name.endswith(".icloud"):
                continue
            stat = f.stat()
            notes.append({
                "title": f.stem,
                "path": str(f),
                "folder": f.parent.name,
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            })

    notes.sort(key=lambda n: n["mtime"], reverse=True)
    if recent:
        notes = notes[:recent]

    # Convert mtime to readable date
    from datetime import datetime
    for n in notes:
        n["modified"] = datetime.fromtimestamp(n["mtime"]).strftime("%Y-%m-%d %H:%M")
        del n["mtime"]

    return {"ok": True, "count": len(notes), "notes": notes}


# ─── Create / Read / Edit / Append (top-level cmds) ──────────────────────────

def cmd_create(args) -> dict:
    folder = args.folder or "Inbox"
    content = args.content or ""
    return create_note(args.title, folder, content)


def cmd_read(args) -> dict:
    return read_note(args.title_or_path, folder=args.folder)


def cmd_edit(args) -> dict:
    if not args.content:
        err("--content is required for edit")
    return edit_note(args.title_or_path, args.content, folder=args.folder)


def cmd_append(args) -> dict:
    if not args.content:
        err("--content is required for append")
    return append_to_note(args.title_or_path, args.content, section=args.section, folder=args.folder)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="obsidian-tool",
        description="Obsidian vault CLI manager",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # daily
    daily = sub.add_parser("daily", help="Manage daily notes")
    daily.add_argument("date", nargs="?", default="today", help="today/yesterday/YYYY-MM-DD")
    daily.add_argument("--create", action="store_true", help="Create if not exists")
    daily.add_argument("--append", metavar="TEXT", help="Text to append")
    daily.add_argument("--section", metavar="SECTION", help="Section heading to append under")

    # inbox
    inbox = sub.add_parser("inbox", help="Manage Inbox")
    inbox.add_argument("--add", metavar="TEXT", help="Quick capture text")
    inbox.add_argument("--title", metavar="TITLE", help="Override filename for --add")
    inbox.add_argument("--list", action="store_true", help="List inbox notes")
    inbox.add_argument("--move", metavar="TITLE", help="Move note out of inbox")
    inbox.add_argument("--to", metavar="FOLDER", help="Destination folder for --move")

    # create
    create = sub.add_parser("create", help="Create a note")
    create.add_argument("title", help="Note title")
    create.add_argument("--folder", default="Inbox", choices=list(FOLDERS.keys()))
    create.add_argument("--content", metavar="TEXT", help="Initial content")

    # read
    read = sub.add_parser("read", help="Read a note")
    read.add_argument("title_or_path", help="Title or path")
    read.add_argument("--folder", choices=list(FOLDERS.keys()), default=None)

    # edit
    edit = sub.add_parser("edit", help="Replace note content")
    edit.add_argument("title_or_path", help="Title or path")
    edit.add_argument("--content", metavar="TEXT", required=True, help="New full content")
    edit.add_argument("--folder", choices=list(FOLDERS.keys()), default=None)

    # append
    append = sub.add_parser("append", help="Append to a note")
    append.add_argument("title_or_path", help="Title or path")
    append.add_argument("--content", metavar="TEXT", required=True, help="Text to append")
    append.add_argument("--section", metavar="SECTION", help="Section heading to append under")
    append.add_argument("--folder", choices=list(FOLDERS.keys()), default=None)

    # search
    search = sub.add_parser("search", help="Full-text search")
    search.add_argument("query", help="Search query")
    search.add_argument("--folder", choices=list(FOLDERS.keys()), default=None)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--context", type=int, default=2, help="Context lines around match")

    # list
    lst = sub.add_parser("list", help="List notes")
    lst.add_argument("--folder", choices=list(FOLDERS.keys()), default=None)
    lst.add_argument("--recent", type=int, default=0, metavar="N", help="Show N most recent notes")

    return p


COMMANDS = {
    "daily": cmd_daily,
    "inbox": cmd_inbox,
    "create": cmd_create,
    "read": cmd_read,
    "edit": cmd_edit,
    "append": cmd_append,
    "search": cmd_search,
    "list": cmd_list,
}


def main():
    if not VAULT_PATH.exists():
        err(f"Vault not found at: {VAULT_PATH}\nEnsure iCloud is synced.")

    parser = build_parser()
    args = parser.parse_args()

    fn = COMMANDS.get(args.cmd)
    if fn is None:
        err(f"Unknown command: {args.cmd}")

    result = fn(args)
    out(result)


if __name__ == "__main__":
    main()
