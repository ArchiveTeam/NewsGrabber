refresh = 4
version = 20160315.01

urls = ['http://feeds.bbci.co.uk/news/video_and_audio/news_front_page/rss.xml?edition=uk',
        'http://feeds.bbci.co.uk/news/video_and_audio/world/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/uk/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/business/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/politics/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/health/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/science_and_environment/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/technology/rss.xml',
        'http://feeds.bbci.co.uk/news/video_and_audio/entertainment_and_arts/rss.xml']
regex = [r'^https?:\/\/[^\/]*bbc\.co\.uk\/',
	      r'^https?:\/\/[^\/]*bbc\.com\/']
videoregex = [r'^https?:\/\/[^\/]*bbc\.co\.uk\/',
	            r'^https?:\/\/[^\/]*bbc\.com\/']
liveregex = ["/live/"]
