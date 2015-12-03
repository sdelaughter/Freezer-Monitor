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
1. Set your own values for CSV_PATH, CSV_ERROR_ADDRESSES, and SMTP_SERVER near the top of freezer_monitor.py
    - CSV_ERROR_ADDRESSES['to'] should be formatted as a list, even for a single address
2. Modify freezer_info.csv with accurate information for each of your monitoring devices (one device per row)
    - The Pi's IP address is used as the key to lookup other values in the CSV file, so make sure all your Pis have fixed IP addresses
    - The first row of the CSV file must contain at least the following six column headers (in any order, but formatted identically):
        IP,Location,Email,Backup Email,Reply-To Email,From Email
    - If two or more email addresses are required for a single freezer's primary or backup contact email, they should be surrounded by double quotes and separated by a comma and a space as follows:
        "it@example.edu, jschmoe@example.edu"
3. If desired, the alert message's content can be modified in freezer_monitor.send_mail()
