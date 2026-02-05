-- WordPress 批量修改文章 slug 的 SQL 脚本
-- 使用前请务必备份数据库！

-- 方法 1: 根据 post_name 和 post_title 的映射关系批量更新
-- 先运行这个查询查看将要修改的内容
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
  AND p.post_name != pm.meta_value;

-- 确认无误后，执行更新
UPDATE wp_posts p
INNER JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_custom_final_slug'
SET p.post_name = pm.meta_value
WHERE p.post_type = 'post'
  AND p.post_status = 'publish'
  AND pm.meta_value IS NOT NULL
  AND p.post_name != pm.meta_value;

-- 方法 2: 如果没有 _custom_final_slug 字段，根据 post_title 重新生成 slug
-- 先查看将要修改的内容
SELECT
    ID,
    post_title,
    post_name,
    -- 模拟生成的新 slug (需要根据实际规则调整)
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(post_title, '：', '-'), '，', '-'), '。', '-'), ' ', '-')) as new_slug
FROM wp_posts
WHERE post_type = 'post'
  AND post_status = 'publish';

-- 方法 3: 清理 WordPress 缓存和重定向
-- 删除旧的重定向记录（如果使用了重定向插件）
-- DELETE FROM wp_redirection_items WHERE url LIKE '%.html';

-- 重置重定向缓存
-- UPDATE wp_options SET option_value = '' WHERE option_name = 'redirection_cache';
