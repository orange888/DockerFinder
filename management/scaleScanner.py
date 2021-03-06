import requests
import time
import subprocess
import math
#from subprocess import Popen, PIPE
from docopt import docopt
__doc__= """ScaleScanner.

Usage:
  ScaleScanner.py run [--monitor-interval=<10>] [--max-scanners=<20>]  [--swarm-mode]
  ScaleScanner.py (-h | --help)
  ScaleScanner.py --version

Options:
  -h --help             Show this screen.
  --monitor-interval=interval   Interval time in seconds between two monitor invocation [default:10]
  --max-scanners=MAX-SCANNERS  Max number of scanners to scale [default:20]
  --swarm-mode          If True scale the swarm node, otherwise docker compose sclae [default:False]
  --version             Show version.
"""
class ScaleScanner:

    def __init__(self, monitor_interval, max_scanners, swarm):
        self.monitor_interval = monitor_interval
        self._swarm_mode = swarm
        self.max_scanners = max_scanners

        # TODO; change from rabbitmq to monitor service
        self._rabbitUrl = "http://0.0.0.0:3002/service/rabbitmq/queue/images"

    def run_loop(self, service):
        while(True):
            # count the message in the queue
            res = requests.get(self._rabbitUrl)

            if res.status_code == requests.codes.ok:
                json_response = res.json()
                #print(json_response)
                if(not json_response['err']):
                    count_msg=json_response['load']
                    print(str(count_msg)+  ": msgs in the queue")
                    scale = self.calc_scale(count_msg)
                    # scale = 1
                    # if count_msg < 100:
                    #     scale = 5
                    # elif count_msg < 500:
                    #     scale = 10
                    # elif count_msg < 1000:
                    #     scale = 30
                    # else:
                    #     scale = 40
                    #scale the scanners
                    self.scale_service(service, scale)
                else:
                    print(json_response['msg'])
            time.sleep(self.monitor_interval)
    def calc_scale(self, num_msgs):
        """
        y=1 : 0,01  is the load of the messages tha we want to divide to the scanners

        x:load = y: 100
        x = (load * y) / 100
        """
        y = 1
        return min(self.max_scanners, math.ceil((num_msgs * y) / 100) )


    def scale_service(self, service, scale):
        if(self._swarm_mode):
            self.scale_swarm(service, scale)
        else:
            self.scale_compose(service, scale)


    def scale_compose(self, service_name, scale):

        command = "docker-compose scale "+ service_name+"="+str(scale)
        print("Scaling compose mode :"+ command)
        #r =    subprocess.check_output(["docker-compose scale "+ service_name+"="+str(scale)],
        r = subprocess.call(command, shell=True)
        #r = subprocess.run(["docker-compose scale "+ service_name+"="+str(scale)],
        #"docker-compose", "scale",  service_name+"="+str(scale) ],
        #                shell=True,
        #                stdout=subprocess.PIPE,
        #                stderr=subprocess.PIPE)
        #print(r.stderr.decode("utf-8"))

    def scale_swarm(self, service_name, scale):
        command = "docker service scale "+service_name+"="+str(scale)
        print("Scaling swarm mode: "+ command)
        r = subprocess.call(command, shell=True)
        # r = subprocess.run(["docker", "service", "scale",  service_name+"="+str(scale)],
        #                 shell=True,
        #                 stdout=subprocess.PIPE,
        #                 stderr=subprocess.PIPE)
        #print(r)


if __name__ == '__main__':
    args = docopt(__doc__, version='ScaleScanner 0.0.1')
    #print(args)
   #--monitor-interval=<10>] [--max-scanners=<20>]  [--swarm-mode]
    scaling = ScaleScanner(monitor_interval=int(args['--monitor-interval']),
                            max_scanners=int(args['--max-scanners']),
                            swarm=args['--swarm-mode'],

    )
    if args['run']:
        while True:
            try:
                scaling.run_loop("scanner")
            except Exception as e:
                print (e)
                print("Waiting 10s and restarting.")
                time.sleep(10)
