
# Expected location: /home/ec2-user/for_IME/

HOST = "127.0.0.1"
PORT = 8080
ADDRESSEE = "probcomp-sys@lists.csail.mit.edu"
ADDRESSEE_RESERVE = "yura.perov@gmail.com"
MAX_TIMEOUT_IN_SECONDS = 1
FILE_TO_SAVE_LAST_RESTART_TIMESTAMP = "/home/ec2-user/for_IME/last_restart.txt"
PATH_TO_VENTURE_BINARY = "/usr/venture/for_demos/venture"

import subprocess
import time
import datetime

# Should return the "timeout" error:
# p = subprocess.Popen("curl --head -m 5 http://ec2-107-20-123-38.compute-1.amazonaws.com:81/ 2>&1",
#                      shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# out, err = p.communicate()

def StopVentureServer():
  subprocess.Popen('pkill -9 -f "' + PATH_TO_VENTURE_BINARY + ' ' + str(PORT) + '"', shell=True).wait()

def RestartVentureServer(comment):
  f = open(FILE_TO_SAVE_LAST_RESTART_TIMESTAMP, "r")
  last_timestamp = float(f.next())
  f.close()
  f = open(FILE_TO_SAVE_LAST_RESTART_TIMESTAMP, "w")
  f.write(str(time.time()))
  f.close()
  UPTIME = int(time.time() - last_timestamp)
  UPTIME = str(datetime.timedelta(seconds=UPTIME))
  StopVentureServer()
    
  subprocess.Popen(PATH_TO_VENTURE_BINARY + " " + str(PORT) + " >/dev/null 2>&1 &", shell=True)
  if comment == 'by_http_request':
    reason = 'The Venture server backing the IME was terminated manually.'
  elif "(28) connect() timed out" in comment:
    reason = 'The Venture server backing the IME is not responding to a report_directives request within ' + str(MAX_TIMEOUT_IN_SECONDS) + ' seconds.'
  elif "(7) couldn't connect to host" in comment:
    reason = 'It seems the Venture server backing the IME is not running.'
  else:
    reason = 'The Venture server backing the IME is responding with an error (not 200 status response) to a report_directives request (or another error).'
  print("Error: " + reason)
  subprocess.Popen('echo -e "' +
                   'To: ' + ADDRESSEE + '\n' +
                   'From: ' + ADDRESSEE + '\n' +
                   'Subject: [venture-maintain] WARNING: Restarting the main Venture server due to non-response (uptime = ' + UPTIME + ')\n' +
                   reason + '\n\n' +
                   'As a result it has been automatically restarted.\n\nGenerated: ' + str(datetime.datetime.now()) + '\n' +
                   '" | /usr/sbin/sendmail -f ' + ADDRESSEE + ' ' + ADDRESSEE, shell=True).wait()
  if ADDRESSEE_RESERVE != '':
    subprocess.Popen('echo -e "' +
                     'To: ' + ADDRESSEE_RESERVE + '\n' +
                     'From: ' + ADDRESSEE_RESERVE + '\n' +
                     'Subject: [venture-maintain] WARNING: Restarting the main Venture server due to non-response (uptime = ' + UPTIME + ')\n' +
                     reason + '\n\n' +
                     'As a result it has been automatically restarted.\n\nGenerated: ' + str(datetime.datetime.now()) + '\n' +
                     '" | /usr/sbin/sendmail -f ' + ADDRESSEE_RESERVE + ' ' + ADDRESSEE_RESERVE, shell=True).wait()

def CheckVentureServer():
  p = subprocess.Popen("curl --head -m " + str(MAX_TIMEOUT_IN_SECONDS) + " http://" + HOST + ":" + str(PORT) + "/ 2>&1",
                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  server_answer = out

  if "200 OK" in server_answer:
    print("The Venture server backing the IME is being run, it seems.")
  else:
    RestartVentureServer(server_answer)
