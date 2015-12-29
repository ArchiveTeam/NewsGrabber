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
if not os.path.isdir('./services'):
	os.makedirs('./services')
if not os.path.isfile('./services/__init__.py'):
	open('./services/__init__.py', 'w').close()
import services

reload(sys)
sys.setdefaultencoding("utf-8")

requests.packages.urllib3.disable_warnings()

version = 20151229.01
refresh_wait = [5, 30, 60, 300, 1800, 3600, 7200, 21600, 43200, 86400, 172800]
refresh = [[], [], [], [], [], [], [], [], [], [], []]
immediate_grab = []
service_urls = {}
service_count = 0
grablistnormal = []
grablistvideos = []
grablistdone = {}
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
irc.send("USER " + irc_nick + " " + irc_nick + " " + irc_nick + " :This is the bot for " + irc_channel_main + ". https://github.com/ArchiveTeam/NewsGrabber.\n")
irc.send("NICK " + irc_nick + "\n")
irc.send("JOIN " + irc_channel_main + "\n")
irc.send("JOIN " + irc_channel_bot + "\n")

def irc_bot():
	global new_grabs
	global service_urls
	while True:
		irc_message = irc.recv(2048)
		with open('irclog', 'a') as file:
			file.write(irc_message)
		if 'PING :' in irc_message:
			irc.send('PONG :\n')
		elif re.search(r'^:[^:]+:.*newsbud(?:dy)?', irc_message) and re.search(r'^:[^:]+:.*[hH](?:ello|ey|i)', irc_message):
			if re.search(r'^:([^!]+)!', irc_message):
				if not re.search(r'^:([^!]+)!', irc_message).group(1) == 'newsbuddy':
					user = re.search(r'^:([^!]+)!', irc_message).group(1)
					irc_print(irc_channel_bot, 'Hello ' + user + '!')
					messages = ['What a beautiful day!', 'I\'m having the time of my life! What about you?', 'News, news, news, news.... Don\'t you just love a busy day?', 'Still alive? The world went BOOM according to some articles...', 'I\'m having a bad day. Don\'t disturbe me!', 'Let\'s save all the news!', 'Can you help me cover more newssites?', 'Together we can save the world on a harddrive!', 'Help me! I need more....', 'I\'m busy grabbing articles.', 'I truly love myself, don\'t you?']
					irc_print(irc_channel_bot, messages[random.randint(0,9)])
		elif re.search(r'^:[^:]+:!help', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_print(user, 'Hello! My options are:')
			irc_print(user, '\'!EMERGENCY_STOP\': Stop the grab immediatly.')
			irc_print(user, '\'!stop\': Write lists of URLs, finish current running grabs and not start new grabs.')
			irc_print(user, '\'!writefiles\': Write lists of URLs.')
			irc_print(user, '\'!imgrab\', \'!immediate-grab\' or \'!immediate_grab\': Make sure URLs are grabbed immediatly after they\'re found. Add \'remove\', \'rem\' or \'r\' to stop URLs from being grabbed immediatly after they\'re found.')
			irc_print(user, '\'!info\' or \'!information\': Request information about a service.')
			irc_print(user, '\'!move\': Move the WARC files.')
			irc_print(user, '\'!upload\': Upload the WARC files.')
		elif re.search(r'^:[^:]+:!stop', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			writefiles()
			new_grabs = False
			irc_print(irc_channel_bot, user + ': No new grabs will be started.')
		elif re.search(r'^:[^:]+:!version', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_print(irc_channel_bot, user + ': I\'m version ' + str(version) + '.')
		elif re.search(r'^:[^:]+:!writefiles', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			writefiles()
		elif re.search(r'^:[^:]+:!move', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			threading.Thread(target = movefiles).start()
			irc_print(irc_channel_bot, user + ': WARC files moving.')
		elif re.search(r'^:[^:]+:!upload', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			threading.Thread(target = uploader).start()
			irc_print(irc_channel_bot, user + ': WARC files uploading.')
		elif re.search(r'^:[^:]+:!info(?:formation)?', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			if not re.search(r'^:[^:]+:!info(?:formation)? web__[a-zA-Z0-9_]*', irc_message):
				irc_print(irc_channel_bot, user + ': What service do you want to have information about?')
			else:
				infoservice = re.search(r'^:[^:]+:!i(?:nfo(?:formation)?)? (web__[a-zA-Z0-9_]*)', irc_message).group(1)
				try:
					irc_print(irc_channel_bot, user + ': Service: ' + infoservice + '. Refreshtime: ' + str(refresh_wait[int(eval("services." + infoservice + ".refresh"))-1]) + ' seconds. URLs: ' + str(eval("services." + infoservice + ".urls")) + '. Regex: ' + str(eval("services." + infoservice + ".regex")) + '. Videoregex: ' + str(eval("services." + infoservice + ".videoregex")) + '. Liveregex: ' + str(eval("services." + infoservice + ".videoregex")) + '.')
					irc_print(irc_channel_bot, user + ': The script of this service is located here: https://github.com/ArchiveTeam/NewsGrabber/blob/master/services/' + infoservice + '.py')
					try:
						irc_print(irc_channel_bot, user + ': ' + service_urls[infoservice] + ' URLs have been added since the script was started.')
					except:
						irc_print(irc_channel_bot, user + ': 0 URLs have been added since the script was started.')
				except:
					irc_print(irc_channel_bot, user + ': Service ' + infoservice + ' doesn\'t exist.')
		elif re.search(r'^:[^:]+:!EMERGENCY_STOP', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			irc_print(irc_channel_bot, user + ': Bot emergency stopped.')
			raise Exception('Bot emergency stopped.')
		elif re.search(r'^:[^:]+:!im(?:mediate[-_])?grab', irc_message):
			user = re.search(r'^:([^!]+)!', irc_message).group(1)
			if not re.search(r'^:[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?web__[a-zA-Z0-9_]*', irc_message):
				irc_print(irc_channel_bot, user + ': What service do you want to have grabbed immediatly?')
			else:
				imservice = re.search(r'^:[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?(web__[a-zA-Z0-9_]*)', irc_message).group(1)
				try:
					if ' r' in irc_message:
						immediate_grab.remove(imservice)
						irc_print(irc_channel_bot, user + ': New URLs from service ' + imservice + ' will not be grabbed immediatly.')
					elif not imservice in immediate_grab:
						immediate_grab.append(imservice)
						irc_print(irc_channel_bot, user + ': New URLs from service ' + imservice + ' will be grabbed immediatly.')
				except:
					irc_print(irc_channel_bot, user + ': Service ' + infoservice + ' doesn\'t exist.')
def irc_bot_count():
	global total_count
	sleep_time = 900
	while True:
		irc_print(irc_channel_bot, str(total_count) + ' URLs added in the last ' + str(int(sleep_time/60)) + ' minutes.')
		total_count = 0
		time.sleep(sleep_time)

def irc_print(channel, message):
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

def upload(name, date1):
	date = re.sub('-', '', date1)
	filesize = os.path.getsize('./ready/' + name)
	itemdate = date
	itemnum = 0
	itemsize = 0
	if os.path.isfile('last_upload'):
		with open('last_upload', 'r') as uploadfile:
			itemsize, itemnum, itemdate = uploadfile.read().split(',', 2)
	if itemdate != date:
		itemdate = date
		itemsize = 0
		itemnum = 0
	if int(itemsize) > 10737418240:
		itemnum  = int(itemnum) + 1
		itemsize = 0
	itemname = 'archiveteam_newssites_' + str(itemdate) + '_' + '0'*(4-len(str(itemnum))) + str(itemnum)
	itemsize = int(itemsize) + filesize
	with open('last_upload', 'w') as uploadfile:
		uploadfile.write(str(itemsize) + ',' + str(itemnum) + ',' + str(itemdate))
	os.system('ia upload {0} ./ready/{1} --metadata="title:{0}" --metadata="mediatype:web" --metadata="collection:opensource" --metadata="date:{2}" --checksum --size-hint=21474836480 --delete'.format(itemname, name, date1))
	os.remove("./ready/" + name + ".upload")
	if os.path.isfile('./ready/' + name):
		irc_print(irc_channel_bot, name + ' uploaded unsuccessful.')

def check(files, num):
	for file in files:
		if file.endswith("0000" + num + ".warc.gz"):
			return True
	return False

def warcnum(folder):
	count = 0
	for root, dirs, files in os.walk("./" + folder):
		for file in files:
			#print(file)
			if file.endswith(".warc.gz"):
				count += 1
		return count

def movefiles():
	list = []
	done = True
	for folder in next(os.walk('.'))[1]:
		if not (folder == 'services' or folder == 'temp' or folder == 'donefiles'):
			for root, dirs, files in os.walk("./" + folder):
				if (check(files, "0") == False or check(files, "1") == True) and not folder == "ready":
					startnum = "0"
					firstnum = None
					moved = False
					while True:
						if not os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
							if firstnum > 0:
								break
						if os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
							#print 'hi'
							if firstnum == None:
								firstnum = int(startnum)
							if not startnum == "0" and not firstnum == int(startnum):
								print(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"))
								moved = True
								os.rename(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"), "./ready/" + folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz")
						startnum = str(int(startnum) + 1)
						if warcnum(folder) <= 1:
							break
						if warcnum(folder) == 2 and os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz"):
							break
			if os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz") and not folder == "ready":
				for root, dirs, files in os.walk("./" + folder):
					for file in files:
						if file.endswith(".warc.gz"):
							list.append("./ready/" + file)
							os.rename(os.path.join(root, file), "./ready/" + file)
					for file in files:
						if file.endswith(".warc.gz") and not os.path.isfile("./ready/" + file):
							#print("./ready/" + file)
							done = False
					if done == True:
						shutil.rmtree("./" + folder)
	for root, dirs, files in os.walk("./ready"):
		for file in files:
			os.rename(os.path.join(root, file), os.path.join(root, re.sub(".*-list(?:-videos)?(?:-immediate)?(?:_temp)?(?:[01]\.[0-9]+)?", "news", file)))
	print("All finished WARCs have been moved.")

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
				if not url in grablistnormal:
					grablistnormal.append(url)
	if os.path.isfile('list-videos'):
		with codecs.open('list-videos', 'r', 'utf-8') as listfile:
			for url in listfile.read().splitlines():
				url = url.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
				if not url in grablistvideos:
					grablistvideos.append(url)
	irc_print(irc_channel_bot, 'All files loaded.')
	

def writefiles():
	global grablistdone
	global grablistnormal
	global grablistvideos
	global writing
	writing = True
	time.sleep(10)
	irc_print(irc_channel_bot, 'Writing service URL files.')
	if not os.path.isdir('./temp/donefiles'):
		os.makedirs('./temp/donefiles')
	for service, urls in grablistdone.iteritems():
		with codecs.open('./temp/donefiles/' + service, 'a', 'utf-8') as doneurls:
			for url in urls:
				try:
					doneurls.write(url + '\n')
				except:
					irc_print(irc_channel_bot, 'Failed printing URL ' + url)
	if os.path.isdir('./donefiles'):
		shutil.rmtree('./donefiles')
	shutil.copytree('./temp/donefiles', './donefiles')
	irc_print(irc_channel_bot, 'Writing new URLs file.')
	with codecs.open('./temp/list', 'a', 'utf-8') as listfile:
		listfile.write('\n'.join(grablistnormal))
	with codecs.open('./temp/list-videos', 'a', 'utf-8') as listfile:
		listfile.write('\n'.join(grablistvideos))
	if os.path.isfile('list'):
		os.remove('list')
	if os.path.isfile('./temp/list'):
		shutil.move('./temp/list', './list')
	if os.path.isfile('list-videos'):
		os.remove('list-videos')
	if os.path.isfile('./temp/list-videos'):
		shutil.move('./temp/list-videos', './list-videos')
	shutil.rmtree('./temp')
	writing = False
	irc_print(irc_channel_bot, 'All files written.')
			

def checkrefresh():
	global refresh
	global service_count
	while True:
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
		time.sleep(300)

def checkurl(service, urlnum, url, regexes, videoregexes, liveregexes):
	global total_count
	global grablistdone
	global grablistnormal
	global grablistvideos
	global service_urls
	imgrabfiles = []
	tries = 0
	while tries < 5:
		try:
			response = requests.get(url)
			response.encoding = 'utf-8'
		except Exception as exception:
			tries += 1
			with open('exceptions', 'a') as exceptions:
				if tries == 5:
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
				if extractedurl.startswith('//'):
					oldextractedurls.append("http:" + extractedurl)
				elif extractedurl.startswith('/'):
					oldextractedurls.append(re.search(r'^(https?:\/\/[^\/]+)', url).group(1) + extractedurl)
				elif extractedurl.startswith('https://') or extractedurl.startswith('http://'):
					oldextractedurls.append(extractedurl)
				elif extractedurl.startswith('?'):
					oldextractedurls.append(re.search(r'^(https?:\/\/[^\?]+)', url).group(1) + extractedurl)
				elif extractedurl.startswith('./'):
					if re.search(r'^https?:\/\/.+\/', url):
						oldextractedurls.append(re.search(r'^(https?:\/\/.+)\/', url).group(1) + '/' + re.search(r'^\.\/(.+)', extractedurl).group(1))
					else:
						oldextractedurls.append(re.search(r'^(https?:\/\/.+)', url).group(1) + '/' + re.search(r'^\.\/(.+)', extractedurl).group(1))
				elif extractedurl.startswith('../'):
					tempurl = url
					tempextractedurl = extractedurl
					while tempextractedurl.startswith('../'):
						if not re.search(r'^https?://[^\/]+\/$', tempurl):
							tempurl = re.search(r'^(.+\/)[^\/]*\/', tempurl).group(1)
						tempextractedurl = re.search(r'^\.\.\/(.*)', tempextractedurl).group(1)
					oldextractedurls.append(tempurl + tempextractedurl)
				elif extractedstart == 'href':
					if re.search(r'^https?:\/\/.+\/', url):
						oldextractedurls.append(re.search(r'^(https?:\/\/.+)\/', url).group(1) + '/' + extractedurl)
					else:
						oldextractedurls.append(re.search(r'^(https?:\/\/.+)', url).group(1) + '/' + extractedurl)
			for extractedurl in re.findall(r'>[^<a-zA-Z0-9]*(https?://[^<]+)<', response.text):
				extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
				oldextractedurls.append(extractedurl)
			for extractedurl in oldextractedurls:
				if '?' in extractedurl:
					oldextractedurls.append(extractedurl.split('?')[0])
        		for extractedurl in oldextractedurls:
				extractedurl = extractedurl.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
				try:
					extractedurlpercent = re.search(r'^(https?://[^/]+).*$', extractedurl).group(1) + urllib.quote(re.search(r'^https?://[^/]+(.*)$', extractedurl).group(1).encode('utf8'), "!#$&'()*+,/:;=?@[]-._~")
				except:
					pass #bad url
				for regex in regexes:
					if re.search(regex, extractedurl) and not extractedurlpercent in extractedurls:
						extractedurls.append(extractedurlpercent)
						break
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
#			with codecs.open('./donefiles/' + service, 'r', 'utf-8') as donefile:
#				with codecs.open('./donefiles/' + service + '-temp', 'a', 'utf-8') as doneurls:
#					with codecs.open('./donefiles/' + service + '_webpage', 'r', 'utf-8') as pagefile:
#						page = pagefile.read()
#						print(page)
#						for doneurl in donefile:
#							if doneurl in response.text:
#								doneurls.write(doneurl + '\n')
#							if re.match(r'^https?://[^/]+(/.*)', doneurl):
#								if re.match(r'^https?://[^/]+(/.*)', doneurl).group(1) in page:
#									print("yessssssssssssss")
#									doneurls.write(doneurl)
#							elif re.match(r'^https?(://.*)', doneurl):
#								if re.match(r'^https?(://.*)', doneurl).group(1) in page:
#									doneurls.write(doneurl)
#							#print(re.match(r'^https?://[^/]+(/.*)', doneurl).group(1))
#							
#			os.remove('./donefiles/' + service)
#			os.rename('./donefiles/' + service + '-temp', './donefiles/' + service)
			if os.path.isfile('list-videos-immediate' + imgrabfiles[0]):
				listname = 'list-videos-immediate' + imgrabfiles[0]
				irc_print(irc_channel_bot, 'Started immediate videos grab for service ' + service + '.')
				threading.Thread(target = grablist, args = (listname,)).start()
			elif os.path.isfile('list-immediate' + imgrabfiles[1]):
				listname = 'list-immediate' + imgrabfiles[1]
				irc_print(irc_channel_bot, 'Started immediate normal grab for service ' + service + '.')
				threading.Thread(target = grablist, args = (listname,)).start()
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
		except:
			irc_print(irc_channel_bot, 'Failed running refreshgrab for refresh ' + str(i) + '.')
			pass #for now
		time.sleep(refresh_wait[i])

def dashboard():
	os.system('~/.local/bin/gs-server')

def processfiles():
	while True:
		try:
			threading.Thread(target = movefiles).start()
			time.sleep(30)
			threading.Thread(target = uploader).start()
		except:
			pass #for now
		time.sleep(270)

def grab():
	while new_grabs:
		time.sleep(20)
		if os.path.isfile('list_temp'):
			os.remove('list_temp')
		if os.path.isfile('list-videos_temp'):
			os.remove('list-videos_temp')
		grablistvideostemp = grablistvideos
		with codecs.open('list-videos_temp', 'a', 'utf-8') as listfile:
			listfile.write('\n'.join(grablistvideostemp))
		print(len(grablistvideos))
		for url in grablistvideostemp:
			grablistvideos.remove(url)
		print(len(grablistvideos))
		if os.path.isfile('list-videos_temp'):
			threading.Thread(target=grablist, args=('list-videos_temp',)).start()
			irc_print(irc_channel_bot, "Started videos grab.")
		grablistnormaltemp = grablistnormal
		with codecs.open('list_temp', 'a', 'utf-8') as listfile:
			listfile.write('\n'.join(grablistnormaltemp))
		print(len(grablistnormal))
		for url in grablistnormaltemp:
			grablistnormal.remove(url)
		print(len(grablistnormal))
		if os.path.isfile('list_temp'):
			threading.Thread(target=grablist, args=('list_temp',)).start()
			irc_print(irc_channel_bot, "Started normal grab.")
		time.sleep(3230)

def grablist(listname):
	videostring = ''
	if '-videos' in listname:
		videostring = '--youtube-dl '
	os.system('~/.local/bin/grab-site --input-file ' + listname + ' --level=0 --no-sitemaps --concurrency=5 --1 --warc-max-size=524288000 --wpull-args="' + videostring + '--no-check-certificate --timeout=300" > /dev/null 2>&1')
	if '-immediate' in listname:
		os.remove(listname)

def main():
	loadfiles()
	pause_length = 10
	threading.Thread(target = irc_bot).start()
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
	threading.Thread(target = checkrefresh).start()
	time.sleep(pause_length)
	threading.Thread(target = dashboard).start()
	threading.Thread(target = processfiles).start()
	for i in range(len(refresh)):
		threading.Thread(target = refresh_grab, args = (i,)).start()
	threading.Thread(target = grab).start()

if __name__ == '__main__':
	main()