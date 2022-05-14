#!/usr/bin/python3

import validators
import requests
import argparse
import threading
from urllib.parse import urlparse
from datetime import datetime

def banner(title=""):
    print("""

                  __   _   __    __          __                                
   ________  ___  / /__/ | / /___/ /__  _____/ /__________  __  __  ____  __  __
  / ___/ _ \/ _ \/ //_/  |/ / __  / _ \/ ___/ __/ ___/ __ \/ / / / / __ \/ / / /
 (__  )  __/  __/ ,< / /|  / /_/ /  __(__  ) /_/ /  / /_/ / /_/ / / /_/ / /_/ / 
/____/\___/\___/_/|_/_/ |_/\__,_/\___/____/\__/_/   \____/\__, (_) .___/\__, /  
                                                         /____/ /_/    /____/   
               				https://github.com/mind2hex/seekNdestroy.py
""")
    total_len = 80
    if title:
        padding = total_len - len(title) - 4
        print("== {} {}\n".format(title, "=" * padding))
    else:
        print("{}\n".format("=" * total_len))

def parse_arguments():
	parser = argparse.ArgumentParser(prog="seekNdestroy.py", description="enumerate content of a http web server")
	parser.add_argument("url", type=str, help="target url ")
	parser.add_argument('-w', "--wordlist", type=argparse.FileType('r', encoding='latin1'), required=True, help="wordlist to use")
	parser.add_argument('-t', "--threads",  type=int, choices=range(1,80), default=20, metavar="[1-80]", help="threads [default 20]")
	parser.add_argument("--timeout", type=int, default=10, metavar="<n>", help="timeout to wait for every request response [default 10] in seconds")
	parser.add_argument("--filter-sc", type=str, default="200,300", help="coma-separated status-code filter [default 200,300]")
	parser.add_argument("--filter-cl", type=int, default=-1, help="content-length filter")
	return parser.parse_args()

def ERROR(msg1, msg2):
	print("[X] ERROR =============================================")
	print("[X]   FROM: ", msg1)
	print("[X] REASON: ", msg2)
	print("[X] FINISHING PROGRAM...")
	print("[X] ===================================================")
	exit(-1)

def check_arguments(args):
	check_arguments_url(args.url)
	#check_arguments_wordlist(args.wordlist)
	#check_arguments_threads(args.threads)
	check_arguments_timeout(args.timeout)
	args.filter_sc = check_arguments_filter_sc(args.filter_sc)
	if args.filter_cl != -1:
		check_arguments_filter_cl(args.filter_cl)
	return args

def check_arguments_url(url):
	if not validators.url(url):
		ERROR("check_arguments_url::validators.url", f"invalid url {url}")

def check_arguments_timeout(timeout):
	if timeout < 0:
		ERROR("check_arguments_timeout", f"invalid timeout {timeout}")

def check_arguments_filter_sc(status_code):
	aux = status_code.split(',')

	if len(aux) == 0:
		ERROR("check_arguments_filter_sc::InvalidLength", f"Invalid status code specified {status_code}")

	for i in aux:
		if i.isdigit() == False:
			ERROR("check_arguments_filter_sc::i.isdigit()==False", f"Invalid status code specified {status_code}")
		elif (int(i) < 100) or (int(i) > 599):
			ERROR("check_arguments_filter_sc::i<100||i>599", f"Status code out of range --> {status_code}")
	else:
		return aux

def check_arguments_filter_cl(content_length):
	if content_length < 0:
		ERROR("check_arguments_filter_cl::content_length<0", f"content length can't be less than 0")

def wordlist_splitter(raw_wordlist, threads):
	wordlist = raw_wordlist.read().split('\n')
	words_per_thread = len(wordlist)//threads
	word_list = []
	while (len(wordlist) > 0):
		word_list.append(wordlist[:words_per_thread])
		wordlist = wordlist[words_per_thread+1:]

		if words_per_thread > len(wordlist):
			word_list.append(wordlist)
			break

	return word_list

def show_config(arguments):
	print("=====GENERAL OPTIONS=======================")
	print(f"[!] TARGET URL: {arguments.url}")
	print(f"[!]   WORDLIST: {arguments.wordlist_path}")
	print(f"[!]    THREADS: {arguments.threads}")
	print(f"[!]    TIMEOUT: {arguments.timeout}")
	print(f"[!]  FILTER_SC: {arguments.filter_sc}")
	if arguments.filter_cl != -1:
		print(f"[!]  FILTER_CL: {arguments.filter_cl}")
	print("\n\n")

def timestamp(msg):
	now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	print("===========================================")	
	if msg == "start":
		print(f"[!] Starting scan at {now}\n")
	else:
		print(f"[!] Finishing scan at {now}\n")


def header():
	print("%-40s\t%-10s\t%-10s\t%-10s"%("## URL ##", "STATUS_CODE", "CONT_LENGTH", "SERVER"))

def http_requester(arguments):
	thread_list = []
	for i in range(0, arguments.threads):
		x = threading.Thread(target=http_requester_thread, args=(arguments.url, arguments.wordlist[i], arguments.timeout, arguments.filter_sc, arguments.filter_cl))
		thread_list.append(x)
		thread_list[i].start()

	# wait for all threads to finish
	for x in thread_list:
		x.join()

def http_requester_thread(url, path_list, _timeout, filter_sc, filter_cl): # add timeout
	global stop_threads

	for i in path_list:
		if stop_threads == True:
			break
		try:
			response = requests.get(f"{url}{i}", timeout=_timeout)
		except:
			print("[X] Connection ERROR: %-40s -------------------------------- X"%(str(url+i)))

		if str(response.status_code) in filter_sc:
			if filter_cl != -1:
				if (response.headers.get('Content-length') != None) and (int(response.headers.get('Content-length')) == filter_cl):					
					print("%-40s\t%-10s\t%-10s\t%-10s"%(str(url+i)[:40], str(response.status_code), str(response.headers['Content-length']), str(response.headers.get("Server"))))					
				else:
					continue
			else:
				print("%-40s\t%-10s\t%-10s\t%-10s"%(str(url+i)[:40], str(response.status_code), str(response.headers.get('Content-length')), str(response.headers.get("Server"))))
		else:
			print("%-40s\t%-10s\t%-10s\t%-10s"%(str(url+i)[:40], str(response.status_code), str(response.headers.get('Content-length')), str(response.headers.get("Server"))), end="\r")


def main():
	banner()
	args = check_arguments(parse_arguments())
	args.wordlist_path = args.wordlist.name
	args.wordlist = wordlist_splitter(args.wordlist, args.threads)	
	show_config(args)
	timestamp("start")
	header()
	http_requester(args)
	timestamp("finish")	

if __name__ == "__main__":
	global stop_threads	
	stop_threads = False
	try:
		main()
	except KeyboardInterrupt:
		stop_threads = True
		print("[X] KeyboardInterrupt: Finishing scan ============================== \n\n")
		timestamp("finish")
		exit(0)




	#http_requester_thread(args.url, args.wordlist[0], args.timeout, args.filter_sc, args.filter_cl)



# PACKAGES REQUIRED
# validators
# requests
# argparse
