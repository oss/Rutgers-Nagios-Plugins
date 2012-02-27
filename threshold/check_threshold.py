#!/usr/bin/python

#Cacti Threshold checker plugin for nagios
#jarek@nbcs.rutgers.edu

import MySQLdb
import os,sys
from optparse import OptionParser
import ConfigParser
import signal

#constants
NAGIOS_CODES = { "OK":0, "WARNING":1, "CRITICAL":2, "UNKNOWN":3}
#config file to use if none is specified in the arguments
DEFAULT_CONFIG_FILE = "/usr/lib64/nagios/plugins/rutgers/etc/threshold.cfg"

#number of thresholds triggered
numBadReported=0
#number of thresholds not triggered
numGoodReported=0

class Host:
	def __init__(self, name):
		self.name = name
		self.thresholds = []
		self.serviceName = "Cacti Thresholds"

class Threshold:
	def __init__(self,serviceName,state,serviceDesc):
		self.serviceName = serviceName
		self.state = state
		self.serviceDesc = serviceDesc

#send threshold states to nagios
def submitToNagios(hostname, serviceName, serviceDesc, state):
	# the command we're going to run that sends the data to nagios
	command = NSCA_BIN + " \'" + hostname + "\' \'" + serviceName + "\' " + str(state) + " \'" + serviceDesc + "\' &>/dev/null"
	
	#increment number we've reported to nagios
	global numBadReported,numGoodReported, verboseMode
	if state==0:
		numGoodReported += 1
	else:
		numBadReported += 1
	#run the command, if it fails return a bad state and complain
	if os.system(command) != 0:
		print "CRITICAL: error running " + command
		sys.exit(NAGIOS_CODES['CRITICAL'])
	if verboseMode:
		print command+"\n"
		
#get hosts in threshold DB that went over their thresholds, and call submitToNagios w/ them
#all parameters are database connection information
def checkDB(DBhost,DBuser,DBpasswd,DBname):
	try:
		#connect to the DB 
		conn = MySQLdb.connect (host=DBhost, user=DBuser,passwd=DBpasswd,db=DBname)
		cursor = conn.cursor()
		#get info from all rows
		query = "SELECT name,host_id,thold_type,thold_hi,thold_low,lastread,thold_alert,bl_alert,bl_enabled FROM thold_data"
		cursor.execute(query)

		# our dictionary of hosts. Key is hostname (just so its easier to see if a host is in here)
		hosts = {}

		#for each row, get the hostname from a different talbeu, and report its status to nagios
		for row in cursor.fetchall():

			#grab units out of the threshold name
			#they are encased in [] and MUST be the last thing in the threshold name
			# (anything after them gets cut off)
			thresholdName = row[0]
			leftIndex = thresholdName.find("[")
			rightIndex = thresholdName.find("]")
			if leftIndex == -1 or rightIndex == -1:
				print "CRITICAL: Threshold '" + thresholdName + "' does not contain units surrounded by []";
				sys.exit (NAGIOS_CODES['CRITICAL'])
			units = thresholdName[leftIndex:rightIndex+1];
			thresholdName = thresholdName[:leftIndex].strip()

			#strip host from threshold name
			try: 
				hostname,thresholdName = thresholdName.split(':')
			except IndexError, e:
				print "CRITICAL: Threshold '" + thresholdName + "' does not contain a host name delimted by ':'";
				sys.exit (NAGIOS_CODES['CRITICAL'])
			if not hostname in hosts.keys():
				hosts[hostname] = Host(hostname)	

			#is it a hard hi/lo value?
			if row[2] == 0:
				#is it triggered?
				if (row[6] !=0):
					status = 2
					stateString = "CRITICAL"
				else:
					status = 0
					stateString = "OK"
				if not row[4]:
					lowThreshold ='None'
				else:
					lowThreshold = str(row[4])
				if not row[3]:
					highThreshold='None'
				else:
					highThreshold=str(row[3])

				desc_string =  stateString + " " +str(row[5]) + " " +units +  " Thresholds (" + lowThreshold + "," + highThreshold + ")" 
			#is it a baseline?
			elif row[8] == "on":
				#is it triggered low?
				if row[7] == 1:
					desc_string = "baseline low (" + str(row[5]) + ")"
					status =2
				#is it triggered high?
				elif row[7] == 2:
					desc_string = "baseline high (" + str(row[5]) + ")"
					status =2
				#it must be ok
				else:
					desc_string = "baseline ok (" + str(row[5]) + ")"
					status =0
			else:
				desc_string = "Not a hard high/low value or a baseline"
				status = 3

			thold = Threshold(thresholdName,status,desc_string)
			hosts[hostname].thresholds.append(thold)

	#if something went wrong, exit with an error and complain
	except MySQLdb.Error, e:
		print "CRITICAL: Database Error %d: %s" % (e.args[0], e.args[1])
		sys.exit (NAGIOS_CODES['CRITICAL'])
	return hosts
#called if the plugin is taking too long to execute
def timedOut():
	print "CRITICAL: timed out"
	sys.exit( NAGIOS_CODES['CRITICAL'])
	

#begin program execution

#get CLI arguments
parser = OptionParser()
parser.add_option("-f","--file",action="store",type="string",dest="config_file", help="Configuration file to use")
parser.add_option("-v","--verbose",action="store_true",default=False,dest="verboseMode", help="Enable verbose output for this script")
parser.add_option("-a","--all-thresholds",action="store_true",default=False,dest="allThresholds", help="Show results of all thresholds in service description, not just the triggered ones")
(options,args) = parser.parse_args()

if not options.config_file:
	config_file = DEFAULT_CONFIG_FILE
else:
	config_file = options.config_file

verboseMode = options.verboseMode
showAllThresholds = options.allThresholds

#read settings from config file
try:
	config = ConfigParser.ConfigParser()
	config.read(config_file)
	databaseHost = config.get("main","DatabaseHost")
	databaseUser = config.get("main","DatabaseUser")
	databasePasswd = config.get("main","DatabasePasswd")
	databaseName = config.get("main","DatabaseName")
	NSCA_BIN = config.get("main","NSCACommand")
	timeoutSeconds = int( config.get("main","TimeoutSeconds") )
except ConfigParser.NoSectionError,e:
	print "CRITICAL: error reading from config file \'" + config_file +"\' Either it isn't readable, or is missing the section \'main\'"
	sys.exit( NAGIOS_CODES['CRITICAL'])
except ConfigParser.NoOptionError, e:
	print "CRITICAL: error reading from config file \'" + config_file +"\' Missing value for setting \'"+ e.option+"\' in section \'"+ e.section + "\'"
	sys.exit( NAGIOS_CODES['CRITICAL'])

#if the plugin takes longer than timeoutSeconds to run, it times out and we call timedOut()
signal.signal(signal.SIGALRM,timedOut)
signal.alarm(timeoutSeconds)

#get all our threshold information, store it in a dictionary of hosts (each host has several thresholds in it)
hosts = checkDB(databaseHost,databaseUser,databasePasswd,databaseName)

#loop over all of ours hosts
for hostname,host in hosts.iteritems():
	# how many thresholds for this host are triggered?
	numBadThresholds = 0
	#what is the output for this host?
	descString = ""

	#loop over all thresholds for this host
	for thold in host.thresholds:
		#if its triggered, add it to our description and incriment number triggered 
		if thold.state != 0:
			descString += "\n" + thold.serviceName + ": " + thold.serviceDesc
			numBadThresholds += 1
		elif showAllThresholds:
			descString += "\n" + thold.serviceName + ": " + thold.serviceDesc

	# if none were triggered for this host, its ok
	if numBadThresholds == 0:
		descString = "OK: 0/"+str(len(host.thresholds))+" thresholds triggered" + descString
		exit_status = NAGIOS_CODES['OK']

	# otherwise, its critical, show the thresholds that were bad
	else:
		descString = "CRITICAL: " + str(numBadThresholds)+"/"+str(len(host.thresholds)) + " thresholds triggered" + descString
		exit_status = NAGIOS_CODES['CRITICAL']

	#send this hosts's info to nagios
	submitToNagios(hostname, host.serviceName, descString, exit_status)

#print out status, and return OK (if we got this far without an error, status must be OK)
print "OK:",numBadReported,"host(s) with threshold(s) triggered,", numGoodReported, "host(s) with none triggered"
sys.exit(NAGIOS_CODES['OK'])
