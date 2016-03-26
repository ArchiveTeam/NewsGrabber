import time
import os
import shutil
import threading
import requests
import re
import codecs
import subprocess
import requests.packages.urllib3
import socket
import random
import sys
import urllib
import datetime
if os.path.isdir('./services'):
	shutil.rmtree('./services')
if not os.path.isdir('./services'):
	os.makedirs('./services')
if not os.path.isfile('./services/__init__.py'):
	open('./services/__init__.py', 'w').close()
import services
import json

reload(sys)
sys.setdefaultencoding("utf-8")

requests.packages.urllib3.disable_warnings()

version = 20160326.01
refresh_wait = [5, 30, 60, 300, 1800, 3600, 7200, 21600, 43200, 86400, 172800]
refresh_names = ['5 seconds', '30 seconds', '1 minute', '5 minutes', '30 minutes', '1 hour', '2 hours', '6 hours', '12 hours', '1 day', '2 days']
standard_video_regex = [r'^https?:\/\/[^\/]+\/.*vid(?:eo)?', r'^https?:\/\/[^\/]+\/.*[tT][vV]', r'^https?:\/\/[^\/]+\/.*movie']
standard_live_regex = [r'^https?:\/\/[^\/]+\/.*live']
refresh = [[], [], [], [], [], [], [], [], [], [], []]
immediate_grab = []
service_urls = {}
service_count = 0
concurrent_uploads = 0
max_concurrent_uploads = 16
grablistnormal = []
grablistvideos = []
grablistdone = {}
fileuploads = {}
last_uploads = {}
accesskey = sys.argv[1]
new_grabs = True
writing = False
total_count = 0
irc_server = 'irc.underworld.no'
irc_port = 6667
irc_channel_bot = '#newsgrabberbot'
irc_channel_main = '#newsgrabber'
irc_nick = 'newsbuddy'
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((irc_server, irc_port))

def new_socket():
	global irc
	irc.close()
	irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	irc.connect((irc_server, irc_port))
	irc_bot_start()
	threading.Thread(target = irc_bot).start()

def irc_bot_start():
	irc.send("USER " + irc_nick + " " + irc_nick + " " + irc_nick + " :This is the bot for " + irc_channel_main + ". https://github.com/ArchiveTeam/NewsGrabber.\n")
	irc.send("NICK " + irc_nick + "\n")
	irc.send("JOIN " + irc_channel_main + "\n")
	irc.send("JOIN " + irc_channel_bot + "\n")

def irc_bot():
	global new_grabs
	global service_urls
	global irc
	global max_concurrent_uploads
	while True:
		irc_message = irc.recv(2048)
		with open('irclog', 'a') as file:
			file.write(irc_message)
		if 'PING :' in irc_message:
			message = re.search(r'^[^:]+:(.*)$', irc_message).group(1)
			irc.send('PONG :' + message + '\n')
		elif re.search(r'^:.+PRIVMSG[^:]+:.*newsbud(?:dy)?', irc_message) and re.search(r'^:.+PRIVMSG[^:]+:.*[hH](?:ello|ey|i)', irc_message):
			if re.search(r'^:([^!]+)!', irc_message):
				if not re.search(r'^:([^!]+)!', irc_message).group(1) == 'newsbuddy':
					user = re.search(r'^:([^!]+)!', irc_message).group(1)
					irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
					irc_print(irc_channel, 'Hello ' + user + '!')
					messages = ['What a beautiful day!', 'I\'m having the time of my life! What about you?', 'News, news, news, news.... Don\'t you just love a busy day?', 'Still alive? The world went BOOM according to some articles...', 'I\'m having a bad day. Don\'t disturbe me!', 'Let\'s save all the news!', 'Can you help me cover more newssites?', 'Together we can save the world on a harddrive!', 'Help me! I need more....', 'I\'m busy grabbing articles.', 'I truly love myself, don\'t you?']
					irc_print(irc_channel, messages[random.randint(0,9)])
		elif re.search(r'^:.+PRIVMSG[^:]+:!help', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_print(user, 'Hello! My options are:')
			irc_print(user, '\'!EMERGENCY_STOP\': Stop the grab immediatly.')
			irc_print(user, '\'!stop\': Write lists of URLs, finish current running grabs and not start new grabs.')
			irc_print(user, '\'!writefiles\': Write lists of URLs.')
			irc_print(user, '\'!imgrab\', \'!immediate-grab\' or \'!immediate_grab\': Make sure URLs are grabbed immediatly after they\'re found. Add \'remove\', \'rem\' or \'r\' to stop URLs from being grabbed immediatly after they\'re found.')
			irc_print(user, '\'!info\' or \'!information\': Request information about a service.')
			irc_print(user, '\'!upload\': Upload the WARC files.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!stop', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			writefiles()
			new_grabs = False
			irc_print(irc_channel, user + ': No new grabs will be started.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!con(?:current)?-uploads', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			if not re.search(r'^:.+PRIVMSG[^:]+:!con(?:current)?-uploads [0-9]+', irc_message):
				irc_print(irc_channel, user + ': Please specify a number of concurrent uploads.')
			else:
				max_concurrent_uploads = int(re.search(r'^:.+PRIVMSG[^:]+:!con(?:current)?-uploads ([0-9]+)', irc_message).group(1))
				irc_print(irc_channel, user + ': Number of concurrent upload is set to ' + str(max_concurrent_uploads) + '.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!start', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			new_grabs = True
			irc_print(irc_channel, user + ': New grabs will be started.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!version', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			irc_print(irc_channel, user + ': I\'m version ' + str(version) + '.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!r(?:efresh-)?s(?:ervices)?', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			irc_print(irc_channel, user + ': Refreshing services...')
			checkrefresh()
		elif re.search(r'^:.+PRIVMSG[^:]+:!writefiles', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			writefiles()
		elif re.search(r'^:.+PRIVMSG[^:]+:!upload', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			threading.Thread(target = uploader).start()
			irc_print(irc_channel, user + ': WARC files uploading.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!info(?:formation)?', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			if not re.search(r'^:.+PRIVMSG[^:]+:!info(?:formation)? web__[a-zA-Z0-9_]*', irc_message):
				irc_print(irc_channel, user + ': What service do you want to have information about?')
			else:
				infoservice = re.search(r'^:.+PRIVMSG[^:]+:!i(?:nfo(?:formation)?)? (web__[a-zA-Z0-9_]*)', irc_message).group(1)
				try:
					irc_print(irc_channel, user + ': Service: ' + infoservice + '. Refreshtime: ' + str(refresh_wait[int(eval("services." + infoservice + ".refresh"))-1]) + ' seconds. URLs: ' + str(eval("services." + infoservice + ".urls")) + '. Regex: ' + str(eval("services." + infoservice + ".regex")) + '. Videoregex: ' + str(eval("services." + infoservice + ".videoregex")) + '. Liveregex: ' + str(eval("services." + infoservice + ".videoregex")) + '.')
					irc_print(irc_channel_bot, user + ': The script of this service is located here: https://github.com/ArchiveTeam/NewsGrabber/blob/master/services/' + infoservice + '.py')
					try:
						irc_print(irc_channel, user + ': ' + service_urls[infoservice] + ' URLs have been added since the script was started.')
					except:
						irc_print(irc_channel, user + ': 0 URLs have been added since the script was started.')
				except:
					irc_print(irc_channel, user + ': Service ' + infoservice + ' doesn\'t exist.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!EMERGENCY_STOP', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			irc_print(irc_channel, user + ': Bot emergency stopped.')
			raise Exception('Bot emergency stopped.')
		elif re.search(r'^:.+PRIVMSG[^:]+:!im(?:mediate[-_])?grab', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
			if not re.search(r'^:.+PRIVMSG[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?web__[a-zA-Z0-9_]*', irc_message):
				irc_print(irc_channel, user + ': What service do you want to have grabbed immediatly?')
			else:
				imservice = re.search(r'^:.+PRIVMSG[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?(web__[a-zA-Z0-9_]*)', irc_message).group(1)
				try:
					if ' r' in irc_message:
						immediate_grab.remove(imservice)
						irc_print(irc_channel, user + ': New URLs from service ' + imservice + ' will not be grabbed immediatly.')
					elif not imservice in immediate_grab:
						immediate_grab.append(imservice)
						irc_print(irc_channel, user + ': New URLs from service ' + imservice + ' will be grabbed immediatly.')
				except:
					irc_print(irc_channel, user + ': Service ' + infoservice + ' doesn\'t exist.')
def irc_bot_count():
	global total_count
	sleep_time = 900
	while True:
		irc_print(irc_channel_bot, str(total_count) + ' URLs added in the last ' + str(int(sleep_time/60)) + ' minutes.')
		total_count = 0
		time.sleep(sleep_time)

def irc_print(channel, message):
	try:
		irc.send("PRIVMSG " + channel + " :" + message + "\n")
	except Exception as exception:
		with open('exceptions', 'a') as exceptions:
			exceptions.write(str(version) + '\n' + str(exception) + '\n\n')
		new_socket()
		irc.send("PRIVMSG " + channel + " :" + message + "\n")
	print("IRC BOT: " + message)

def uploader():
	for root, dirs, files in os.walk("./ready"):
		for file in files:
			date = re.search(r'([0-9][0-9][0-9][0-9]\-[0-9][0-9]\-[0-9][0-9])', file).group(1)
			date2 = re.sub('-', '', date)
			if re.match(r'news', file) and file.endswith(".warc.gz"):
				if not os.path.isfile(os.path.join(root, file) + ".upload"):
					open(os.path.join(root, file) + ".upload", 'a').close()
					threading.Thread(target = upload, args = (file, date)).start()
					time.sleep(2)

def ia_upload_allowed():
	global accesskey
	resp = requests.get('https://s3.us.archive.org/?check_limit=1&accesskey=' + accesskey)
	if resp.status_code == 200:
		try:
			data = json.loads(resp.text)
			if 'over_limit' in data and data['over_limit'] is not 0:
				return False

			if 'detail' in data and 'rationing_engaged' in data['detail'] and data['detail']['rationing_engaged'] is not 0:
				return False
		except:
			pass

		return True
	else:
		return False

def upload(name, date1):
	global fileuploads
	global concurrent_uploads
	global max_concurrent_uploads
	global last_uploads
	if os.path.isfile('./ready/' + name):
		date = re.sub('-', '', date1)
		filesize = os.path.getsize('./ready/' + name)
		itemdate = date
		itemnum = 0
		itemsize = 0
		if name in fileuploads:
			itemnum = fileuploads[name]
			itemname = str(itemdate) + '_' + '0'*(4-len(str(itemnum))) + str(itemnum)
		else:
			if itemdate in last_uploads:
				itemsize, itemnum = last_uploads[itemdate]
			elif os.path.isfile('./last_upload/last_upload_' + itemdate):
				with open('./last_upload/last_upload_' + itemdate, 'r') as uploadfile:
					itemvalues = uploadfile.read().split(',')
					if len(itemvalues) == 2:
						itemsize, itemnum = itemvalues
			if int(itemsize) > 10737418240:
				itemnum = int(itemnum) + 1
				itemsize = 0
			itemname = str(itemdate) + '_' + '0'*(4-len(str(itemnum))) + str(itemnum)
			itemsize = int(itemsize) + filesize
			fileuploads[name] = itemnum
			last_uploads[itemdate] = [itemsize, itemnum]
		if os.path.isfile('./ready/' + name):
			while ia_upload_allowed() == False:
				time.sleep(20)
			while concurrent_uploads > max_concurrent_uploads:
				time.sleep(20)
			concurrent_uploads += 1
			os.system('ia upload archiveteam_newssites_{0} ./ready/{1} --metadata="title:Archive Team Newsgrab: {0}" --metadata="description:A collection of news articles grabbed from a wide variety of sources around the world automatically by Archive Team scripts." --metadata="mediatype:web" --metadata="collection:archiveteam_newssites" --metadata="date:{2}" --checksum --size-hint=c --delete'.format(itemname, name, date1))
			concurrent_uploads -= 1
		if os.path.isfile("./ready/" + name + ".upload"):
			os.remove("./ready/" + name + ".upload")
		if os.path.isfile('./ready/' + name):
			irc_print(irc_channel_bot, name + ' uploaded unsuccessful.')

def loadfiles():
	global grablistdone
	global grablistnormal
	global grablistvideos
	irc_print(irc_channel_bot, 'Loading service URL files.')
	if os.path.isdir('./donefiles'):
		for root, dirs, files in os.walk('./donefiles'):
			for file in files:
				with codecs.open('./donefiles/' + file, 'r', 'utf-8') as servicefile:
					service = file
					print service
					for url in servicefile.read().splitlines():
						url = url.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
						url = re.search(r'^(https?:\/\/.*?) *$', url).group(1)
						try:
							grablistdone[service]
						except:
							grablistdone[service] = []
						if not url in grablistdone[service]:
							grablistdone[service].append(url)
	irc_print(irc_channel_bot, 'Loading new URLs file.')
	if os.path.isfile('list'):
		with codecs.open('list', 'r', 'utf-8') as listfile:
			for url in listfile.read().splitlines():
				url = url.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
				url = re.search(r'^(https?:\/\/.*?) *$', url).group(1)
				if not url in grablistnormal:
					grablistnormal.append(url)
	if os.path.isfile('list-videos'):
		with codecs.open('list-videos', 'r', 'utf-8') as listfile:
			for url in listfile.read().splitlines():
				url = url.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
				url = re.search(r'^(https?:\/\/.*?) *$', url).group(1)
				if not url in grablistvideos:
					grablistvideos.append(url)
	irc_print(irc_channel_bot, 'All files loaded.')


def writefiles():
	global grablistdone
	global grablistnormal
	global grablistvideos
	global writing
	global last_uploads
	writing = True
	time.sleep(10)
	irc_print(irc_channel_bot, 'Writing service URL files.')
	for service, urls in grablistdone.iteritems():
		with codecs.open('./donefiles/' + service, 'w', 'utf-8') as doneurls:
			try:
				doneurls.write('\n'.join(urls))
			except Exception as exception:
				with open('exceptions', 'a') as exceptions:
					exceptions.write(str(version) + ' ' + service + '\n' + str(exception) + '\n\n')
					irc_print(irc_channel_bot, 'Files from service ' + service + ' failed to write.')
	irc_print(irc_channel_bot, 'Writing item numbering files.')
	for itemdate, data in last_uploads.iteritems():
		itemsize, itemnum = data
		with codecs.open('./last_upload/last_upload_' + itemdate, 'w') as numfile:
			numfile.write(str(itemsize) + ',' + str(itemnum))
	irc_print(irc_channel_bot, 'Writing new URLs file.')
	with codecs.open('./list', 'a', 'utf-8') as listfile:
		listfile.write('\n'.join(grablistnormal))
	with codecs.open('./list-videos', 'a', 'utf-8') as listfile:
		listfile.write('\n'.join(grablistvideos))
	writing = False
	irc_print(irc_channel_bot, 'All files written.')


def checkrefresh():
	global refresh
	global service_count
	refresh = [[], [], [], [], [], [], [], [], [], [], []]
	new_services = 0
	if os.path.isdir('./services'):
		shutil.rmtree('./services')
	os.system('git clone https://github.com/ArchiveTeam/NewsGrabber.git')
	shutil.copytree('./NewsGrabber/services', './services')
	shutil.rmtree('./NewsGrabber')
	reload(services)
	for root, dirs, files in os.walk("./services"):
		for service in files:
			if service.startswith("web__") and service.endswith(".py"):
				if not service[:-3] in refresh[int(eval("services." + service[:-3] + ".refresh"))-1]:
					for refreshlist in refresh:
						while service[:-3] in refreshlist:
							refreshlist.remove(service[:-3])
					refresh[int(eval("services." + service[:-3] + ".refresh"))-1].append(service[:-3])
					new_services += 1
					print('Found service ' + service[:-3] + '.')
	new_count = new_services-service_count
	service_count = new_services
	if new_count == 1:
		irc_print(irc_channel_bot, 'Found and updated ' + str(new_count) + ' service.')
	elif new_count != 0:
		irc_print(irc_channel_bot, 'Found and updated ' + str(new_count) + ' services.')
	writehtmlserviceslist()

def checkurl(service, urlnum, url, regexes, videoregexes, liveregexes):
	global total_count
	global grablistdone
	global grablistnormal
	global grablistvideos
	global service_urls
	global standard_video_regex
	global standard_live_regex
	imgrabfiles = []
	tries = 0
	while tries < 10:
		try:
			response = requests.get(url)
			response.encoding = 'utf-8'
		except Exception as exception:
			tries += 1
			with open('exceptions', 'a') as exceptions:
				if tries == 10:
					exceptions.write(str(version) + ' ' + str(tries) + ' ' + url + '\n' + str(exception) + '\n\n')
				#	irc_print(irc_channel_bot, str(version) + ' ' + str(tries) + ' ' + url + ' EXCEPTION ' + str(exception))
		try:
			response
		except NameError:
			pass
		else:
			tries = 5
			oldextractedurls = []
			extractedurls = []
			extractedvideourls = []
			count = 0
			url = re.search(r'([^#]+)', url).group(1)
			for extractedurl in re.findall(r"'(index\.php[^']+)'", response.text):
				extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
				oldextractedurls.append(re.match(r'^(https?://.+/)', url).group(1) + extractedurl)
			for extractedurl in re.findall('(....=(?P<quote>[\'"]).*?(?P=quote))', response.text):
				extractedstart = re.search(r'^(....)', extractedurl[0]).group(1)
				extractedurl = re.search('^....=[\'"](.*?)[\'"]$', extractedurl[0]).group(1)
				extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
				extractedurl = extractedurl.replace('%3A', ':').replace('%2F', '/')
				if extractedurl.startswith('//'):
					oldextractedurls.append("http:" + extractedurl)
				elif extractedurl.startswith('/'):
					oldextractedurls.append(re.search(r'^(https?:\/\/[^\/]+)', url).group(1) + extractedurl)
				elif re.search(r'^https?:?\/\/?', extractedurl):
					oldextractedurls.append(extractedurl.replace(re.search(r'^(https?:?\/\/?)', extractedurl).group(1), re.search(r'^(https?)', extractedurl).group(1) + '://'))
				elif extractedurl.startswith('?'):
					oldextractedurls.append(re.search(r'^(https?:\/\/[^\?]+)', url).group(1) + extractedurl)
				elif extractedurl.startswith('./'):
					if re.search(r'^https?:\/\/.*\/', url):
						oldextractedurls.append(re.search(r'^(https?:\/\/.*)\/', url).group(1) + '/' + re.search(r'^\.\/(.*)', extractedurl).group(1))
					else:
						oldextractedurls.append(re.search(r'^(https?:\/\/.*)', url).group(1) + '/' + re.search(r'^\.\/(.*)', extractedurl).group(1))
				elif extractedurl.startswith('../'):
					tempurl = url
					tempextractedurl = extractedurl
					while tempextractedurl.startswith('../'):
						if not re.search(r'^https?://[^\/]+\/$', tempurl):
							tempurl = re.search(r'^(.*\/)[^\/]*\/', tempurl).group(1)
						tempextractedurl = re.search(r'^\.\.\/(.*)', tempextractedurl).group(1)
					oldextractedurls.append(tempurl + tempextractedurl)
				elif extractedstart == 'href':
					if re.search(r'^https?:\/\/.*\/', url):
						oldextractedurls.append(re.search(r'^(https?:\/\/.*)\/', url).group(1) + '/' + extractedurl)
					else:
						oldextractedurls.append(re.search(r'^(https?:\/\/.*)', url).group(1) + '/' + extractedurl)
			for extractedurl in re.findall(r'>[^<a-zA-Z0-9]*(https?:?//?[^<]+)<', response.text):
				extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
				oldextractedurls.append(extractedurl.replace(re.search(r'^(https?:?\/\/?)', extractedurl).group(1), re.search(r'^(https?)', extractedurl).group(1) + '://'))
			for extractedurl in oldextractedurls:
				if '?' in extractedurl:
					oldextractedurls.append(extractedurl.split('?')[0])
			for extractedurl in oldextractedurls:
				extractedurl = extractedurl.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
				extractedurl = re.search(r'^(https?:\/\/.*?) *$', extractedurl).group(1)
				extractedurl = urllib.unquote(extractedurl)
				try:
					extractedurlpercent = re.search(r'^(https?://[^/]+).*$', extractedurl).group(1) + urllib.quote(re.search(r'^https?://[^/]+(.*)$', extractedurl).group(1).encode('utf8'), "!#$&'()*+,/:;=?@[]-._~")
				except:
					pass #bad url
				for regex in regexes:
					if re.search(regex, extractedurl) and not extractedurlpercent in extractedurls:
						extractedurls.append(extractedurlpercent)
						break
			videoregexes += [regex for regex in standard_video_regex if not regex in videoregexes]
			liveregexes += [regex for regex in standard_live_regex if not regex in liveregexes]
			for extractedurl in extractedurls:
				for regex in videoregexes:
					if re.search(regex, extractedurl) and not extractedurl in extractedvideourls:
						extractedvideourls.append(extractedurl)
						break
			imgrabfiles.append(str(random.random()))
			imgrabfiles.append(str(random.random()))
			for extractedurl in extractedurls:
				while writing:
					time.sleep(1)
				try:
					grablistdone[service]
				except:
					grablistdone[service] = []
				if not extractedurl in grablistdone[service]:
					for regex in liveregexes:
						if re.search(regex, extractedurl):
							break
					else:
						grablistdone[service].append(extractedurl)
					if extractedurl in extractedvideourls and service in immediate_grab:
						filename = 'list-videos-immediate' + imgrabfiles[0]
						with codecs.open(filename, 'a', 'utf-8') as listurls:
							if not extractedurl in grablistvideos:
								listurls.write(extractedurl + '\n')
					elif service in immediate_grab:
						filename = 'list-immediate' + imgrabfiles[1]
						with codecs.open(filename, 'a', 'utf-8') as listurls:
							if not extractedurl in grablistnormal:
								listurls.write(extractedurl + '\n')
					if extractedurl in extractedvideourls:
						if not extractedurl in grablistvideos:
							grablistvideos.append(extractedurl)
					else:
						if not extractedurl in grablistnormal:
							grablistnormal.append(extractedurl)
					count += 1
					if count == 1:
						if not url in grablistnormal:
							grablistnormal.append(url)
			if os.path.isfile('list-videos-immediate' + imgrabfiles[0]):
				with open('rsync_targets', 'r') as file:
					rsync_targets = [target for target in file.read().splitlines() if target != '']
					listname = 'list-videos-immediate' + imgrabfiles[0]
					irc_print(irc_channel_bot, 'Started immediate videos grab for service ' + service + '.')
					os.system("rsync -avz --no-o --no-g --progress --remove-source-files " + listname + " " + rsync_targets[0])
			elif os.path.isfile('list-immediate' + imgrabfiles[1]):
				with open('rsync_targets', 'r') as file:
					rsync_targets = [target for target in file.read().splitlines() if target != '']
					listname = 'list-immediate' + imgrabfiles[1]
					irc_print(irc_channel_bot, 'Started immediate normal grab for service ' + service + '.')
					os.system("rsync -avz --no-o --no-g --progress --remove-source-files " + listname + " " + rsync_targets[0])
			print('Extracted ' + str(count) + ' URLs from service ' + service + ' for URL ' + url + '.')
			try:
				service_urls[service] += count
			except:
				service_urls[service] = count
			total_count += count

def refresh_grab(i):
	while True:
		try:
			for service in refresh[i]:
				urlnum = 0
				for url in eval("services." + service + ".urls"):
					threading.Thread(target = checkurl, args = (service, str(urlnum), url, eval("services." + service + ".regex"), eval("services." + service + ".videoregex"), eval("services." + service + ".liveregex"))).start()
					urlnum += 1
		except Exception as exception:
			with open('exceptions', 'a') as exceptions:
				exceptions.write(str(version) + '\n' + str(exception) + '\n\n')
			irc_print(irc_channel_bot, 'Failed running refreshgrab for refresh ' + str(i) + '.')
		time.sleep(refresh_wait[i])

def dashboard():
	os.system('~/.local/bin/gs-server')

def processfiles():
	while True:
		try:
			threading.Thread(target = uploader).start()
		except:
			pass #for now
		time.sleep(270)

def spliturllist(urllist, num):
	urllists = []
	lastnum = 0.
	while lastnum < len(urllist):
		newlist = urllist[int(lastnum):int(lastnum + (len(urllist)/float(num)))]
		urllists.append(newlist)
		lastnum += len(urllist)/float(num)
	return urllists

def grab():
	global grablistvideos
	global grablistnormal
	while True:
		with open('rsync_targets', 'r') as file:
			rsync_targets = [target for target in file.read().splitlines() if target != '']
			rsync_targets_num = len(rsync_targets)
			if new_grabs:
				time.sleep(20)
			grablistvideostemp = list(set(grablistvideos))
			videolists = spliturllist(grablistvideostemp, rsync_targets_num)
			for i in range(rsync_targets_num):
				with codecs.open('list-videos_temp' + str(i), 'a', 'utf-8') as listfile:
					listfile.write('\n'.join(videolists[i]))
			print(len(grablistvideos))
			for url in grablistvideostemp:
				grablistvideos.remove(url)
			print(len(grablistvideos))
			if new_grabs:
				for i in range(rsync_targets_num):
					if os.path.isfile('list-videos_temp' + str(i)):
						rsync_exit_code = os.system("rsync -avz --no-o --no-g --progress --remove-source-files list-videos_temp" + str(i) + " " + rsync_targets[i])
						if rsync_exit_code != 0:
							irc_print(irc_channel_bot, 'URLslist list-videos_temp' + str(i) + ' failed to sync.')
			grablistnormaltemp = list(set(grablistnormal))
			normallists = spliturllist(grablistnormaltemp, rsync_targets_num)
			for i in range(rsync_targets_num):
				with codecs.open('list_temp' + str(i), 'a', 'utf-8') as listfile:
					listfile.write('\n'.join(normallists[i]))
			print(len(grablistnormal))
			for url in grablistnormaltemp:
				grablistnormal.remove(url)
			print(len(grablistnormal))
			if new_grabs:
				for i in range(rsync_targets_num):
					if os.path.isfile('list_temp' + str(i)):
						rsync_exit_code = os.system("rsync -avz --no-o --no-g --progress --remove-source-files list_temp" + str(i) + " " + rsync_targets[i])
						if rsync_exit_code != 0:
							irc_print(irc_channel_bot, 'URLslist list_temp' + str(i) + ' failed to sync.')
		time.sleep(3580)

def writehtmlindex():
	if not os.path.isfile('index.html'):
		with open('index.html', 'w') as file:
			file.write('<!DOCTYPE html>\n<html>\n<head>\n<style>\ntable#lists {\n    width:60%;\n}\ntable#lists tr:nth-child(even) {\n    background-color: #eee;\n}\ntable#lists tr:nth-child(odd) {\n   background-color:#fff;\n}\ntable#lists th	{\n    background-color: black;\n    color: white;\n}\n</style>\n</head>\n<body>\n\n<div><a href="services.html">Services</a></div><table id="lists" align="center">\n  <tr>\n    <th>Date</th>\n    <th>URLs</th>\n    <th>ID</th>\n    <th>YouTube-DL</th>\n    <th>Immediate grab</th>\n  </tr>\n</table>\n\n</body>\n</html>\n')

def writehtmllist(folder):
	urlslist = []
	grabid = re.search(r'-([0-9a-z]{8})$', folder).group(1)
	youtubedl = 'no'
	imgrab = 'no'
	if '-videos' in folder:
		youtubedl = 'yes'
	if re.search(r'[0-9]\.[0-9]+', folder):
		imgrab = 'yes'
	if os.path.isfile('./'+ folder + '/input_file'):
		with open('./'+ folder + '/input_file', 'r') as file:
			urlslist = file.read().splitlines()
		if not os.path.isfile('index.html'):
			writehtmlindex()
		if not os.path.isdir('./urllists'):
			os.makedirs('./urllists')
		with open('index.html', 'r') as file:
			newhtml = file.read()
		if not grabid in newhtml:
			with open('index.html', 'w') as file:
				file.write(newhtml.replace('  <tr>\n    <th>Date</th>\n    <th>URLs</th>\n    <th>ID</th>\n    <th>YouTube-DL</th>\n    <th>Immediate grab</th>\n  </tr>\n', '  <tr>\n    <th>Date</th>\n    <th>URLs</th>\n    <th>ID</th>\n    <th>YouTube-DL</th>\n    <th>Immediate grab</th>\n  </tr>\n  <tr>\n    <td><a href="urllists/' + grabid + '.html">' + datetime.datetime.fromtimestamp(os.path.getctime('./' + folder + '/input_file')).strftime("%Y-%m-%d %H:%M") + '</a></td>\n    <td><a href="urllists/' + grabid + '.html">' + str(len(urlslist)) + '</a></td>\n    <td><a href="urllists/' + grabid + '.html">' + grabid + '</a></td>\n    <td><a href="urllists/' + grabid + '.html">' + youtubedl + '</a></td>\n    <td><a href="urllists/' + grabid + '.html">' + imgrab + '</a></td>\n  </tr>\n'))
			with open('./urllists/' + grabid + '.html', 'w') as file:
				file.write('<!DOCTYPE html>\n<html>\n<head>\n<style>\ntable#lists {\n    width:100%;\n}\ntable#list tr:nth-child(even) {\n    background-color: #eee;\n}\ntable#list tr:nth-child(odd) {\n   background-color:#fff;\n}\ntable#list th	{\n    background-color: black;\n    color: white;\n}\n</style>\n</head>\n<body>\n\n<table id="list" align="center">\n  <tr>\n    <th>URL</th>\n  </tr>\n  <tr>\n    <td>' + '</td>\n  </tr>\n  <tr>\n    <td>'.join(urlslist) + '</td>\n  </tr>\n</table>\n\n</body>\n</html>\n')

def serviceshtml():
	def make_name(name, m):
		display_name = name[5:-3].replace('_','.')
		wikidata = getattr(m, 'wikidata', None)
		if wikidata:
			return '<a href="https://www.wikidata.org/wiki/{}">{}</a>'.format(wikidata, display_name)
		return display_name
	make_multiline = lambda arr, func: '<br>'.join(map(func, arr))
	as_code = lambda s: '<code>{}</code>'.format(s)
	as_url = lambda s: '<a href="{}">{}</a>'.format(s, s.split('://',1)[1])
	servicemodules = sorted([(service, getattr(services, service[:-3])) for root, dirs, files in os.walk("./services")
		for service in files if service.startswith("web__") and service.endswith(".py")])
	return '\n'.join(['<tr>{}</tr>'.format(' '.join(['<td>{}</td>'.format(d) for d in [
		n,
		make_name(name, m),
		make_multiline(m.urls, as_url),
		refresh_names[m.refresh-1],
		make_multiline(m.regex, as_code),
		make_multiline(m.videoregex, as_code),
		make_multiline(m.liveregex, as_code),
		m.version,
		]])) for (n, (name, m)) in enumerate(servicemodules)])

def writehtmlserviceslist():
	with open('services.html', 'w') as file:
		file.write('<!DOCTYPE html>\n<html>\n<head>\n<style>\ntable#lists {\n    width:60%;\n}\ntable#lists tr:nth-child(even) {\n    background-color: #eee;\n}\ntable#lists tr:nth-child(odd) {\n   background-color:#fff;\n}\ntable#lists th	{\n    background-color: black;\n    color: white;\n}\n</style>\n</head>\n<body>\n\n<table id="lists" align="center">\n  <tr>\n    <th>#</th>\n    <th>Name</th>\n    <th>URLs</th>\n    <th>Refresh</th>\n    <th>Regex</th>\n    <th>Video Regex</th>\n    <th>Live Regex</th>\n    <th>Version</th>\n  </tr>\n' + serviceshtml() + '\n</table>\n\n</body>\n</html>\n')

def main():
	if not os.path.isfile('rsync_targets'):
		raise Exception('Please add a rsync target(s) to file \'rsync_targets\'')
	irc_bot_start()
	threading.Thread(target = irc_bot).start()
	loadfiles()
	writehtmlindex()
	pause_length = 10
	time.sleep(pause_length*2)
	irc_print(irc_channel_bot, 'Hello!')
	irc_print(irc_channel_bot, 'Version ' + str(version) + '.')
	irc_print(irc_channel_main, 'Hello! I\'ve just been (re)started. Follow my newsgrabs in ' + irc_channel_bot)
	irc_print(irc_channel_bot, 'Script started.')
	threading.Thread(target = irc_bot_count).start()
	if not os.path.isdir("./ready"):
		os.makedirs("./ready")
	for root, dirs, files in os.walk("./ready"):
		for file in files:
			if file.endswith(".upload"):
				os.remove(os.path.join(root, file))
	checkrefresh()
	time.sleep(pause_length)
	threading.Thread(target = dashboard).start()
	threading.Thread(target = processfiles).start()
	for i in range(len(refresh)):
		threading.Thread(target = refresh_grab, args = (i,)).start()
	threading.Thread(target = grab).start()

if __name__ == '__main__':
	main()
