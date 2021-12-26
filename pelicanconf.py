AUTHOR = 'hillerliao'
SITENAME = '廖智海'
SITESUBTITLE = '互联网产品折腾师'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'en'

THEME = "pelican-hyde"

PROFILE_IMAGE = 'avatar.jpg'

STATIC_PATHS = ['images']

GOOGLE_ANALYTICS = '297740936'

# Feed generation is usually not desired when developing
# FEED_ALL_ATOM = None
FEED_ALL_RSS = 'feeds/all.rss.xml'
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None



# Blogroll
LINKS = (('Pelican', 'https://getpelican.com/'),
         ('Python.org', 'https://www.python.org/'),
         ('Jinja2', 'https://palletsprojects.com/p/jinja/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('twitter', 'https://twitter.com/hillerliao'),
          ('github', 'https://github.com/hillerliao'),)

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True