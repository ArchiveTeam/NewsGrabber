# NewsGrabber

THIS IS STILL IN BETA

An Archive Team project to save every news article from every newswebsite. The dashboard of this grab can be viewed here: http://newsgrabber.harrycross.me:29000.

How does this work?
-------------------
In `/services/` is a list of Python files. Each of these files are for individual newswebsites. The files contain the seed URLs from which new URLs are discovered and matched with the regexes in those same files. New URLs are added to a list of URLs to be grabbed and saved into WARC files. The WARC files are uploaded to the Internet Archive and browsable in the Wayback Machine.

A website is rechecked for new URLs every few seconds. All new URLs are downloaded every 1 hour.

Add a new website
------------------
Every new website that is added requires a Python file in `/services/` in order to be grabbed. This Python file should contain:
### Filename
The name of the new Python file should start with `web__` and end with `.py`. The name should contain the name of the website or a description of what part of the websites it holds. The filename should only contain the following characters: `0123456789`, `abcdefghijklmnopqrstuvwxyz`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ` and `_`. For example: `web__skynews_com.py` or `web__rtlnieuws_nl_videos.py`.

### `refresh`
This is a number indicating how often the URLs in `urls` should be recrawled for new URLs. When `refresh = 4` the URLs in `urls` will be redownloaded and checked for new URLs every 300 seconds. For example:
```
refresh = 6
```
Refresh can be any number from 1 to 11 were:
```
1 = 5 seconds
2 = 30 seconds
3 = 60 seconds - 1 minute
4 = 300 seconds - 5 minutes
5 = 1800 seconds - 30 minutes
6 = 3600 seconds - 60 minutes - 1 hour
7 = 7200 seconds - 120 minutes - 2 hours
8 = 21600 seconds - 360 minutes - 6 hours
9 = 43200 seconds - 720 minutes - 12 hours
10 = 86400 seconds - 1,440 minutes - 24 hours
11 = 172800 seconds - 2,880 minutes - 48 hours - 2 days
```
### `version`
This is the version number of the Python script. This should be the date and the count of the updates from that one day, for example:
```
version = 20151215.01
```
### `urls`
This is a list of URLs that will be checked for new links. These urls should be pages with a list of the newest articles, like rss feeds, and/or frontpages which have links to the newest articles. As few links as possible should be added, but all new articles should be found. For example:
```
urls = ['http://www.theguardian.com/uk/rss']
```
### `regex`
This is a list of regex patterns which will be matched with the links found in the downloaded URLs from `urls`. Links that match with one or more of these regex patterns will be added to the list to be downloaded. Often the regexes will match the main site of the newsarticles. For example:
```
regex = [r'^https?:\/\/[^\/]*theguardian\.com']
```
### `videoregex`
This is a list of regex patterns which will be matched with the links found in the downloaded URLs from `urls` and that match with one or more regexes from `regex`. If the URLs match one or more of these regexes they will be downloaded with youtube-dl. For example:
```
videoregex = [r'\/video\/']
```
If the website contains no videos:
```
videoregex = []
```
### `liveregex`
This is a list of regex patterns which will be matched with the links found in the downloaded URLs from `urls` and that match with one or more regexes from `regex`. If the URLs match one or more of these regexes they will not be added to the list of downloaded URLs. This means these URLs will be downloaded over and over again every time they are found. Can be used for livepages. For example:
```
liveregex = [r'\/liveblog\/']
```
If the website contains no live pages:
```
liveregex = []
```
