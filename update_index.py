#!/usr/bin/env python3
"""
update_index.py — Ibin! Notes Site 主页一键更新脚本
====================================================
用法：
    python3 update_index.py              # 扫描目录并重新生成 index.html
    python3 update_index.py --push       # 生成后自动 git add/commit/push
    python3 update_index.py --dry-run    # 仅预览，不写入文件

功能：
    1. 扫描本项目目录下所有子文件夹中的 .html 文件
    2. 尝试从 <title> 或 <h1> 标签提取文档标题
    3. 读取 docs_config.json 获取文档描述（可选）
    4. 自动更新 index.html 中的文档卡片区域
    5. 更新统计数字（文档数量、领域数量）
    6. 支持 git push
"""

import os
import re
import json
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html import escape


# ─── 配置 ────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent.resolve()
INDEX_FILE    = SCRIPT_DIR / "index.html"
CONFIG_FILE   = SCRIPT_DIR / "docs_config.json"
IGNORE_FILES  = {"index.html"}
IGNORE_DIRS   = {".git", ".github", "assets", "static", "__pycache__", "node_modules"}

# 每个子文件夹的展示配置
FOLDER_CONFIG = {
    "MLA_DSA": {
        "label":    "MLA_DSA — 多头潜在注意力与 DSA",
        "emoji":    "🧠",
        "css_class": "mla-section",
        "default_tag": "MLA",
    },
    "De_Attn": {
        "label":    "De_Attn — Decode Attention 优化",
        "emoji":    "⚙️",
        "css_class": "attn-section",
        "default_tag": "Attn",
    },
}

# 如果文件夹不在上面的配置里，使用这个默认值
DEFAULT_FOLDER_ICON = {
    "css_class": "mla-section",
    "emoji": "📁",
    "default_tag": "Notes",
}

# 文件名 → (emoji, 标题, 描述, tag) 的映射，优先级高于自动提取
FILE_META = {
    "MLA_Best_Operators":               ("🏆", "MLA 最优算子设计",              "探讨 MLA 注意力计算中最优算子的选择策略，分析不同实现方案的性能权衡。",               "MLA · Operators"),
    "MLA_DSA_Inference_Guide":          ("📘", "MLA DSA 推理指南",              "完整的 MLA DSA 推理流程指南，涵盖从模型加载到高效推理的全链路优化方案。",            "MLA · Inference"),
    "MLA_GEMM_Visual":                  ("📊", "MLA GEMM 可视化分析",           "通过交互式可视化展示 MLA 中 GEMM 操作的矩阵变换过程，直观理解计算流程。",           "MLA · GEMM"),
    "MLA_Matrix_Absorption":            ("🔗", "MLA 矩阵吸收原理",              "深入解析 MLA 的矩阵吸收技术，理解其如何减少 KV Cache 显存占用。",                    "MLA · KV Cache"),
    "MLA_Prefix_Cache_ChunkedPrefill":  ("⚡", "MLA Prefix Cache & Chunked Prefill", "MLA 场景下 Prefix Cache 与 Chunked Prefill 的结合应用，提升长序列推理吞吐量。", "MLA · Prefill"),
    "MLA_Simplified_Diagram":           ("🗺️", "MLA 简化架构图解",              "以简化的架构图形式呈现 MLA 的整体结构，适合快速建立直觉认知。",                    "MLA · Architecture"),
    "RoPE_Variants_Comparison":         ("🔄", "RoPE 位置编码变体对比",          "系统比较 RoPE 各变体在长序列外推上的表现与适用场景。",                              "RoPE · Variants"),
    "flash_decoding_guide":             ("💥", "Flash Decoding 推理优化指南",    "Flash Decoding 算法详解，揭示其如何通过并行化 KV 维度大幅提升解码吞吐。",           "Flash Decoding"),
    "cute_divide_ops_v1":               ("🔨", "CuTe 分块操作详解（v1）",        "CuTe 库中分块操作的原理与实现，版本一：基础概念与核心 API 介绍。",                   "CuTe · Divide"),
    "cute_divide_ops_v2":               ("🔧", "CuTe 分块操作详解（v2）",        "CuTe 分块操作进阶篇，版本二：深入 Tiling 策略与实战 kernel 示例。",                 "CuTe · Advanced"),
    "rope_comparison_guide":            ("📐", "RoPE 实现对比指南",              "对比不同 RoPE 实现方案在解码场景下的精度、性能与工程可用性。",                      "RoPE · Decode"),
}
# ─────────────────────────────────────────────────────────


def get_cn_time() -> str:
    """返回中国时间字符串 YYYY-MM-DD"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d")


def extract_html_title(filepath: Path) -> str:
    """从 HTML 文件中提取 <title> 或第一个 <h1> 作为标题"""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")[:8000]
        m = re.search(r"<title[^>]*>\s*(.+?)\s*</title>", content, re.IGNORECASE | re.DOTALL)
        if m:
            t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if t and len(t) < 120:
                return t
        m = re.search(r"<h1[^>]*>\s*(.+?)\s*</h1>", content, re.IGNORECASE | re.DOTALL)
        if m:
            t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if t and len(t) < 120:
                return t
    except Exception:
        pass
    return ""


def stem_key(filename: str) -> str:
    """filename (without .html) → lookup key, strip hash suffix"""
    # Remove hash suffix like '-a0e79449'
    s = re.sub(r"-[0-9a-f]{8}$", "", Path(filename).stem)
    return s


def get_file_meta(folder: str, filename: str, filepath: Path):
    """Returns (emoji, title, desc, tag) for a given html file."""
    key = stem_key(filename)
    if key in FILE_META:
        return FILE_META[key]
    # Try config file
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            folder_cfg = cfg.get(folder, {})
            if filename in folder_cfg:
                fc = folder_cfg[filename]
                return (fc.get("emoji","📄"), fc.get("title", key),
                        fc.get("desc",""), fc.get("tag", folder))
        except Exception:
            pass
    # Auto-extract title
    auto_title = extract_html_title(filepath) or key.replace("_", " ")
    fc = FOLDER_CONFIG.get(folder, DEFAULT_FOLDER_ICON)
    return ("📄", auto_title, "", fc["default_tag"])


def render_card(href: str, emoji: str, title: str, desc: str, tag: str) -> str:
    return f"""
      <a class="card" href="{escape(href)}" target="_blank">
        <div class="card-emoji">{emoji}</div>
        <div class="card-title">{escape(title)}</div>
        <div class="card-desc">{escape(desc)}</div>
        <div class="card-footer">
          <span class="card-tag">{escape(tag)}</span>
          <span class="card-arrow">→</span>
        </div>
      </a>"""


def render_section(folder: str, files: list[tuple[str, Path]]) -> str:
    """Render a full section block for a folder."""
    fc = FOLDER_CONFIG.get(folder, {
        "label": folder,
        "emoji": "📁",
        "css_class": "mla-section",
        "default_tag": folder,
    })
    count = len(files)
    cards_html = ""
    for filename, filepath in sorted(files):
        emoji, title, desc, tag = get_file_meta(folder, filename, filepath)
        href = f"{folder}/{filename}"
        cards_html += render_card(href, emoji, title, desc, tag)

    return f"""  <!-- AUTO-SECTION:{folder}:START -->
  <div class="section {fc['css_class']}" data-section="{folder.lower().replace('_','-')}">
    <div class="section-header">
      <div class="section-icon">{fc['emoji']}</div>
      <div>
        <div class="section-title">{fc['label']}</div>
      </div>
      <span class="section-subtitle section-tag">{count} 篇文档</span>
    </div>
    <div class="cards-grid">
{cards_html}
    </div>
  </div>
  <!-- AUTO-SECTION:{folder}:END -->"""


def scan_folders() -> dict[str, list[tuple[str, Path]]]:
    """Scan project directory for html files grouped by folder."""
    result: dict[str, list] = {}

    # Known folders first (preserve display order)
    ordered_folders = list(FOLDER_CONFIG.keys())

    for item in sorted(SCRIPT_DIR.iterdir()):
        if not item.is_dir():
            continue
        if item.name in IGNORE_DIRS or item.name.startswith("."):
            continue

        html_files = sorted([
            (f.name, f)
            for f in item.glob("*.html")
            if f.name not in IGNORE_FILES
        ])
        if html_files:
            result[item.name] = html_files

    # Return in ordered fashion
    ordered = {}
    for k in ordered_folders:
        if k in result:
            ordered[k] = result.pop(k)
    # Append any new folders
    ordered.update(result)
    return ordered


def update_index(dry_run: bool = False) -> tuple[int, int]:
    """
    Update index.html with fresh content.
    Returns (total_docs, total_sections).
    """
    if not INDEX_FILE.exists():
        print(f"❌ index.html 不存在：{INDEX_FILE}")
        return 0, 0

    content = INDEX_FILE.read_text(encoding="utf-8")
    folders = scan_folders()

    total_docs = sum(len(v) for v in folders.values())
    total_sections = len(folders)

    print(f"📁 发现 {total_sections} 个文件夹，共 {total_docs} 篇 HTML 文档")
    for folder, files in folders.items():
        print(f"   {folder}/  ({len(files)} 篇):")
        for fname, _ in files:
            print(f"      - {fname}")

    # ── Replace AUTO-SECTION blocks ──
    # Remove all existing AUTO-SECTION blocks
    content = re.sub(
        r"\s*<!-- AUTO-SECTION:[^:]+:START -->.*?<!-- AUTO-SECTION:[^:]+:END -->",
        "",
        content,
        flags=re.DOTALL,
    )

    # Build new sections HTML
    new_sections = "\n".join(render_section(f, files) for f, files in folders.items())

    # Insert before <!-- No results -->
    insert_marker = "  <!-- No results -->"
    if insert_marker in content:
        content = content.replace(insert_marker, f"\n{new_sections}\n\n  {insert_marker[2:]}")
    else:
        # Fallback: insert before </main>
        content = content.replace("</main>", f"\n{new_sections}\n\n</main>")

    # ── Update stats ──
    content = re.sub(
        r'(<span class="stat-num" id="totalDocs">)\d+(</span>)',
        rf"\g<1>{total_docs}\g<2>",
        content,
    )
    content = re.sub(
        r'(<span class="stat-num">)\d+(</span>\s*<span class="stat-label">技术领域)',
        rf"\g<1>{total_sections}\g<2>",
        content,
    )

    # ── Update date ──
    today = get_cn_time()
    content = re.sub(
        r"(最近更新：<strong[^>]*>)\d{4}-\d{2}-\d{2}(</strong>)",
        rf"\g<1>{today}\g<2>",
        content,
    )

    # ── Update JS totalDocs fallback ──
    content = re.sub(
        r"(document\.getElementById\('totalDocs'\)\.textContent = query \? totalVisible : )\d+",
        rf"\g<1>{total_docs}",
        content,
    )

    if dry_run:
        print("\n🔍 Dry-run 模式，不写入文件。预览前 200 字符：")
        print(content[:200])
        return total_docs, total_sections

    INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"\n✅ index.html 已更新（{today}）")
    print(f"   文档总数：{total_docs}  |  领域数：{total_sections}")
    return total_docs, total_sections


def git_push():
    """Add, commit and push changes."""
    today = get_cn_time()
    cmds = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"docs: update index {today}"],
        ["git", "push"],
    ]
    for cmd in cmds:
        print(f"$ {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0:
            print(f"⚠️  命令失败: {result.stderr.strip()}")
            break
    else:
        print("🚀 已推送到远程仓库！")


def main():
    parser = argparse.ArgumentParser(
        description="Ibin! Notes Site — 主页一键更新脚本"
    )
    parser.add_argument("--push",    action="store_true", help="更新后自动 git push")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    args = parser.parse_args()

    print("=" * 50)
    print("  Ibin! Notes — 主页更新脚本")
    print("=" * 50)

    total, sections = update_index(dry_run=args.dry_run)

    if args.push and not args.dry_run and total > 0:
        print()
        git_push()

    print("\n完成！")


if __name__ == "__main__":
    main()
