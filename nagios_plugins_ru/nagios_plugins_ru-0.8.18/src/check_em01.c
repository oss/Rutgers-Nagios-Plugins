/* Print Debug Info. Uncomment the #define below to print debugging to stderr */

//#define DEBUG
//#define DEBUG_ERROR_CORRECTION

/* Number of seconds to timeout */
#define CONNECT_TIMEOUT 5
#define MAX_RETRIES 5
/******************************************************************************

Esensors EM01 Plugin.
Description: This plugin is written mainly for Nagios, but can be
easily used for other software too.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

Credits:
Duncan Robertson [Duncan.Robertson@vsl.com.au] - 64bits fix
Ali Rahimi [ali@XCF.Berkeley.EDU] - Sockets code
David W. Deley [deleyd@cox.net] - Random numbers

$Id: check_em01.c,v 2.3.2 1:00 PM 1/04/2010 $

******************************************************************************/
/** This value is to multiple the Voltage value detected by a fixed constant. (
	* i.e. if you are using a regulator supply to measure AC voltage)
	*/
const float VOLTAGE_MULTIPLIER = 1.0;
const float VOLTAGE_OFFSET = 0.0; 

/**
*  Tells the plugin to reset contact closure on trigger. Change to 0 to turn this off.
*/
const int RESETCONTACT = 1;

/**
* Maximum percentage of deviation of data from average, for the data to be included in average calculation.
*/
const float MAX_DEVIATION_PERCENT = 25.0;

/*
* Maximum number of loops to average data for error correction.
*/
const int MAX_ECCOUNT = 7;

/*
* Poll Time in ms between each data sample  .
*/
const int POLL_DELAY = 1200;

/*
* Weighted Average Data Filter  .
*/
#define DATA_FILTER
const int DATA_FILTER_TRESHOLD = 10;	// Filter Coefficient for Illumination & thermistor
const int DATA_WEIGHT = 10;		// No. of replicas of good data



const int DEFAULTPORT = 80;
const char *progname = "check_em01";
const char *revision = "$Revision: 2.2 $";
const char *copyright = "2009";
const char *email = "techhelp@eEsensors.com";

typedef int SOCKET;
typedef enum {E_NET_ERRNO=-1, E_NET_OK=0} NetErrnoType;

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <math.h>
#include <time.h>

void     INThandler(int);

static NetErrnoType net_errno = E_NET_OK;
static int saved_errno = 0;
static SOCKET s;


/* Translations between ``net_errno'' values and human readable strings.
*/
static const char *net_syserrlist[] = {
	"All was chill"
};




#ifdef STRERROR_NOT_DEFINED
const char *strerror(int errno) { return sys_errlist[errno]; }
#endif

static void NetSetErrno(NetErrnoType e)
{
	if(e == E_NET_ERRNO)saved_errno = errno;
	net_errno = e;
}



/* NetErrStr()
*--------------------------------------------------------------------
* Returns a diagnostic message for the last failure.
*/
const char *NetErrStr()
{
	return net_errno==E_NET_ERRNO ? strerror(saved_errno) :
	net_syserrlist[net_errno];
}

/* NetErrNo()
*--------------------------------------------------------------------
* Returns a diagnostic number for the last failure.
*/
NetErrnoType NetErrNo()
{
	return net_errno;
}

/* NetMakeContact()
*--------------------------------------------------------------------
* Makes a tcp connection to a host:port pair.
*--------------------------------------------------------------------
* ``Hostname'' can either be in the form of a hostname or an IP address
* represented as a string. If the hostname is not found as it is,
* ``hostname'' is assumed to be an IP address, and it is treated as such.
*
* If the lookup succeeds, a TCP connection is established with the
* specified ``port'' number on the remote host and a stream socket is
* returned.
*
* On any sort of error, an error code can be obtained with @NetErrNo()
* and a message with @NetErrStr().
*/
SOCKET
NetMakeContact(const char *hname, int port)
{
	int fd;
	struct sockaddr_in addr;
	struct hostent *hent;

	fd = socket(AF_INET, SOCK_STREAM, 0);
	if(fd == -1)
	{
		NetSetErrno(E_NET_ERRNO);
		return -1;
	}


	hent = gethostbyname(hname);
	if(hent == NULL)
	addr.sin_addr.s_addr = inet_addr(hname);
	else
	memcpy(&addr.sin_addr, hent->h_addr, hent->h_length);
	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);

#ifdef DEBUG
	fprintf(stderr, "Creating Connection... ");
#endif

	if(connect(fd, (struct sockaddr *)&addr, sizeof(addr)))
	{
		NetSetErrno(E_NET_ERRNO);
		return -1;
	}

	NetSetErrno(E_NET_OK);
	return fd;
}



/*********************************************************************************/

float Exp10(int n)
{
	int i;
	float result = 1;
	for(i =n; i; i--)
	result *= 10;
	return result;
}

float myatof(const char *s)
{
	float result;
	int val = 0, dec = 0, n = 0;;
	int neg = 0;

	/* skip white space */
	while (*s == ' ' || *s == '\t') {
		s++;
	}

	if (*s == '-') {
		neg = 1;
		s++;
	} else if (*s == '+') {
		s++;
	}
	while (*s >= '0' && *s <= '9') {
		val *= 10;
		val += *s++ - '0';
	}
	result = val;

	if(*s == '.') {
		*s++;
		while (*s >= '0' && *s <= '9') {
			dec *= 10;
			dec += *s++ - '0';
			n++;
		}

		if(n)
		result += dec/Exp10(n);
	}

	if (neg) {
		result = -result;
	}

	return result;
}

/*
This function is an abstraction layer between app and sockets.
Currently, it only passes down all the arguments it receives from
app. However, in the future, it will be easier to change 
sockets library and not affect the main app code at all.
*/
SOCKET connectWebsensor (char* hostname, int port){
	//SOCKET s;
	fd_set readfds;

	int i;
	s = NetMakeContact(hostname,port);
	if(s==-1) {
		return -1;
	}
	else{
		/* Make the socket non-blocking */
		ioctl(s, FIONBIO, 1);
		FD_ZERO(&readfds);
		FD_SET(0, &readfds);
		FD_SET(s, &readfds);
		return s;

	}
}

/*
This function is called when a timeout has occurred.
It shutsdown the socket and allows the main loop to continue.
*/
void  INThandler(int sig)
{
	signal(SIGALRM, SIG_IGN);
	shutdown(s, SHUT_RDWR);
	alarm(CONNECT_TIMEOUT);
	signal(SIGALRM, INThandler);
}



float CalculateAverage(char** avgDataBuf, int pos, int len){
	char datachar[7];
	int averageCountIndex;
	int j = 0;
	int k = 0;
	float min_dev=100;
	float dev=0;
	float fdata[10];
	float gdata;
	float dataAvg = 0.0;
	float data_sum = 0.0;
	float data[10];
		

	for(averageCountIndex = 0; averageCountIndex < MAX_ECCOUNT; averageCountIndex++)
	{
		strncpy(datachar, avgDataBuf[averageCountIndex]+pos, len);
		datachar[len] = '\0';
		data[averageCountIndex] = myatof(datachar);
	#ifdef DEBUG_ERROR_CORRECTION
		printf("\nData(%d) = %f",averageCountIndex, data[averageCountIndex]);
	#endif
			
		#ifdef DATA_FILTER	
		if(data[averageCountIndex]>DATA_FILTER_TRESHOLD)
		{
			for(j=0;j<DATA_WEIGHT;j++)
			{
				fdata[j]=data[averageCountIndex];
				k++;
				data_sum += fdata[j];
			}
		 #ifdef DEBUG_ERROR_CORRECTION
		 printf("\nFData sum = %f",data_sum);
		 #endif
		}	
		#endif
		data_sum += data[averageCountIndex];
				
	}
	k += MAX_ECCOUNT;
	dataAvg = data_sum / k;
	data_sum = 0.0;
	#ifdef DEBUG_ERROR_CORRECTION	
	printf("\nAverage = %f",dataAvg);
	#endif	
	for(averageCountIndex = 0; averageCountIndex < MAX_ECCOUNT; averageCountIndex++)
	{		dev = (fabs(data[averageCountIndex] - dataAvg) / dataAvg) * 100;
		#ifdef DEBUG_ERROR_CORRECTION		
		printf("\ndata(%d)= %f and Deviation = %f ",averageCountIndex, data[averageCountIndex], dev);
		#endif	
		if(dev <= min_dev)
		{
			gdata = data[averageCountIndex];	
			min_dev = dev;
			continue;		 
		}
		#ifdef DEBUG_ERROR_CORRECTION
		else
		{
		printf("\nBad Data(%d) = %f",averageCountIndex, data[averageCountIndex]);
		}
		#endif
	}
	#ifdef DEBUG_ERROR_CORRECTION
	printf("\nData with min Deviation(%f) = %f",min_dev, gdata);
	#endif	
	//dataAvg = data_sum / ngd; // average of all good data
	gdata += 0.01;
	return gdata;
}

main(int argc, char **argv)
{
	int l, retry, averageCountIndex, i, random_backoff;
	long ms;
	float data, ecData;
	char iobuf[1024], timestr[32], datachar[7];
	char* pos;
	char* averageDataBuffer[MAX_ECCOUNT];
	char rcvd_checksum, calc_checksum;
	time_t start_time, cur_time;
	double r, x;
	SOCKET contacts;

	progname = argv[0];
	if(argc < 2 || strcmp(argv[1],"--help") == 0) {
		print_help();
		return(3);
	}

	time(&cur_time);
	sprintf(timestr, "%s", ctime(&cur_time));

	signal(SIGALRM, INThandler);
	alarm(CONNECT_TIMEOUT);
	
	for(averageCountIndex = 0; averageCountIndex < MAX_ECCOUNT; averageCountIndex++){
		
		for(retry = 0; retry < MAX_RETRIES; retry++){

			srand((unsigned int)time(NULL));

			r = (   (double)rand() / ((double)(RAND_MAX)+(double)(1)) ); 
			x = (r * 20); 	
			random_backoff = (int) x; 

#ifdef DEBUG
			fprintf(stderr, "Sleeping: %d ", 100+random_backoff);
#endif
			for(ms=0; ms < (POLL_DELAY + random_backoff); ms++){
				usleep(1000); 
			}


			/* make connection to websensor */
			s = connectWebsensor(argv[1], DEFAULTPORT);
#ifdef DEBUG
			fprintf(stderr, "Socket created ");
#endif

			if(NetErrNo() != 0){
#ifdef DEBUG
				fprintf(stderr, "Could not connect to Websensor because %s, will retry %d more times.\n", NetErrStr(), 10-retry);
#endif
				shutdown(s, SHUT_RDWR);
				continue;
			}


			/* send HTTP GET request to obtain data */
			if(argc>2){

				switch (toupper(argv[2][0])){
				case 'R':
					write(s, "GET /index.html?eR HTTP/1.1\r\nUser-Agent: EsensorsPlugin\r\nHost: localhost\r\n\r\n", 77);
					break;

				case 'V':
					write(s, "GET /index.html?eV HTTP/1.1\r\nUser-Agent: EsensorsPlugin\r\nHost: localhost\r\n\r\n", 77);
					break;

				default:
					write(s, "GET /index.html?em123456 HTTP/1.1\r\nUser-Agent: EsensorsPlugin\r\nHost: localhost\r\n\r\n", 83);
					break;
				}
			}

			else{ // Not enough arguments from command line. Use default websensor command.
				write(s, "GET /index.html?em123456 HTTP/1.1\r\nUser-Agent: EsensorsPlugin\r\nHost: localhost\r\n\r\n", 83);
			}

#ifdef DEBUG
			fprintf(stderr, "Wrote to Socket... ");
#endif

			l = read(s, iobuf, sizeof(iobuf));

#ifdef DEBUG
			fprintf(stderr, "Read from socket\n");
#endif
			
			/* No data returned from websensor. Will retry again. */

			if(l<=0){
#ifdef DEBUG
				fprintf(stderr, "No Data Read, will retry %d more times.\n", MAX_RETRIES-retry);
#endif
				shutdown(s, SHUT_RDWR);
				continue;
			}

			pos = strstr(iobuf, "<body>");
			if(pos == 0){
				printf("Invalid data received.\n");
				return(3);  
			}



			//Search for the sensor data string
			pos = strstr(iobuf, "TF:");
			if(pos == 0){
				pos = strstr(iobuf, "TC:");
				if(pos == 0){
#ifdef DEBUG			
					fprintf(stderr, "Using default parsing parameters.\n");			
#endif
					pos=&iobuf[167];
				}
			}

			if(argc>2 && toupper(argv[2][0]) == 'V'){ //If the command was for voltage measurement, try looking for the string 'RV' instead.
				pos = strstr(iobuf, "RV");
				if(pos == 0 || pos[1] != 'V'){
#ifdef DEBUG
					fprintf(stderr, "Invalid Data Received. Will retry %d more times.\n", MAX_RETRIES-retry);
#endif
					shutdown(s, SHUT_RDWR);
					continue;
				}
				else{
					pos = pos - 2;
					break; //Voltage data looks good
				}
			}
			
			pos = pos - 2;
			/* Unsupported command. OBSOLETE CODE */
			if(pos[0] == '#'){
				printf("Invalid Command. Option %c selected may not be available for this websensor.\n", argv[2][0]);
				return 3;
			}

			/* The http data is not properly formatted. */
			if(pos[2] != 'T' && pos[2] != 'R' && pos[1] != 'v'){
#ifdef DEBUG
				fprintf(stderr, "Data input incorrect, will retry %d more times.\n", MAX_RETRIES-retry);
#endif
				shutdown(s, SHUT_RDWR);
				continue;
			}
			else{
				break; /* All data looks good. Break out of loop. */
			}
		}
		
		
		/* Retried 3 times earlier and still no good data. Time to exit */
		if(retry >= MAX_RETRIES){
			printf("NO DATA\n");
			return 3;
		}
		else{
			shutdown(s, SHUT_RDWR);
		}
		
		averageDataBuffer[averageCountIndex] = (char*) malloc(strlen(pos)+1);
		strncpy(averageDataBuffer[averageCountIndex], pos, strlen(pos));	
	}
	time(&cur_time);
	sprintf(timestr, "%s", ctime(&cur_time));

	if(argc > 2){
		switch(toupper(argv[2][0])){
			
		case 'G':  //Cacti/RRDTool Output TempF:** Humid:**
			{
				data = CalculateAverage(averageDataBuffer, 5, 5);
				printf("Temp:%3.2f ", data);
				//printf("TempUnit:%c ", pos[3]); //prints the temperature unit
				
				data = CalculateAverage(averageDataBuffer, 13, 4);
				printf("Humid:%3.2f ", data);
				
				data = CalculateAverage(averageDataBuffer, 21, 5);
				printf("Illum:%3.2f\n", data);
				
				return(0);
			}
			break;	
			
		case 'T': 
			{
				data = CalculateAverage(averageDataBuffer, 5, 5);
				if(argc != 7){
					printf("(No limits specified) Temperature: %3.2f %c | Temp%c=%3.2f\n", data, pos[3], pos[3], data);
					return(0);
				}
				if(data < myatof(argv[5]) || data > myatof(argv[6])){
					printf("CRITICAL ( %s< or >%s ) Temperature: %3.2f %c | Temp%c=%3.2f\n", argv[5], argv[6], data, pos[3], pos[3], data);
					return(2);
				}
				else if(data < myatof(argv[3]) || data > myatof(argv[4])){
					printf("WARNING ( %s< or >%s ) Temperature: %3.2f %c | Temp%c=%3.2f\n", argv[3], argv[4], data, pos[3], pos[3], data);
					return(1);
				}
				else{
					printf("OK Temperature: %3.2f %c | Temp%c=%3.2f\n", data, pos[3], pos[3], data);
					return(0);
				}
			}
			break;

		case 'H': 
			{
				data = CalculateAverage(averageDataBuffer, 13, 4);
				if(argc != 7){
					printf("(No limits specified) %3.2f% | Humid=%3.2f\n", data, data);
					return(0);
				}
				if(data < myatof(argv[5]) || data > myatof(argv[6])){
					printf("CRITICAL ( %s< or >%s ) Humidity: %3.2f% | Humid=%3.2f\n", argv[5], argv[6], data, data);
					return(2);
				}
				else if(data < myatof(argv[3]) || data > myatof(argv[4])){
					printf("WARNING ( %s< or >%s ) Humidity: %3.2f% | Humid=%3.2f\n", argv[3], argv[4], data, data);
					return(1);
				}
				else{
					printf("OK Humidity: %3.2f% | Humid=%3.2f\n", data, data);
					return(0);
				}
			}
			break;

		case 'I': 
			{
				data = CalculateAverage(averageDataBuffer, 21, 5);
				if(argc != 7){
					printf("(No limits specified) Illumination: %3.2f | Illum=%3.2f\n",  data, data);
					return(0);
				}
				if(data < myatof(argv[5]) || data > myatof(argv[6])){
					printf("CRITICAL ( %s< or >%s ) Illumination: %3.2f | Illum=%3.2f\n", argv[5], argv[6],  data, data);
					return(2);
				}
				else if(data < myatof(argv[3]) || data > myatof(argv[4])){
					printf("WARNING ( %s< or >%s ) Illumination: %3.2f | Illum=%3.2f\n", argv[3], argv[4],  data, data);
					return(1);
				}
				else{
					printf("OK Illumination: %3.2f | Illum=%3.2f\n",  data,data);
					return(0);
				}
			}
			break;

		case 'C':
			{
				if(iobuf[160] == 'W'){
					printf("OK Contacts Close. | Contacts=0\n");
					return(0);
				}
				else if(iobuf[160] == 'N'){
					printf("CRITICAL Contacts Open! | Contacts=1\n");
					
					/* Reset the Contact Closure back to Closed */
					if(RESETCONTACT == 1){
						contacts = connectWebsensor(argv[1], DEFAULTPORT);
						if(NetErrNo() != 0){
							fprintf(stderr, "Could not reset contact closure", NetErrStr());
							shutdown(contacts, SHUT_RDWR);
							return(2);
						}
						write(contacts, "GET /index.html?eL HTTP/1.1\r\nUser-Agent: EsensorsPlugin\r\nHost: localhost\r\n\r\n", 77);
						l = read(contacts, iobuf, sizeof(iobuf));
						//printf("%s", iobuf);
						shutdown(contacts, SHUT_RDWR);	
					}
					return(2);
				}
				else{
					printf("WARNING Unknown status. Try Reset Device.\n");
					return(1);
				}
			}
			break;

		case 'R':
			{
				data = CalculateAverage(averageDataBuffer, 4, 6);
				if(argc != 7){
					printf("(No limits specified) Ext. Temperature: %3.2f %c | XTemp%c=%3.2f\n", data, pos[3], pos[3], data);
					return(0);
				}
				if(data < myatof(argv[5]) || data > myatof(argv[6])){
					printf("CRITICAL ( %s< or >%s ) Ext. Temperature: %3.2f %c | XTemp%c=%3.2f\n", argv[5], argv[6], data, pos[3], pos[3], data);
					return(2);
				}
				else if(data < myatof(argv[3]) || data > myatof(argv[4])){
					printf("WARNING ( %s< or >%s ) Ext. Temperature: %3.2f %c | XTemp%c=%3.2f\n", argv[3], argv[4], data, pos[3], pos[3], data);
					return(1);
				}
				else{
					printf("OK Ext. Temperature: %3.2f %c | XTemp%c=%3.2f\n", data, pos[3], pos[3], data);
					return(0);
				}
			}
			break;

		case 'V':
			{
				data = CalculateAverage(averageDataBuffer, 21, 5);
			
				if(data <= VOLTAGE_OFFSET+(0.5*VOLTAGE_MULTIPLIER)){ //Anything less than VOLTAGE_OFFSET AC should be considered as zero
					data = 0.00;
				}
				
				if(argc != 7){
					printf("(No limits specified) Voltage: %3.2f V | Voltage=%3.2f\n", data,data);
					return(0);
				}
				if(data < myatof(argv[5]) || data > myatof(argv[6])){
					printf("CRITICAL ( %s< or >%s ) Voltage: %3.2f V | Voltage=%3.2f\n", argv[5], argv[6], data, data);
					return(2);
				}
				else if(data < myatof(argv[3]) || data > myatof(argv[4])){
					printf("WARNING ( %s< or >%s ) Voltage: %3.2f V | Voltage=%3.2f\n", argv[3], argv[4], data, data);
					return(1);
				}

				else{
					printf("OK Voltage: %3.2f V | Voltage=%3.2f\n", data,data);
					return(0);
				}
			}

			default : 
			printf("Please choose only 'T', 'H', 'I', 'R', 'V' or 'C'.\n Please refer to README for further instructions.\n");
			break;
		}
	}
	else{
		iobuf[195] = 0;
		fprintf(stderr, "2");
		printf("%s\t%s", pos+2, timestr);
		fprintf(stderr, "3");
	}

	return 0;
}

int print_help (void)
{
	fprintf (stdout, "Copyright (c) 2005-2009 Esensors, Inc <TechHelp@eEsensors.com>\n");
	fprintf (stdout,("This plugin is written mainly for Nagios/Cacti/RRDTool, but can work standalone too. \nIt returns the HVAC data from the EM01 Websensor\n\n"));
	print_usage ();
	return 0;
}


int print_usage (void)
{
	fprintf(stdout, "usage: \n %s [hostname] [T/H/I] [LowWarning HighWarning LowCritical HighCritical]\n\n", progname); 
	fprintf(stdout, "Only the hostname is mandatory. The rest of the arguments are optional\n");
	fprintf(stdout, "T is for Temperature data, H for Humidity Data and I for Illumination data\nExamples:\n");
	fprintf(stdout, "This will return all HVAC data: \n %s 192.168.0.2\n\n", progname); 
	fprintf(stdout, "This will return only Illumination data: \n %s 192.168.0.2 I\n\n", progname); 
	fprintf(stdout, "This will return temperature data with status: \n %s 192.168.0.2 T 65 85 60 90\n\n", progname); 
	fprintf(stdout, "This will return humidity data with status: \n %s 192.168.0.2 H 25.5 50 15 70.5\n\n", progname); 
	fprintf(stdout, "This will return Cacti/RRDTool format: \n %s 192.168.0.2 G\n\n", progname); 	
	fprintf(stdout, "For further information, please refer to the README file included with the package\n");
	fprintf(stdout, "or available for download from http://www.eesensors.com\n");
	return 0;
}
