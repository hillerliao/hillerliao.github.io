#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atom Feed to WordPress Import XML Converter
Generates a WordPress WXR import file from an Atom feed.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import argparse
import os
import re

# Namespaces
ATOM_NS = 'http://www.w3.org/2005/Atom'
NS_MAP = {'atom': ATOM_NS}

def get_text(element, tag, default=''):
    """Helper to get text content from an element"""
    found = element.find(f'atom:{tag}', NS_MAP)
    return found.text if found is not None and found.text else default

def convert_atom_to_wordpress(atom_file, output_file):
    """Convert Atom feed to WordPress XML"""
    
    tree = ET.parse(atom_file)
    root = tree.getroot()
    
    # Create RSS root element
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:excerpt': 'http://wordpress.org/export/1.2/excerpt/',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/',
        'xmlns:wfw': 'http://wellformedweb.org/CommentAPI/',
        'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
        'xmlns:wp': 'http://wordpress.org/export/1.2/'
    })
    
    channel = ET.SubElement(rss, 'channel')
    
    # Feed Info
    title = get_text(root, 'title', 'Imported Blog')
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'link').text = 'https://zhihai.me'
    ET.SubElement(channel, 'description').text = get_text(root, 'subtitle', '')
    ET.SubElement(channel, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(channel, 'language').text = 'zh-CN'
    ET.SubElement(channel, 'wp:wxr_version').text = '1.2'
    
    entries = root.findall('atom:entry', NS_MAP)
    print(f"Found {len(entries)} entries to process.")
    
    for entry in entries:
        item = ET.SubElement(channel, 'item')
        
        # Title
        post_title = get_text(entry, 'title')
        ET.SubElement(item, 'title').text = post_title
        
        # Link & Slug
        # <link href="/slug.html" rel="alternate"></link>
        link_elem = entry.find('atom:link[@rel="alternate"]', NS_MAP)
        if link_elem is not None:
            href = link_elem.get('href', '')
            # Assuming href is like /slug.html or https://domain/slug.html
            # We want to extract 'slug' for wp:post_name
            
            # Simple parsing: get last segment, remove extension
            path = href
            if '://' in path:
                path = path.split('://', 1)[1]
                if '/' in path:
                    path = path.split('/', 1)[1]
            
            # Remove leading slash if present
            path = path.lstrip('/')
            
            slug = path
            if slug.endswith('.html'):
                slug = slug[:-5]
            
            ET.SubElement(item, 'link').text = f'/{slug}.html' # Keep original rule logic if needed, or just link
            ET.SubElement(item, 'wp:post_name').text = slug
            
            # Add custom field for original slug just in case
            postmeta = ET.SubElement(item, 'wp:postmeta')
            ET.SubElement(postmeta, 'wp:meta_key').text = '_custom_final_slug'
            ET.SubElement(postmeta, 'wp:meta_value').text = slug
        
        # Author
        author_elem = entry.find('atom:author/atom:name', NS_MAP)
        creator = author_elem.text if author_elem is not None else 'hillerliao'
        ET.SubElement(item, 'dc:creator').text = creator
        
        # Date
        # <published>2025-02-15T00:00:00+08:00</published>
        published = get_text(entry, 'published')
        if not published:
            published = get_text(entry, 'updated')
            
        try:
            # Parse ISO 8601 format
            # Dealing with timezone might be tricky, stripping for simplicity or parsing if needed
            # Valid format: 2025-02-15T00:00:00+08:00
            if '+' in published:
                dt_str = published.split('+')[0]
            elif 'Z' in published:
                dt_str = published.split('Z')[0]
            else:
                dt_str = published
            
            dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            
            pub_date_fmt = dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
            wp_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            
            ET.SubElement(item, 'pubDate').text = pub_date_fmt
            ET.SubElement(item, 'wp:post_date').text = wp_date
            ET.SubElement(item, 'wp:post_date_gmt').text = wp_date
        except Exception as e:
            print(f"Date parsing error for {post_title}: {e}")
            ET.SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Categories
        for cat in entry.findall('atom:category', NS_MAP):
            term = cat.get('term')
            if term:
                ET.SubElement(item, 'category', {'domain': 'category', 'nicename': term}).text = term
        
        # Content
        content_elem = entry.find('atom:content', NS_MAP)
        content_html = content_elem.text if content_elem is not None else ''
        ET.SubElement(item, 'content:encoded').text = content_html
        
        # Summary/Excerpt
        summary_elem = entry.find('atom:summary', NS_MAP)
        summary_html = summary_elem.text if summary_elem is not None else ''
        ET.SubElement(item, 'excerpt:encoded').text = summary_html
        
        # Other WP fields
        ET.SubElement(item, 'wp:status').text = 'publish'
        ET.SubElement(item, 'wp:post_type').text = 'post'
        ET.SubElement(item, 'wp:post_id').text = str(hash(post_title) % 1000000)
        ET.SubElement(item, 'wp:comment_status').text = 'open'
        ET.SubElement(item, 'wp:ping_status').text = 'open'
        ET.SubElement(item, 'wp:post_parent').text = '0'
        ET.SubElement(item, 'wp:menu_order').text = '0'
        ET.SubElement(item, 'wp:is_sticky').text = '0'
        
        print(f"Processed: {post_title}")

    # Generate pretty XML with CDATA
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    
    # Wrap content in CDATA
    for item in reparsed.getElementsByTagName('item'):
        for node_name in ['content:encoded', 'excerpt:encoded', 'title', 'wp:post_name']:
            nodes = item.getElementsByTagName(node_name)
            if nodes:
                for node in nodes:
                    if node.firstChild:
                        text_content = node.firstChild.data
                        text_content = text_content.replace(']]>', ']]&gt;')
                        cdata = reparsed.createCDATASection(text_content)
                        node.replaceChild(cdata, node.firstChild)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reparsed.toprettyxml(indent='  '))
    
    print(f"\nSuccessfully generated {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Convert Atom feed to WordPress WXR')
    parser.add_argument('--input', '-i', default='temp_atom_feed.xml', help='Input Atom XML file')
    parser.add_argument('--output', '-o', default='wordpress_import_from_feed.xml', help='Output WXR file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Input file {args.input} not found.")
        return
        
    convert_atom_to_wordpress(args.input, args.output)

if __name__ == '__main__':
    main()
