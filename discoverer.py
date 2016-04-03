import requests
import os
import time
import shutil
import threading
import re
import urllib
import codecs
import random
import string
if os.path.isdir('./services'):
	shutil.rmtree('./services')
if not os.path.isdir('./services'):
	os.makedirs('./services')
if not os.path.isfile('./services/__init__.py'):
	open('./services/__init__.py', 'w').close()
import services

version = 20160402.01
assigned_services = []
refresh = [[], [], [], [], [], [], [], [], [], [], []]
writing = False
refresh_wait = [5, 30, 60, 300, 1800, 3600, 7200, 21600, 43200, 86400, 172800]
standard_video_regex = [r'^https?:\/\/[^\/]+\/.*vid(?:eo)?', r'^https?:\/\/[^\/]+\/.*[tT][vV]', r'^https?:\/\/[^\/]+\/.*movie']
standard_live_regex = [r'^https?:\/\/[^\/]+\/.*live']
immediate_grab = []
grablistnormal = []
grablistvideos = []
grablistdone = {}
total_count = 0

def refresh_assigned_services():
	global assigned_services
	while True:
		newlists = os.listdir('./assigned_services')
		if len(newlists) != 0:
			assigned_services_ = []
			for newlist in [newlist for newlist in newlists if not (newlist.startswith('.') or newlist.endswith('~'))]:
				checkrefresh()
				with open('./assigned_services/' + newlist, 'r') as file:
					for line in file:
						line = line.replace('\n', '').replace('\r', '')
						if line != '':
							assigned_services_.append(line)
			assigned_services = list(assigned_services_)
			print(assigned_services)
			os.remove('./assigned_services/' + newlist)
		time.sleep(300)

def checkrefresh():
	global refresh
	refresh = [[], [], [], [], [], [], [], [], [], [], []]
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
					print('Found service ' + service[:-3] + '.')

def checkurl(service, urlnum, url, regexes, videoregexes, liveregexes):
	global total_count
	global grablistdone
	global grablistnormal
	global grablistvideos
	global standard_video_regex
	global standard_live_regex
	imgrabfiles = []
	tries = 0
	while tries < 10:
		try:
			response = requests.get(url, headers={'User-Agent': 'ArchiveTeam; Googlebot/2.1'})
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
			tries = 10
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
					liveurl = False
					for regex in liveregexes:
						if re.search(regex, extractedurl):
							liveurl = True
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
							if liveurl == False:
								grablistvideos.append(service + ', ' + extractedurl)
							if liveurl == True:
								grablistvideos.append(extractedurl)
					else:
						if not extractedurl in grablistnormal:
							if liveurl == False:
								grablistnormal.append(service + ', ' + extractedurl)
							if liveurl == True:
								grablistnormal.append(extractedurl)
					count += 1
					if count == 1:
						if not url in grablistnormal:
							grablistnormal.append(url)
			#if os.path.isfile('list-videos-immediate' + imgrabfiles[0]):
			#	with open('rsync_targets', 'r') as file:
			#		rsync_targets = [target for target in file.read().splitlines() if target != '']
			#		listname = 'list-videos-immediate' + imgrabfiles[0]
			#		irc_print(irc_channel_bot, 'Started immediate videos grab for service ' + service + '.')
			#		os.system("rsync -avz --no-o --no-g --progress --remove-source-files " + listname + " " + rsync_targets[0])
			#elif os.path.isfile('list-immediate' + imgrabfiles[1]):
			#	with open('rsync_targets', 'r') as file:
			#		rsync_targets = [target for target in file.read().splitlines() if target != '']
			#		listname = 'list-immediate' + imgrabfiles[1]
			#		irc_print(irc_channel_bot, 'Started immediate normal grab for service ' + service + '.')
			#		os.system("rsync -avz --no-o --no-g --progress --remove-source-files " + listname + " " + rsync_targets[0])
			print('Extracted ' + str(count) + ' URLs from service ' + service + ' for URL ' + url + '.')
			total_count += count

def send_urls():
	global writing
	while True:
		writing = True
		with open('rsync_target_discovery', 'r') as file:
			rsync_target = file.read()
		randomstring = ''.join(random.choice(string.ascii_lowercase) for num in range(10))
		grablistvideostemp = list(grablistvideos)
		with open('grablistvideos' + randomstring, 'w') as file:
			file.write('\n'.join(grablistvideostemp) + '\n')
		for url in grablistvideostemp:
			grablistvideos.remove(url)
		rsync_exit_code = os.system("rsync -avz --no-o --no-g --progress --remove-source-files grablistvideos" + randomstring + " " + rsync_target)
		if rsync_exit_code == 0:
			print('File synced successfully to the storage server.')
		else:
			print('Your received exit code ' + str(rsync_exit_code) + ' while syncing file to storage server.')
		grablistnormaltemp = list(grablistnormal)
		with open('grablistnormal' + randomstring, 'w') as file:
			file.write('\n'.join(grablistnormaltemp) + '\n')
		for url in grablistnormaltemp:
			grablistnormal.remove(url)
		rsync_exit_code = os.system("rsync -avz --no-o --no-g --progress --remove-source-files grablistnormal" + randomstring + " " + rsync_target)
		if rsync_exit_code == 0:
			print('Discovery file synced successfully to the storage server.')
		else:
			print('Your received exit code ' + str(rsync_exit_code) + ' while syncing discovery file to storage server.')
		writing = False
		time.sleep(60)

def refresh_grab(i):
	global writing
	while True:
		writingpauses = 0
		try:
			for service in refresh[i]:
				if service in assigned_services:
					urlnum = 0
					for url in eval("services." + service + ".urls"):
						while writing:
							writingpauses += 1
							time.sleep(1)
						threading.Thread(target = checkurl, args = (service, str(urlnum), url, eval("services." + service + ".regex"), eval("services." + service + ".videoregex"), eval("services." + service + ".liveregex"))).start()
						urlnum += 1
		except Exception as exception:
			with open('exceptions', 'a') as exceptions:
				exceptions.write(str(version) + '\n' + str(exception) + '\n\n')
		time.sleep(refresh_wait[i]-writingpauses)

def main():
	if not os.path.isdir('./assigned_services'):
		os.makedirs('./assigned_services')
	if not os.path.isfile('rsync_target_discovery'):
		raise Exception('Please add a rsync target for the discovered URL lists to file \'rsync_target_discovery\'')
	checkrefresh()
	threading.Thread(target = refresh_assigned_services).start()
	time.sleep(60)
	for i in range(len(refresh)):
		threading.Thread(target = refresh_grab, args = (i,)).start()
	time.sleep(60)
	threading.Thread(target = send_urls).start()

if __name__ == '__main__':
	main()
	