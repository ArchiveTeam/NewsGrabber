refresh = 2
version = 20151213.01

urls = ['http://feeds.bbci.co.uk/news/rss.xml',
        'http://www.bbc.co.uk/news',
        'http://www.bbc.com/news']
regex = [r'^https?:\/\/[^\/]*bbc\.co\.uk\/',
	    r'^https?:\/\/[^\/]*bbc\.com\/']	
videoregex = []
liveregex = ["/live/"]

cookie = None
