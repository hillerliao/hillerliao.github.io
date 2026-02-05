AUTHOR = "hillerliao"
SITENAME = "廖智海"
SITESUBTITLE = "互联网产品折腾师"
SITEURL = ""

PATH = "content"
ARTICLE_PATHS = ["blog"]

TIMEZONE = "Asia/Shanghai"

# 你原来是 en，我建议 zh；如果你想完全不变就改回 en
DEFAULT_LANG = "zh"

THEME = "themes_dl/pelican-hyde"

PROFILE_IMAGE = "avatar.jpg"

STATIC_PATHS = ["images"]

# Google Analytics（你原来的 UA）
GOOGLE_ANALYTICS = "UA-79917414-1"

# RSS
FEED_ALL_RSS = "feeds/all.rss.xml"
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ("Pelican", "https://getpelican.com/"),
    ("Python.org", "https://www.python.org/"),
    ("Jinja2", "https://palletsprojects.com/p/jinja/"),
    ("You can modify those links in your config file", "#"),
)

# Social widget
SOCIAL = (
    ("twitter", "https://twitter.com/hillerliao"),
    ("github", "https://github.com/hillerliao"),
)

DEFAULT_PAGINATION = False

# 自定义页面
TEMPLATE_PAGES = {"talk.html": "talk/index.html"}
