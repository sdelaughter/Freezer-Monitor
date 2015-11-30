"""Monitoring Script for -80 Freezers
Written by Samuel DeLaughter
University of Massachusetts Amherst
Departments of Chemistry and Biochemistry & Molecular Biology

Watches for a change in state on a particular GPIO pin of the Raspberry Pi connected to a freezer.
Sends a warning message if the switch opens.
Sends an all-clear message once the switch closes again.
If a warning or all-clear message fails to send, a backup message will be sent to net-l.

Contact information is read from a CSV file which can be identical on all Raspberry Pis.
The Pi's local IP address is used as the key to lookup other values in the CSV file.
The first row of the CSV file must contain the following four column headers:
	IP,Location,Department,Email
NOTE: Capitalization must be identical but order is irrelevant.  There should be no spaces on either side.
	
If two or more email addresses are associated with a single device, they should be formatted as follows in the CSV:
	"it@example.edu, jschmoe@example.edu"	
NOTE: The double quotes above are necessary

Example CSV File:
	Freezer Number,Department,PI,Email,Location,IP,Hostname,Comments
	1,Chemistry,Chemistry (backup),minus80-backup@example.edu,BLDG 345,10.12.80.11,minus80-chembackup-1, Backup Minus-80
	2,Chemistry,Schmoe,"minus80-schmoe@example.edu, it@example.edu",BLDG 456,10.12.80.12,minus80-schmoe-1,
	
NOTE: The trailing comma on the third line is necessary for the comment field, which is left blank here.

If any errors are encountered while reading the CSV file, a warning message will be sent to the backup email address.


"""

__version__ = "1.3.1"

import sys
import time
import argparse
import logging
import logging.handlers
from time import sleep
from pprint import pprint
from threading import Thread
from datetime import datetime

import RPi.GPIO as GPIO

import csv
#import socket
import netifaces as ni
import smtplib
from email.mime.text import MIMEText

#Set path for CSV info file
CSV_PATH = '/usr/local/python/freezer/lib/python2.7/site-packages/freezer_info_dummy.csv'

#Set backup email address
#MAKE SURE TO CHANGE THIS BEFORE DEPLOYING
BACKUP_EMAIL = 'it@example.com'

#Set up logging
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')	#Print to syslog
std_handler = logging.StreamHandler(sys.stdout)			#Print to stdout
my_logger.addHandler(handler)
my_logger.addHandler(std_handler)


def parse_info(csv_file):
	"""Parse the CSV file to find contact and location information for freezers

	Parameters
	----------
	csv_file : string
		The full pathname of the CSV file containing contact information
		This path is set as the global variable CSV_PATH at the top of this file

	Returns
	-------
	entries: list
		A list of dictionaries, one for each row
		Each dictionary's keys are the column headers from the file's first row

	"""

	reader = csv.reader(open(csv_file, 'rU'))
	rows = []
	for row in reader:
		rows.append(row)
	header = rows.pop(0)
	entries = []
	for row in rows:
		entry = {}
		for i in range(len(row)):
			entry[header[i]] = row[i]
		entries.append(entry)
	return entries


def send_mail(status, recipients, location, dept, event_time):
	"""Send a warning or all-clear message, depending on the switch status
	If the message fails to send, send a message to the backup contact
	If that message fails to send, try the original message again in 5 minutes
	
	Parameters
	----------
	status : int
		This should be either a 0 or 1
		1 indicates a problem and will trigger a warning message
		0 indicates a resolved problem and will trigger an all-clear message
	recipients : list
		A list of strings, one for each email address to contact
		This is extracted from the CSV file via parse_info() and handle_event()
	location : string
		The physical location (room number) of the freezer
		This is extracted from the CSV file via parse_info() and handle_event()
	dept : 
		The department which owns the freezer
		Used to set the reply-to value for the email
		This is extracted from the CSV file via parse_info() and handle_event()
	event_time : string
		The time at which the event was detected
		
	Returns
	-------
	None
	
	"""
	
	my_logger.debug('Attempting to send mail to ' + str(recipients))
		
	if status == 1:
		msg = 'A potential problem has been detected with the -80 freezer located in room: ' + str(location)
		msg += '\nThis event was detected at: ' + str(event_time)
		msg = MIMEText(msg)
		msg['Subject'] = ('ALERT: Problem with -80 freezer in ' + str(location))
	elif status == 0:
		msg = 'The problem detected with the -80 freezer located in room: ' + str(location) + ' appears to have been resolved.'
		msg += '\nThis resolution was detected at: ' + str(event_time)
		msg += '\nPlease check this freezer to confirm that it is now working properly.'
		msg = MIMEText(msg)
		msg['Subject'] = ('Re: ALERT: Problem with -80 freezer in ' + str(location))
		
	if dept == 'BMB':
		sender = 'freezer-monitor@biochem.umass.edu'
		reply_to = 'ithelp@biochem.umass.edu'
	else:
		sender = 'freezer-monitor@chem.umass.edu'
		reply_to = 'ithelp@chem.umass.edu'
	msg['reply-to'] = reply_to
	
	s = smtplib.SMTP('mailhub.oit.umass.edu')
	try:
		s.sendmail(sender, recipients, msg.as_string())
		my_logger.info('Sent mail to: ' + str(recipients) + '		 For freezer in: ' + str(location))
	except:
		my_logger.warning('Failed to send ' + str(msg_type)+ ' message to ' + str(recipients))
		try:
			if status == 1:
				msg = 'A problem has been detected with a -80 freezer, but the warning message failed to send to the PI\n'
			elif status == 0:
				msg = 'A problem with a -80 freezer has been resolved, but the all-clear message failed to send to the PI\n'
			msg += '\nFreezer Location: ' + str(location)
			msg += '\nIntended Recipient(s): ' + str(recipients)
			msg += '\nTime of Event: ' + str(event_time)
			msg = MIMEText(msg)
			msg['Subject'] = ('ALERT: Failed to notify PI about the status of -80 Freezer in ' + str(location))
			msg['reply-to'] = reply_to
			s.sendmail(sender, [BACKUP_EMAIL], msg.as_string())
			my_logger.info('Sent message failure warning to ' + str(BACKUP_EMAIL) + ' for freezer in: ' + str(location))
		except:
			if status == 1:
				my_logger.critical('Failed to alert net-l that a warning message failed to send. Trying original message again in 5 minutes.')
			if status == 0:
				my_logger.critical('Failed to alert net-l that an all-clear message failed to send. Trying original message again in 5 minutes.')
			time.sleep(300)
			send_mail(status, recipients, location, dept, event_time)


def handle_csv_error(status, ip, event_time):
	"""Handle any errors encountered while reading the CSV file
	Send mail to net-l about the CSV error and the freezer event
	If the message fails to send, wait 15 minutes and try again
	
	Parameters
	----------
	status : int
		This should be either a 0 or 1
		1 indicates a problem and will trigger a warning message
		0 indicates a resolved problem and will trigger an all-clear message
	
	ip : string
		The IP address of the Raspberry Pi sending the message
		When the CSV file can't be read, this is the only information available
	
	event_time : string
		The time at which the event was detected
	
	Returns
	-------
	None
	
	"""
	my_logger.critical('!!! Failed to read CSV File !!!')
	try:
		msg = 'Failure to read CSV file on RaspberryPi at IP: ' + str(ip)
		msg += '\nEvent Time: ' + str(event_time)
		msg += '\n\nPlease verify the contents and structure of the CSV file ASAP.	Alert messages for freezer events cannot be sent until this error is resolved.'
		if status == 1:
			msg += '\n\nAlso note that this message indicates a potential problem with the freezer connected to this RaspberryPi. Please check the freezer or notify the appropriate lab members immediately.'
		elif status == 0:
			msg += '\n\nNote that this message indicates the resolution of a potential problem with the freezer connected to this RaspberryPi. Please notify the appropriate lab members to confirm that the freezer is now working properly.'
		msg = MIMEText(msg)
		
		msg['Subject'] = ('Freezer CSV error for RPi at IP' + str(ip))
		msg['reply-to'] = 'ithelp@chem.umass.edu'
		sender = 'freezer-monitor@chem.umass.edu'
		s = smtplib.SMTP('mailhub.oit.umass.edu')
		s.sendmail(sender, ['net-l@chem.umass.edu'], msg.as_string())
		my_logger.info('Sent warning to net-l')
		sleep(900)
		handle_event(status)
	except:
		my_logger.critical('!!! Failed to read CSV File and failed to alert net-l !!!')
		sleep(900)
		handle_event(status)

				
			
def handle_event(status):
	"""Called by the monitor() function whenever the status of the freezer changes
	Also called if the freezer is in error status when this script starts
	This function should always be run in its own thread in case another freezer event occurs before it finishes
	Does the following in order:
		Store the current time (at which the event was detected)
		Detect the local IP address
		Parse the CSV file with parse_info()
		If any rows in the CSV file have an IP field matching the local IP:
			Send an email to the corresponding addresses with send_mail()
	
	Parameters
	----------
	status : 
		This should be either a 0 or 1
		1 indicates a problem and will trigger a warning message
		0 indicates a resolved problem and will trigger an all-clear message
	
	Returns
	-------
	None
	
	"""
	event_time = time.asctime()
	my_logger.info('Freezer event detected at ' + str(event_time))
	
	#Detect the local IP address
	ip = ni.ifaddresses('eth0')[2][0]['addr']
	#If netifaces is not installed, the line below can be used to detect the local IP instead
	#ip = ([(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
	
	my_logger.debug('Detected local IP address of ' + str(ip))
	parsed_csv = False
	while not parsed_csv:
		try:
			info = parse_info(CSV_PATH)
			parsed_csv = True
			my_logger.debug('Finished parsing CSV file')
		except:
			handle_csv_error(status, ip, event_time)
						
	for i in range(len(info)):
		if info[i]['IP'] == ip:
			recipients = ((info[i]['Email']).split(', '))
			location = (info[i]['Location'])
			department = (info[i]['Department'])
			send_mail(status, recipients, location, department, event_time)
	

def gpio_setup(PIN):
	"""Setup the GPIO pins
	
	Parameters
	----------
	PIN : int
		The board number of the GPIO pin used to detect the freezer's status
	
	Returns
	-------
	None
	
	"""
	
	#Set the pin numbering system to use (GPIO.BOARD or GPIO.BCM)
	GPIO.setmode(GPIO.BOARD)
	
	#Disable GPIO warning messages (not really sure what these messages would be, but disabling them appears to be standard practice)
	GPIO.setwarnings(False)
	
	#Set the pin as an input with no internal pull-up or pull-down
	GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
	
	#Uncomment these lines to set a pull-down on all unmonitored pins
	#for i in [3, 5, 7, 11, 13, 15, 19, 21, 23, 29, 31, 33, 35, 37, 8, 10, 12, 16, 18, 22, 24, 26, 32, 36, 38, 40]:
	#	if i != PIN:
	#		GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)			
	
			
def monitor(PIN):
	"""Monitor a given GPIO pin for changes in its state
	Launch a new handle_event() thread when the state changes, passing the state as an argument
	
	Parameters
	----------
	PIN : int
		The board number of the GPIO pin used to detect the freezer's status
		
	Returns
	-------
	None
	
	"""
	a = GPIO.input(PIN)
	if a == 1:
	#If the initial reading is 1, handle an event
	#Necessary for detecting a problem after recovering from a power outage
		event_thread=Thread(target=handle_event, args=(1,), name='Event Handling Thread')
		event_thread.daemon = True
		event_thread.start()
	while True:
		b = GPIO.input(PIN)
		if a != b:
			my_logger.info('Status changed to: ' + str(b) + ' , handling event')
			event_thread=Thread(target=handle_event, args=(b,))
			event_thread.daemon = True
			event_thread.start()
		a = b
		time.sleep(0.1)


def main():
	"""The main function
	Specify the GPIO pin to monitor, set it up, and monitor it
	
	Also sets up versioning -- run the script with -V or --version to print the version number
	The version number is set at the top of this script -- change it when making any changes
	
	Parameters
	----------
	None
	
	Returns
	-------
	None
	
	"""
	
	parser = argparse.ArgumentParser(description = 'Freezer Monitoring Script')
	parser.add_argument('-V', '--version', action='version', version=__version__)
	parser.parse_args()

	PIN = 11
	gpio_setup(PIN)
	monitor(PIN)

if __name__ == '__main__':
	main()
