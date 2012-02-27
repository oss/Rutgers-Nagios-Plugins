#!/usr/bin/python
import ConfigParser
import operator
import os,sys
import os.path
import httplib
import time
from optparse import OptionParser

def get_timestamp(file):
	stat=os.stat(file)
	return stat.st_mtime

def debug_print():
	print "servername=", server_name
	print "warn_time=",warn_time 
	print "crit_time=", crit_time 
	print "Zipped Filenames: ", zipped_files
	print "status_directory: ",status_directory
	print "make_status_directory: ",make_status_directory

def mark_file_out_of_date(filename):
	status_file_name = unzipped_directory+filename+"-out-of-date"
	#the status file doesn't exist, so it just became out of date	
	if not os.path.isfile(status_file_name):
		if debug:
			print "marking",filename,"as out of date (creating new statusfile)"
		status_file = open(status_file_name,'w')	
		status_file.write("Out of Date")
	else:
	#the file already exists. If it is older than warn_time, give a warning on filename (same w/ crit_time)
	#no one should edit the files between their creation and now, if they do the calculation below gets broken
		creation_time = os.stat(status_file_name).st_mtime
		current_time= time.time()
		age = int((current_time-creation_time) * 1/60 * 1/60) # convert time to hours
		if debug:
			print filename,"has a status file that is",age,"hours old"
		if int(warn_time) <= age < int(crit_time):
			warn_files.append((int(age),filename))
		elif age >= int(crit_time):
			crit_files.append((age,filename))

def remove_status_file(filename):
	to_delete = unzipped_directory+filename+"-out-of-date"
	try: 
		os.remove(to_delete)
	except Exception, e:
		print "ClamAV_Defs UNKNOWN-","error deleting statusfile",to_delete
		sys.exit(-1)
	


	


def get_remote_time(filename):
	conn=httplib.HTTPConnection(server_name)
	conn.request("HEAD","/"+filename)
	response=conn.getresponse()
	date_str = response.getheader("last-modified")
	date = time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
	if debug:
		print "The time of",filename,"on the remote server is",(time.mktime(date)*1/60 *1/60)
	return time.mktime(date) 

def check_times():
	for file in zipped_files:
		unzipped_time = get_timestamp(unzipped_directory+file.replace(".gz",""))
		remote_time=get_remote_time(file)
		difference = remote_time - unzipped_time
		difference = int(difference * 1/60 * 1/60)
		if debug:
			print file,"differs from the webserver by",difference,"hours"
		if int(warn_time) <= difference: # as longs as its at least warn level, mark it
					# we'll decide if its warn or critical later (in mark_file_out_of_date)
			mark_file_out_of_date(file)
		elif os.path.isfile(unzipped_directory+file+"-out-of-date"):
			if debug:
				print "deleting the status file for",file
			remove_status_file(file)
			

def sort_dict(dict):
	items=dict.items()
	items.sort(reverse=True)
	return	items

		

try:
	#if command-line options were passed for warn and crit time, override the default values
	parser=OptionParser()
	parser.add_option("-w","--warn-time",action="store",type="int",dest="warn_time")
	parser.add_option("-d","--debug",action="store_true",dest="debug" )
	parser.add_option("-s","--settings",action="store",dest="settings_file" )
	parser.add_option("-c","--crit-time",action="store",type="int",dest="crit_time")
	parser.add_option("-m","--make-status-dir",action="store_true",dest="make_status_directory")
	(options,args)= parser.parse_args()
	if options.settings_file:
		settings_file=options.settings_file
	else:
		sys.stderr.write("ClamAV_Defs UNKNOWN- a settings file must be specified\n")	
		sys.exit(-1)

#set global variables
	config = ConfigParser.ConfigParser()
	config.read(settings_file)
	server_name = config.get("main","server_name")
	warn_time = config.get("main","default_warn_time")
	crit_time = config.get("main","default_crit_time")
	unzipped_directory = config.get("main","unzipped_directory")
	status_directory=config.get("main","status_directory")
	make_status_directory_str=(config.get("main","make_status_directory"))
	make_status_directory = make_status_directory_str.lower() == "true"
	zipped_files=[]
	warn_files=[]
	crit_files=[]
	debug=False

	if options.warn_time is not None:
		warn_time=options.warn_time
	if options.crit_time is not None:
		crit_time=options.crit_time
	if options.debug:
		debug=True
	if options.make_status_directory:
		make_status_directory=True

	for filename in config.options("Filenames"):
		zipped_files.append(config.get("Filenames",filename))

#make sure unzipped directory is sane (actually a directory, and ends with a trailing slash)
	if not unzipped_directory.endswith("/"):
		unzipped_directory = unzipped_directory +"/"
	if not status_directory.endswith("/"):
		status_directory = status_directory +"/"

	if not os.path.isdir(unzipped_directory):
		print "ClamAV_Defs UNKNOWN-",unzipped_directory,"is not a directory"
		sys.exit(-1)
	if not os.path.isdir(status_directory):
		print status_directory, "does not exist"
		if make_status_directory:
			print "creating it"
			os.mkdir(status_directory)	
		else:	
			raise IOError(status_directory, "does not exist",2)

#Main program execution begins
	if debug:
		debug_print()
	check_times()
	exit_status=0
	if debug:
		print "warn:",warn_files
		print "crit:",crit_files
	if crit_files:
		exit_status=2 
		print "ClamAV_Defs CRITICAL-",
		for file in sorted(crit_files,reverse=True):
			print file[1], file[0],"hours",
		print
	elif warn_files:
		exit_status=1 
		print "ClamAV_Defs WARNING-",
		for file in sorted(warn_files,reverse=True):
			print file[1], file[0],"hours",
		print
	else:
		exit_status=0
		print "ClamAV_Defs OK-All files are up to date"

	sys.exit(exit_status)

except OSError, ex:	
	print "ClamAV_Defs UNKNOWN-" , sys.exc_info()[0], ex.args
	sys.exit(-1)

except AttributeError, SystemExit:
	pass
except SystemExit,e:
	raise e
		
except Exception, ex:
	print "ClamAV_Defs UNKNOWN-",sys.exc_info()[0], ex.args
