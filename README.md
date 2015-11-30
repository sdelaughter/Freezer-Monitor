#Freezer-Monitor
Enables the use of a Raspberry Pi to monitor scientific laboratory freezers

Created by Samuel DeLaughter
For the department of Chemistry and the Department of Biochemistry & Molecular Biology
At the University of Massachusetts Amherst


This script is designed to run as a daemon process on a Raspberry Pi to monitor the status of laboratory freezers.
It aims to provide a low-cost, fully open source alternative to commercial monitoring modules.

In the event of a status change in the freezer, it will send an alert message to an email address designated in a CSV file.
It will also send an alert to a hard-coded backup address in the event that the CSV file is unreadable or the designated email is unreachable.
