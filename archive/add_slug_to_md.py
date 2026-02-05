#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有Markdown文章添加slug字段
如果文件已有slug字段，保持不变
如果文件有urlname字段，转换为slug字段
如果文件没有slug字段，从title生成slug
"""

import os
import re
import unicodedata

def slugify(text):
    """
    将标题转换为slug
    中文使用pypinyin转换为拼音，英文保持原样
    """
    try:
        from pypinyin import pinyin, Style
        has_pypinyin = True
    except ImportError:
        has_pypinyin = False

    # 首先处理特殊字符
    char_map = {
        '：': ' ', '，': ' ', '。': ' ', '！': ' ', '？': ' ',
        '（': ' ', '）': ' ', '【': ' ', '】': ' ', '《': ' ', '》': ' ',
        '、': ' ', '；': ' ', '“': ' ', '”': ' ', '‘': ' ', '’': ' ',
        ' ': '-', '_': '-', '/': '-', '\\': '-', '|': '-',
        '[': '-', ']': '-', '{': '-', '}': '-', '(': '-', ')': '-'
    }

    result = text.strip()
    for old, new in char_map.items():
        result = result.replace(old, new)

    # 分割成单词/字符
    parts = []
    current_word = ''

    for char in result:
        if char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
            current_word += char
        else:
            if current_word:
                parts.append(current_word.lower())
                current_word = ''
            # 处理中文字符
            if has_pypinyin and '\u4e00' <= char <= '\u9fff':
                # 中文字符，转换为拼音
                py = pinyin(char, style=Style.NORMAL)[0][0]
                parts.append(py)
            elif not has_pypinyin and '\u4e00' <= char <= '\u9fff':
                # 没有pypinyin，用简单的字母代替
                parts.append('cn')
            # 其他字符忽略

    if current_word:
        parts.append(current_word.lower())

    # 连接并清理
    slug = '-'.join(parts)
    # 移除多余的连字符
    while '--' in slug:
        slug = slug.replace('--', '-')
    slug = slug.strip('-')

    return slug if slug else 'untitled'

def parse_frontmatter(content):
    """解析Markdown文件的frontmatter"""
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    # 解析frontmatter
    metadata = {}
    lines = frontmatter_text.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # 处理多行值和列表
            if value.startswith('[') and value.endswith(']'):
                # 这是一个列表，保持原样
                metadata[key] = value
            else:
                # 移除引号
                value = value.strip("'\"")
                metadata[key] = value

    return metadata, body

def update_frontmatter(metadata, body, new_slug=None):
    """更新frontmatter，添加或更新slug字段"""
    lines = []

    # 处理每个字段，保持原有格式
    for key, value in metadata.items():
        if key == 'slug' and new_slug:
            lines.append(f'slug: {new_slug}')
        elif key == 'urlname':
            # 将urlname转换为slug
            if new_slug:
                lines.append(f'slug: {new_slug}')
            else:
                lines.append(f'slug: {value}')
        else:
            lines.append(f'{key}: {value}')

    # 如果没有slug字段，添加它
    if 'slug' not in metadata and new_slug:
        lines.append(f'slug: {new_slug}')

    # 如果有urlname但没有slug，需要移除urlname或转换
    if 'urlname' in metadata and 'slug' not in metadata:
        # 已经在上面处理了
        pass

    frontmatter = '\n'.join(lines)
    return f'---\n{frontmatter}\n---\n\n{body}'

def process_file(filepath):
    """处理单个Markdown文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 解析frontmatter
    metadata, body = parse_frontmatter(content)

    if metadata is None:
        print(f"跳过 {filepath} - 没有有效的frontmatter")
        return False

    # 检查是否已有slug字段
    if 'slug' in metadata:
        print(f"跳过 {filepath} - 已有slug字段: {metadata['slug']}")
        return False

    # 确定要使用的slug
    new_slug = None

    if 'urlname' in metadata:
        # 从urlname转换
        new_slug = metadata['urlname']
        print(f"处理 {filepath} - 从urlname转换: {new_slug}")
    elif 'title' in metadata:
        # 从title生成
        title = metadata['title']
        new_slug = slugify(title)
        print(f"处理 {filepath} - 从title生成: {title} -> {new_slug}")
    else:
        print(f"跳过 {filepath} - 没有title或urlname")
        return False

    # 更新文件内容
    updated_content = update_frontmatter(metadata, body, new_slug)

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    return True

def main():
    blog_dir = 'content/blog'

    if not os.path.exists(blog_dir):
        print(f"目录不存在: {blog_dir}")
        return

    processed = 0
    skipped = 0

    for filename in os.listdir(blog_dir):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(blog_dir, filename)
        if process_file(filepath):
            processed += 1
        else:
            skipped += 1

    print(f"\n处理完成!")
    print(f"已处理: {processed} 个文件")
    print(f"已跳过: {skipped} 个文件")

if __name__ == '__main__':
    main()
