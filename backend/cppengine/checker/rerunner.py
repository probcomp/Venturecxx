
# Expected location: /home/ec2-user/for_IME/

# Add (without comments) to /etc/rc.local and also run once:
# sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
# sudo iptables -t nat -A PREROUTING -p tcp --dport 81 -j REDIRECT --to-port 5300

import flask
from checker_functions import *

rerunner_server = flask.Flask(__name__)

@rerunner_server.route('/', methods=['GET'])
def just():
  return flask.make_response("Local port: " + str(PORT))

@rerunner_server.route('/restart_venture_server', methods=['GET'])
def restart_venture_server():
  RestartVentureServer('by_http_request')
  return flask.make_response("The Venture server has been restarted. <a href='http://www.yuraperov.com/MIT.PCP/demo.html'>Return to the list of demos</a>.")
                                  
rerunner_server.run(port=5300, host='0.0.0.0')
