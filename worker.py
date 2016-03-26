import requests
import os
import time

def main():
	while True:
		new_script = requests.get('https://raw.githubusercontent.com/ArchiveTeam/NewsGrabber/master/worker_script.py')
		if new_script.status_code == 200:
			with open('worker_script.py', 'w') as file:
				file.write(new_script.text)
			returned = os.system('python worker_script.py')
			if returned != 0:
				print('Something went wrong running this script.')
		else:
			print('Something went wrong. How is your internet connection?')
		time.sleep(3)

if __name__ == '__main__':
	main()
	