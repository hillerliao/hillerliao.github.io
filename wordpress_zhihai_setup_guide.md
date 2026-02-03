# WordPress zhihai.me URL配置指南

## 1. 导入文章
使用 `wordpress_import_zhihai.xml` 文件导入到WordPress。

## 2. 设置固定链接结构
在WordPress后台：
- 进入"设置" → "固定链接"
- 选择"自定义结构"
- 输入：`/%postname%.html`
- 保存更改

## 3. 添加URL重写规则
将 `wordpress_zhihai_url_rules.php` 中的代码添加到：
- 主题的 `functions.php` 文件，或
- 创建为单独的插件

## 4. 验证URL结构
导入后，文章URL将保持原格式：
- 原格式：`https://zhihai.me/sql-to-csv-converterwei-chan-pin-huo-yun-ying-ren-yuan-da-zao-de-shu-ju-ge-shi-zhuan-huan-li-qi.html`
- 新格式：`https://yoursite.com/sql-to-csv-converterwei-chan-pin-huo-yun-ying-ren-yuan-da-zao-de-shu-ju-ge-shi-zhuan-huan-li-qi.html`

## 5. 刷新重写规则
在WordPress后台：
- 进入"设置" → "固定链接"
- 点击"保存更改"来刷新重写规则

## 6. 测试URL
访问几篇文章确认URL结构正确。

## 注意事项
- 确保WordPress安装在根目录
- 如果安装在子目录，需要相应调整重写规则
- 导入后检查所有文章的slug是否正确
- 如果发现URL包含中文字符，请在文章编辑页面检查“缩略名”(Slug)字段
- 确保没有安装会将标题自动转换为中文拼音或保持中文字符的插件（如 Pinyin Slugs 等）
- .html 后缀将通过重写规则实现

## URL示例
- 原站：`https://zhihai.me/{slug}.html`
- 新站：`https://yoursite.com/{slug}.html`

这样可以完美保持原有的URL结构，避免SEO损失。