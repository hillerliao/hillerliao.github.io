#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pelican to WordPress 转换工具
将 Pelican Markdown 文章转换为 WordPress 导入 XML 格式
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
import argparse

def parse_frontmatter(content):
    """解析 Markdown 文章的 frontmatter"""
    # 分离 frontmatter 和正文
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    # 解析 frontmatter
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            metadata[key] = value
    
    return metadata, body

def convert_to_wordpress_xml(md_files, output_file):
    """将 Markdown 文件转换为 WordPress XML"""
    
    # 创建 RSS 根元素
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:excerpt': 'http://wordpress.org/export/1.2/excerpt/',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/',
        'xmlns:wfw': 'http://wellformedweb.org/CommentAPI/',
        'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
        'xmlns:wp': 'http://wordpress.org/export/1.2/'
    })
    
    channel = ET.SubElement(rss, 'channel')
    
    # 添加频道信息
    ET.SubElement(channel, 'title').text = '廖智海博客导入'
    ET.SubElement(channel, 'link').text = 'https://hillerliao.github.io'
    ET.SubElement(channel, 'description').text = '从 Pelican 导入的文章'
    ET.SubElement(channel, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(channel, 'language').text = 'zh-CN'
    ET.SubElement(channel, 'wp:wxr_version').text = '1.2'
    
    # 处理每个 Markdown 文件
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 frontmatter 和正文
            metadata, body = parse_frontmatter(content)
            
            # 创建 item 元素
            item = ET.SubElement(channel, 'item')
            
            # 标题
            title = metadata.get('title', os.path.basename(md_file).replace('.md', ''))
            ET.SubElement(item, 'title').text = title
            
            # 链接 - 使用相对路径
            # 优先从 metadata 获取 slug 或 urlname
            slug = metadata.get('slug', metadata.get('urlname'))
            if not slug:
                # 如果都没有，使用文件名
                slug = os.path.basename(md_file).replace('.md', '')
            
            ET.SubElement(item, 'link').text = f'/{slug}.html'
            
            # 发布日期
            date_str = metadata.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))
            try:
                if len(date_str) == 16:
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                else:
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                ET.SubElement(item, 'pubDate').text = pub_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
            except:
                ET.SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # 创建者
            creator = metadata.get('authors', metadata.get('author', 'hillerliao'))
            ET.SubElement(item, 'dc:creator').text = creator
            
            # 分类和标签
            category = metadata.get('category', 'blog')
            ET.SubElement(item, 'category', {'domain': 'category', 'nicename': category}).text = category
            
            # 处理标签
            tags = metadata.get('tags', '')
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                for tag in tag_list:
                    ET.SubElement(item, 'category', {'domain': 'post_tag', 'nicename': tag}).text = tag
            
            # 内容 (转换为 HTML)
            html_content = markdown_to_html(body)
            ET.SubElement(item, 'content:encoded').text = html_content
            
            # 摘要
            summary = metadata.get('summary', '')
            if summary:
                ET.SubElement(item, 'excerpt:encoded').text = summary
            else:
                # 如果没有摘要，取正文前100个字符
                excerpt = body.replace('\n', ' ').strip()[:100] + '...'
                ET.SubElement(item, 'excerpt:encoded').text = excerpt
            
            # WordPress 特定信息
            ET.SubElement(item, 'wp:post_id').text = str(hash(md_file) % 1000000)
            ET.SubElement(item, 'wp:post_date').text = date_str
            ET.SubElement(item, 'wp:post_date_gmt').text = date_str
            ET.SubElement(item, 'wp:comment_status').text = 'open'
            ET.SubElement(item, 'wp:ping_status').text = 'open'
            ET.SubElement(item, 'wp:post_name').text = slug  # 使用slug作为post_name来保持URL
            ET.SubElement(item, 'wp:status').text = 'publish'
            ET.SubElement(item, 'wp:post_parent').text = '0'
            ET.SubElement(item, 'wp:menu_order').text = '0'
            ET.SubElement(item, 'wp:post_type').text = 'post'
            ET.SubElement(item, 'wp:post_password').text = ''
            ET.SubElement(item, 'wp:is_sticky').text = '0'
            
            # 添加自定义字段来保存原始slug
            postmeta = ET.SubElement(item, 'wp:postmeta')
            ET.SubElement(postmeta, 'wp:meta_key').text = '_custom_slug'
            ET.SubElement(postmeta, 'wp:meta_value').text = slug
            
            # 分类信息
            ET.SubElement(item, 'category', {'domain': 'category', 'nicename': category}).text = category
            
            print(f"已处理: {title}")
            
        except Exception as e:
            print(f"处理文件 {md_file} 时出错: {e}")
            continue
    
    # 美化 XML 输出并处理 CDATA
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    
    # 将 content:encoded 和 excerpt:encoded 转换为 CDATA
    for item in reparsed.getElementsByTagName('item'):
        for node_name in ['content:encoded', 'excerpt:encoded']:
            nodes = item.getElementsByTagName(node_name)
            if nodes and nodes[0].firstChild:
                # 获取原始文本
                text_content = nodes[0].firstChild.data
                
                # 处理 CDATA 中不允许的 ']]>'
                # 将 ']]>' 替换为 ']]&gt;' 是一种简单的方法，虽然 CDATA 不解析实体，
                # 但 WordPress 在导入时通常能处理这种情况，或者我们可以暂时这样处理。
                # 更好的做法是拆分 CDATA，但 minidom 比较死板。
                # 这里我们采用简单替换，因为在 HTML 中将 > 替换为 &gt; 是安全的。
                text_content = text_content.replace(']]>', ']]&gt;')
                
                # 创建 CDATA 节点
                cdata = reparsed.createCDATASection(text_content)
                # 替换原始文本节点
                nodes[0].replaceChild(cdata, nodes[0].firstChild)
    
    pretty_xml = reparsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"\n转换完成! 输出文件: {output_file}")
    print(f"共转换了 {len(md_files)} 篇文章")

def markdown_to_html(markdown_text):
    """简单的 Markdown 到 HTML 转换"""
    html = markdown_text
    
    # 标题转换
    html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 粗体和斜体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # 代码块
    html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 图片
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', html)
    
    # 段落
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<'):
            para = f'<p>{para}</p>'
        html_paragraphs.append(para)
    
    return '\n\n'.join(html_paragraphs)

def main():
    parser = argparse.ArgumentParser(description='Pelican to WordPress 转换工具')
    parser.add_argument('--input', '-i', default='content/blog', help='输入目录 (默认: content/blog)')
    parser.add_argument('--output', '-o', default='wordpress_import.xml', help='输出文件 (默认: wordpress_import.xml)')
    
    args = parser.parse_args()
    
    # 查找所有 Markdown 文件
    md_files = []
    if os.path.isdir(args.input):
        for root, dirs, files in os.walk(args.input):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
    else:
        md_files = [args.input]
    
    if not md_files:
        print(f"在 {args.input} 中没有找到 Markdown 文件")
        return
    
    print(f"找到 {len(md_files)} 个 Markdown 文件")
    
    # 转换为 WordPress XML
    convert_to_wordpress_xml(md_files, args.output)

if __name__ == '__main__':
    main()