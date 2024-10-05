Palioxis - Linux "kill-switch" utility aka the 2024 "DELETE MY BROWSER HISTORY WHEN I DIE"
========
Palioxis was the Greek personification of the backrush or retreat from battle,and this little thing salts the earth behind you.
It seems fitting in the scenarios that would surround the needed use of this script.

For use by freedom fighters as needed for self-preservation,or yknow if you wanna delete your collection of stolen federal document.

100% to be operated drunk or high. 
You might lose data and stuff but itll be funny.

2024 Updates:
Targets dirs now defined in targets.txt with improved error handling and shit for now
Added option to install itself as a systemd
Suggest arguments based upon the mode if run with no args
no args also has option to add a new path/file to self destruction:
<br>Do you want to run as (1) server, (2) client, or (3) add a new directory to targets.txt? (Enter 1, 2, or 3): <br>

Running in 'Server' mode:<br>
usage: ./palioxis.py --mode server --host 127.0.0.1 --port 44524 --key OHSNAP<br>
This will start Palioxis as a server, meaning it will listen on
the given host and port for the 'destroy key'. Once received, it
will proceed to shred the specified files and truecrypt drives.
Once the server starts, it will run in the background as a daemon
process until you either reboot or kill the process.
**It's good idea to run the Palioxis server as system service**<br><br>

Running in 'Client' mode:<br>
usage: ./palioxis.py --mode client --list /etc/palioxis/nodes.txt<br>
This will start Palioxis as the master client. It will read server hosts
from the file specified with the --list argument and attempt to send the 
kill signal to each of these hosts. <br><br>
 
Example server list file:<br>
192.168.56.102 44524 OHSNAP
192.168.56.104 44524 FREEDOM
192.168.56.105 44524 L33T

