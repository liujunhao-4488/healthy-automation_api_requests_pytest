# -*- coding: utf-8 -*-
"""
权威语料入库（ingest）—— 把 权威文件/*.pdf 和 *.md 变成检索器能吃的 JSON
======================================================================
这一步在 RAG 里叫 **ingest（数据摄取）**，是整条链路里最容易被忽略、
却最决定成败的一环：检索器再好，喂进去的块切错了，召回就是错的。

职责链条（只做前两段，检索是 kb_retriever 的事）：

    权威文件/*.pdf  +  *.md
        ↓ ① extract   PDF 用 pypdf 抽每页文字；md 直接读文本
        ↓ ② clean     去页眉/页脚/页码（PDF）、去图片与分隔线（md）
        ↓ ③ section   PDF 按「一、二、三」「（一）（二）」猜章节；
                      md 按 `#` 标题切（显式结构，不用猜）
        ↓ ④ chunk     章节内按长度切块（带重叠），复用 kb_retriever 的切法
        ↓
    kb_data/authority_chunks.json   ← 派生物，随时可重跑重建

⚠️ **两种格式走两条解析路径，但出口是同一个**（都产出 [{name, text}]，
   后面共同走 split_into_chunks）。为什么不硬凑成一套：
   PDF 抽出来的是没有结构的行，"章节"只能靠中文序号猜；
   md 的标题是显式 `#`，按它切最准。硬合并反而两边都做不好。

⭐ 为什么原文（PDF）和派生物（JSON）要分开存
----------------------------------------------------------------------
  换嵌入模型、改切块参数、加一批新文档，都要**重跑这一整个脚本**。
  只要 PDF 还在，一切都能重建；反之若只留 JSON，原文的溯源信息就丢了。
  答辩要问"语料哪来的"——答案是指向 PDF，不是指向 JSON。

用法：
    algorithm\\.venv\\Scripts\\python.exe ingest_authority.py --probe   # 只看统计，不写文件
    algorithm\\.venv\\Scripts\\python.exe ingest_authority.py           # 正式生成 JSON
"""

import argparse
import json
import os
import re
import sys

from pypdf import PdfReader

# 让本脚本能 import 同级目录的切块函数 —— 切块逻辑**只允许有一处实现**，
# 否则「文档入库怎么切」和「检索怎么切」两套参数一打架，召回率就没法解释。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_retriever import split_into_chunks  # noqa: E402

# ══════════════════════════════════════════════════════════════════════
SOURCE_DIR = r"D:/jiankang/healthy/权威文件"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "authority_chunks.json")

# 页眉页脚噪声的常见形态：纯页码、纯短横线、只有数字和空格
_PAGE_NUMBER = re.compile(r"^\s*[-—–\s]*\d{1,3}\s*[-—–\s]*$")
_BLANK = re.compile(r"[ \t\u3000]+")
_MULTI_NEWLINE = re.compile(r"\n{2,}")

# 章节标题：一、 / （一） / 1. / 第一章
_SEC_H1 = re.compile(r"^\s*[一二三四五六七八九十]+\s*[、.．]")
_SEC_H2 = re.compile(r"^\s*[（(]\s*[一二三四五六七八九十]+\s*[)）]")
_MD_TITLE = re.compile(r"^\s*第[一二三四五六七八九十]+章")

# ⚠️ 目录行：「一、前言 ......... 1」这种点号引导 + 行尾页码。
#    必须单独识别并丢弃 —— 否则它既会被 _SEC_H1 误判成章节标题，
#    又会把一堆没有正文内容的标题塞进索引，稀释检索分数。
#    实测这批 PDF 的引导符有点号、间隔号、省略号三种形态。
_TOC_LINE = re.compile(r"[.·…_]{3,}\s*\d{1,3}\s*$")

# ── Markdown 专用（2026-10-16 起支持 .md 语料）──────────────────────
# 标题：`# xxx` ~ `###### xxx`。取第一个捕获组当章节名。
_MD_HEAD = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
# 噪声行：内嵌图片、水平分隔线（`------`）、注释。这些是排版痕迹，不是内容。
_MD_NOISE = re.compile(r"^(<img[\s>]|<!--|[-=*_]{3,}$)")


def _is_toc_line(line):
    return bool(_TOC_LINE.search(line))


def _is_toc_page(lines):
    """一页里出现 4 行以上目录行，判定为目录页（整页丢弃）。"""
    return sum(1 for line in lines if _is_toc_line(line)) >= 4
# ══════════════════════════════════════════════════════════════════════


def extract_pages(pdf_path):
    """抽取 PDF 每页文字，返回 [(页码, 原始文本), ...]（页码从 1 开始）。"""
    reader = PdfReader(pdf_path)
    pages = []
    for index, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:                       # 单页失败不能让整篇挂掉
            print("   ⚠️ 第 %d 页抽取失败: %s" % (index, exc))
            text = ""
        pages.append((index, text))
    return pages


def clean_text(text, book_title=""):
    """
    清洗一页文字。

    实测这批 PDF 的噪声形态：
      · 页码单独成行（"7" / "- 19 -"）
      · 书名字样重复出现在页眉
      · 中文排版的行尾是硬换行，被 pypdf 抽成一堆空白
    清洗的**尺度**要克制：宁可留一点噪声，也别把正文切没。
    """
    lines = []
    for raw_line in text.split("\n"):
        line = _BLANK.sub(" ", raw_line).strip()
        if not line:
            continue
        if _PAGE_NUMBER.match(line):        # 页码行
            continue
        if book_title and line == book_title:   # 页眉=书名
            continue
        lines.append(line)
    return "\n".join(lines)


def guess_title_and_year(pdf_name, first_page_text):
    """从文件名 + 首页文字推断书名和版本年份。"""
    title = os.path.splitext(pdf_name)[0]
    year = ""
    match = re.search(r"(\d{4})\s*年", first_page_text or "")
    if match:
        year = match.group(1)
    else:
        match = re.search(r"(\d{4})", title)
        if match:
            year = match.group(1)
    return title, year


def split_sections(pages):
    """
    把「页 → 文本」整理成「章节 → 文本」。

    章节标题单独成行时（一、二、三 / （一）（二）），它既能当导航，
    又该**留在正文里**——因为「减钠增钾」这种词常常只出现在标题，
    标题丢了检索就召回不到（这正是 kb_retriever 里把 title 并进正文的同一理由）。
    """
    sections = []           # [{name, text}]
    current_name = "正文"
    buffer = []
    skipped_toc_pages = 0

    for page_no, text in pages:
        page_lines = [line.strip() for line in text.split("\n") if line.strip()]
        if _is_toc_page(page_lines):     # 目录页整页跳过
            skipped_toc_pages += 1
            continue
        for line in page_lines:
            if _is_toc_line(line):       # 零散的目录行也丢掉
                continue
            if _SEC_H1.match(line) or _MD_TITLE.match(line):
                # 顶层标题：开新章节
                if buffer:
                    sections.append({"name": current_name, "text": "\n".join(buffer)})
                    buffer = []
                current_name = line
                buffer.append(line)
            elif _SEC_H2.match(line) and len(line) <= 40:
                # 二级标题：不新开章节，但前置空行帮助切块时识别断点
                buffer.append(line)
            else:
                buffer.append(line)
    if buffer:
        sections.append({"name": current_name, "text": "\n".join(buffer)})
    sections = [s for s in sections if _is_real_section(s)]
    return sections, skipped_toc_pages


def _is_real_section(section):
    """丢掉只有标题、没有正文的碎片章节（目录页残留的典型形态）。"""
    body = "\n".join(
        line for line in section["text"].split("\n")
        if line.strip() != section["name"].strip()
    )
    return len(body.strip()) >= 60


def ingest_one(pdf_path):
    """处理单篇 PDF，返回 chunk 列表。"""
    pdf_name = os.path.basename(pdf_path)
    pages = extract_pages(pdf_path)
    first_text = pages[0][1] if pages else ""
    title, year = guess_title_and_year(pdf_name, first_text)

    cleaned = [(no, clean_text(text, title)) for no, text in pages]
    sections, toc_pages = split_sections(cleaned)

    # docId：给权威文档一个**独立于 health_article 的 id 空间**。
    # 用字符串前缀区分来源，检索结果里一眼看得出"这条是官方指南还是站内文章"。
    doc_id = "guideline:" + title

    chunks = []
    for section in sections:
        section_name = _BLANK.sub("", section["name"])[:40]   # 章节名去掉排版空白
        for piece in split_into_chunks(section["text"]):
            if len(piece.strip()) < 30:      # 太短的块多半是残页/噪声，不入索引
                continue
            chunks.append({
                "docId": doc_id,
                "docTitle": title,
                "year": year,
                "sourceType": "authority",     # ⭐ 双源架构的标记位
                "docType": "guideline",        # PDF = 官方指南
                "section": section_name,
                "text": piece,
            })
    return {
        "file": pdf_name,
        "title": title,
        "year": year,
        "pages": len(pages),
        "tocPages": toc_pages,
        "chars": sum(len(t) for _, t in cleaned),
        "sections": [s["name"] for s in sections],
        "chunks": chunks,
    }


# ══════════════════════════════════════════════════════════════════════
# Markdown 语料
# ══════════════════════════════════════════════════════════════════════

def split_md_sections(md_path):
    """
    读 Markdown，按 `#` 标题切成章节，返回 [{name, text}]。

    和 PDF 那套的关键差别：**md 的章节是显式的**（`# 准则五 少盐少油，控糖限酒`），
    不需要靠"行首是一二三、"去猜。所以这里不做任何猜测，只按标题切。

    两个刻意的处理：
      · 标题文字**保留在正文里**（buffer.append(current_name)）——
        理由同 PDF：`控糖` 这种词恰恰只在标题出现过，标题丢了就召回不到；
      · 文件开头的 `<img>` 和 `------` 直接丢 —— 它们是排版痕迹，
        留在索引里会稀释分数（实测同一份 pdf 的目录页污染是同类问题）。
    """
    with open(md_path, "r", encoding="utf-8") as handle:
        raw_lines = handle.read().split("\n")

    sections = []
    current_name = "正文"
    buffer = []

    for raw_line in raw_lines:
        line = _BLANK.sub(" ", raw_line).strip()
        if not line or _MD_NOISE.match(line):
            continue
        heading = _MD_HEAD.match(line)
        if heading:
            if buffer:
                sections.append({"name": current_name, "text": "\n".join(buffer)})
                buffer = []
            current_name = heading.group(1).strip()
            buffer.append(current_name)          # 标题进正文（见上）
            continue
        buffer.append(line)

    if buffer:
        sections.append({"name": current_name, "text": "\n".join(buffer)})

    sections = [s for s in sections if _is_real_section(s)]
    return sections


def ingest_one_markdown(md_path):
    """处理单个 .md，返回与 ingest_one 同形的 dict（调用方不用分支）。"""
    md_name = os.path.basename(md_path)
    title, year = guess_title_and_year(md_name, "")
    sections = split_md_sections(md_path)

    # docId 前缀与 PDF 一致 —— 对检索器来说它们都是 "authority" 源。
    doc_id = "guideline:" + title

    chunks = []
    for section in sections:
        section_name = _BLANK.sub("", section["name"])[:40]
        for piece in split_into_chunks(section["text"]):
            if len(piece.strip()) < 30:      # 与 PDF 侧同一个下限
                continue
            chunks.append({
                "docId": doc_id,
                "docTitle": title,
                "year": year,
                "sourceType": "authority",
                # 编号 .md（12_控糖饮食建议等）是站内整理的摘要，不是官方指南；
                # 《中国居民膳食指南(2022)》虽然不是编号文件，但属于官方指南。
                "docType": "summary" if re.match(r"^\d+_", title) else "guideline",
                "section": section_name,
                "text": piece,
            })

    return {
        "file": md_name,
        "title": title,
        "year": year,
        "pages": 0,                          # md 没有"页"的概念，用 0 占位
        "tocPages": 0,
        "chars": sum(len(s["text"]) for s in sections),
        "sections": [s["name"] for s in sections],
        "chunks": chunks,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", help="只打印统计，不写文件")
    args = parser.parse_args()

    if not os.path.isdir(SOURCE_DIR):
        print("❌ 未找到目录: %s" % SOURCE_DIR)
        return 1

    source_files = sorted(
        f for f in os.listdir(SOURCE_DIR)
        if f.lower().endswith((".pdf", ".md"))
    )
    if not source_files:
        print("❌ %s 里没有 PDF / MD" % SOURCE_DIR)
        return 1

    pdf_count = sum(1 for f in source_files if f.lower().endswith(".pdf"))
    md_count = len(source_files) - pdf_count
    print("发现 %d 份语料（PDF %d + MD %d）\n" % (len(source_files), pdf_count, md_count))

    all_chunks = []
    total_pages = total_chars = 0

    for file_name in source_files:
        path = os.path.join(SOURCE_DIR, file_name)
        if file_name.lower().endswith(".pdf"):
            result = ingest_one(path)
            unit = "%3d页" % result["pages"]
            total_pages += result["pages"]
        else:
            result = ingest_one_markdown(path)
            unit = "  md "                      # markdown 没有页的概念
        total_chars += result["chars"]
        all_chunks.extend(result["chunks"])
        print("%-40s %s %6d字 → %3d块" % (
            result["title"][:38], unit, result["chars"], len(result["chunks"])
        ))
        if args.probe:
            print("      章节: %s" % " | ".join(result["sections"][:8]))

    print()
    print("═" * 70)
    print("合计：%d 份 / %d 页 / %d 字 → **%d 个 chunk**" % (
        len(source_files), total_pages, total_chars, len(all_chunks)
    ))

    lengths = [len(c["text"]) for c in all_chunks]
    if lengths:
        print("块长：min=%d  max=%d  平均=%d" % (
            min(lengths), max(lengths), sum(lengths) // len(lengths)
        ))
    empty = sum(1 for L in lengths if L < 30)
    print("过短的块（<30 字，疑似噪声块）: %d" % empty)

    if args.probe:
        print("\n—— 抽样 3 块 ——")
        step = max(1, len(all_chunks) // 4)
        for chunk in all_chunks[::step][:3]:
            print("\n[%s | %s]" % (chunk["docTitle"], chunk["section"]))
            print("  %s" % chunk["text"][:150].replace("\n", " / "))
        return 0

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    payload = {
        "source": "国家卫生健康委办公厅 食养指南系列 + 中国营养学会《中国居民膳食指南(2022)》",
        "chunkCount": len(all_chunks),
        "chunks": all_chunks,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
    print("\n✅ 已写出: %s" % OUTPUT_FILE)
    print("   文件大小: %.1f KB" % (os.path.getsize(OUTPUT_FILE) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
