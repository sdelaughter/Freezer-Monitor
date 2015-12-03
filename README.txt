#Freezer-Monitor
Enables the use of a Raspberry Pi to monitor scientific laboratory freezers

Created by Samuel DeLaughter
For the department of Chemistry and the Department of Biochemistry & Molecular Biology
At the University of Massachusetts Amherst


This script is designed to run as a daemon process on a Raspberry Pi to monitor the status of laboratory freezers.
It aims to provide a low-cost, fully open source alternative to commercial monitoring modules.

In the event of a status change in the freezer, it will send an alert message to an email address designated in a freezer_info.csv.  This allows contact information to be changed in a single location rather than modifying the script on individual monitoring devices.  Make sure to update freezer_info.csv with your actual contact information before deploying.

In the event that the CSV file is unreadable or the designated email is unreachable, an alert will be sent to a backup email address which is set near the top of the script.  Make sure to modify this value before deploying as well.

By default, the script watches GPIO pin #11 (using board-numbering for a Raspberry Pi model B+)

Circuit-Diagram.jpg illustrates how to physically connect the Raspberry Pi to the freezer.  You may need to experiment with different resistors in the 1kΩ - 10kΩ range for the +3.3v pin in order to tune the device to suit your freezer's monitoring contact.


BEFORE DEPLOYING
----------------
Make sure to set your own values for CSV_PATH, CSV_ERROR_ADDRESSES, and SMTP_SERVER near the top of freezer_monitor.py
