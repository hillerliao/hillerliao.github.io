#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress 批量修改文章 slug 的 Python 脚本
使用前请务必备份数据库！
"""

import mysql.connector
from mysql.connector import Error

# 数据库配置 - 请根据实际情况修改
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'wordpress_db',
    'charset': 'utf8mb4'
}

def connect_db():
    """连接数据库"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ 数据库连接成功")
            return connection
    except Error as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def preview_changes(conn):
    """预览将要修改的 slug"""
    cursor = conn.cursor(dictionary=True)

    # 方法1: 根据 _custom_final_slug meta 字段更新
    query = """
    SELECT
        p.ID,
        p.post_title,
        p.post_name,
        pm.meta_value as custom_slug
    FROM wp_posts p
    LEFT JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_custom_final_slug'
    WHERE p.post_type = 'post'
      AND p.post_status = 'publish'
      AND pm.meta_value IS NOT NULL
      AND p.post_name != pm.meta_value
    """

    print("\n" + "="*80)
    print("【预览】方法1: 使用 _custom_final_slug 字段")
    print("="*80)

    cursor.execute(query)
    results = cursor.fetchall()

    if not results:
        print("没有需要修改的文章")
    else:
        print(f"共 {len(results)} 篇文章需要修改:\n")
        for row in results:
            print(f"ID: {row['ID']}")
            print(f"  原标题: {row['post_title']}")
            print(f"  当前slug: {row['post_name']}")
            print(f"  目标slug: {row['custom_slug']}")
            print()

    # 方法2: 根据标题重新生成 slug
    query2 = """
    SELECT
        ID,
        post_title,
        post_name
    FROM wp_posts
    WHERE post_type = 'post'
      AND post_status = 'publish'
      AND post_name != post_title
    """

    print("\n" + "="*80)
    print("【预览】方法2: 根据标题重新生成 slug")
    print("="*80)

    cursor.execute(query2)
    results2 = cursor.fetchall()

    if not results2:
        print("没有需要修改的文章")
    else:
        print(f"共 {len(results2)} 篇文章需要修改:\n")
        for row in results2:
            new_slug = generate_slug(row['post_title'])
            print(f"ID: {row['ID']}")
            print(f"  标题: {row['post_title']}")
            print(f"  当前slug: {row['post_name']}")
            print(f"  新slug: {new_slug}")
            print()

    cursor.close()
    return len(results) > 0 or len(results2) > 0

def generate_slug(title):
    """根据标题生成 slug (保持中文字符)"""
    import re

    # 移除特殊字符，保留中文、英文、数字、连字符
    slug = title.lower()

    # 替换中文标点符号为连字符
    replace_chars = {
        '：': '-', '，': '-', '。': '-', '！': '-', '？': '-',
        '（': '-', '）': '-', '【': '-', '】': '-',
        '、': '-', '；': '-', '“': '-', '”': '-'
    }

    for old, new in replace_chars.items():
        slug = slug.replace(old, new)

    # 替换空格和特殊字符为连字符
    slug = re.sub(r'[ \/\|_]+', '-', slug)

    # 移除连续的连字符
    slug = re.sub(r'-+', '-', slug)

    # 移除首尾的连字符
    slug = slug.strip('-')

    return slug

def update_with_custom_slug(conn):
    """使用 _custom_final_slug 字段更新"""
    cursor = conn.cursor()

    query = """
    UPDATE wp_posts p
    INNER JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_custom_final_slug'
    SET p.post_name = pm.meta_value
    WHERE p.post_type = 'post'
      AND p.post_status = 'publish'
      AND pm.meta_value IS NOT NULL
      AND p.post_name != pm.meta_value
    """

    try:
        cursor.execute(query)
        affected = cursor.rowcount
        conn.commit()
        print(f"✅ 方法1更新完成，共修改 {affected} 篇文章")
        return affected
    except Error as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
        return 0

def update_with_generated_slug(conn):
    """根据标题重新生成 slug 并更新"""
    cursor = conn.cursor(dictionary=True)

    # 先查询需要更新的文章
    query = """
    SELECT ID, post_title, post_name
    FROM wp_posts
    WHERE post_type = 'post'
      AND post_status = 'publish'
    """

    cursor.execute(query)
    results = cursor.fetchall()

    updated = 0
    for row in results:
        new_slug = generate_slug(row['post_title'])
        if new_slug != row['post_name']:
            update_query = "UPDATE wp_posts SET post_name = %s WHERE ID = %s"
            try:
                cursor.execute(update_query, (new_slug, row['ID']))
                updated += 1
            except Error as e:
                print(f"❌ 更新 ID {row['ID']} 失败: {e}")

    conn.commit()
    cursor.close()
    print(f"✅ 方法2更新完成，共修改 {updated} 篇文章")
    return updated

def clear_cache(conn):
    """清理 WordPress 缓存"""
    cursor = conn.cursor()

    # 删除旧的重定向记录（如果使用了重定向插件）
    # cursor.execute("DELETE FROM wp_redirection_items WHERE url LIKE '%.html'")

    # 重置重定向缓存
    cursor.execute("UPDATE wp_options SET option_value = '' WHERE option_name = 'redirection_cache'")

    # 清除其他可能的缓存
    cursor.execute("UPDATE wp_options SET option_value = '' WHERE option_name LIKE '%cache%'")

    conn.commit()
    cursor.close()
    print("✅ 缓存清理完成")

def main():
    print("="*80)
    print("WordPress 批量修改文章 slug 工具")
    print("="*80)
    print("⚠️  重要提示: 操作前请务必备份数据库！\n")

    conn = connect_db()
    if not conn:
        return

    # 预览
    has_changes = preview_changes(conn)

    if not has_changes:
        print("\n没有需要修改的文章")
        conn.close()
        return

    # 询问用户选择
    print("\n请选择操作:")
    print("1. 使用 _custom_final_slug 字段更新")
    print("2. 根据标题重新生成 slug")
    print("3. 两种方法都执行")
    print("4. 仅清理缓存")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == '0':
        print("已取消")
    elif choice == '1':
        update_with_custom_slug(conn)
        clear_cache(conn)
    elif choice == '2':
        update_with_generated_slug(conn)
        clear_cache(conn)
    elif choice == '3':
        update_with_custom_slug(conn)
        update_with_generated_slug(conn)
        clear_cache(conn)
    elif choice == '4':
        clear_cache(conn)
    else:
        print("无效选项")

    conn.close()
    print("\n操作完成！")

if __name__ == '__main__':
    main()
