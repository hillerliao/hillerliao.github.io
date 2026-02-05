<?php
/*
 * WordPress URL重写规则 - zhihai.me风格
 * 用于保持与原博客相同的URL结构: https://zhihai.me/{slug}.html
 * 
 * 将此代码添加到主题的functions.php文件中
 * 或者创建为单独的插件
 */

// 添加自定义重写规则 - 支持 .html 后缀
function add_zhihai_url_rewrite_rules() {
    add_rewrite_rule(
        '^([^/]+)\.html$',
        'index.php?name=$matches[1]',
        'top'
    );
}
add_action('init', 'add_zhihai_url_rewrite_rules');

// 确保WordPress能够处理这些URL
function custom_post_type_link($post_link, $post) {
    if ($post->post_type == 'post') {
        // 检查是否有自定义的slug
        $slug = get_post_meta($post->ID, '_custom_slug', true);
        if ($slug) {
            return home_url("/{$slug}.html");
        }
    }
    return $post_link;
}
add_filter('post_link', 'custom_post_type_link', 10, 2);

// 保存自定义slug
function save_custom_slug($post_id) {
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (wp_is_post_revision($post_id)) return;
    
    if (isset($_POST['custom_slug'])) {
        update_post_meta($post_id, '_custom_slug', sanitize_text_field($_POST['custom_slug']));
    }
}
add_action('save_post', 'save_custom_slug');

// 在后台添加自定义slug字段
function add_custom_slug_field() {
    add_meta_box(
        'custom_slug_field',
        'URL Slug (用于保持原URL)',
        'custom_slug_field_callback',
        'post',
        'normal',
        'high'
    );
}
add_action('add_meta_boxes', 'add_custom_slug_field');

function custom_slug_field_callback($post) {
    wp_nonce_field(basename(__FILE__), 'custom_slug_nonce');
    $custom_slug = get_post_meta($post->ID, '_custom_slug', true);
    echo '<label for="custom_slug">URL Slug:</label>';
    echo '<input type="text" id="custom_slug" name="custom_slug" value="' . esc_attr($custom_slug) . '" size="50" />';
    echo '<p class="description">这将用于生成 /{slug}.html 格式的URL，保持与原zhihai.me博客一致</p>';
}

// 设置固定的permalink结构 - 支持 .html 后缀
function set_custom_permalink_structure() {
    global $wp_rewrite;
    $wp_rewrite->set_permalink_structure('/%postname%.html');
}
add_action('init', 'set_custom_permalink_structure');

// 刷新重写规则（激活主题时）
function flush_rewrite_rules_on_theme_activation() {
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'flush_rewrite_rules_on_theme_activation');

// 移除WordPress默认的URL结构
function remove_default_permalink_structure() {
    global $wp_rewrite;
    $wp_rewrite->pagination_base = 'page';
    $wp_rewrite->comments_pagination_base = 'comment-page';
}
add_action('init', 'remove_default_permalink_structure');

?>