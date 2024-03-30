'''
Please add your name:
Please add your matric number: 
'''

import os
import sys
import atexit

from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import RemoteController

from mininet.util import irange,dumpNodeConnections

net = None


'''
TODO(s) to account for

  TODO #1 - See if I have to change the self.addLink(SWITCH, HOST, BW) to remove BW portion to account for QoS queues 
  TODO #2 - 

'''

class TreeTopo(Topo):		
    def __init__(self):
		# Initialize topology
      Topo.__init__(self)
    
    def getTopoContent(self, contents):
        hosts = contents[0]
        switch = contents[1]
        links = contents[2]
        links_content = contents[3:]

        self.parsed_link_map = {}
        for info in links_content:
          link = info.split(',')
          node_client = link[0]
          node_switch = link[1]
          bw = link[2]

          if node_client not in self.parsed_link_map:
              self.parsed_link_map[node_client] = {}
          if node_switch not in self.parsed_link_map:
              self.parsed_link_map[node_switch] = {}
          
        
          self.parsed_link_map[node_client][node_switch] = int(bw)
          self.parsed_link_map[node_switch][node_client] = int(bw)

        return hosts, switch, links, links_content
    
	  # HELPER FUNCTIONS: You can write other functions as you need (IN CLASS)
    ######################################################################################


    ######################################################################################


    def build(self):
      file = sys.argv[1] if len(sys.argv) > 1 else 'topology.in'

      # Read file contents
      topo_f = open(file, "r")
      topo_contents = topo_f.read().split()
      host, switch, link, linksInfo = self.getTopoContent(topo_contents)
      
      print("Hosts: " + host)
      print("switch: " + switch)
      print("links: " + link)
      print("linksInfo: " + str(linksInfo))

      # Add switch
      for x in range(1, int(switch) + 1):
        sconfig = {'dpid': "%016x" % x}
        self.addSwitch('s%d' % x, **sconfig)
        
      # Add hosts
      for y in range(1, int(host) + 1):
        ip = '10.0.0.%d/8' % y
        self.addHost('h%d' % y, ip=ip)

      # Add Links
      for x in range(int(link)):
        info = linksInfo[x].split(',')
        host = info[0]
        switch = info[1]
        bandwidth = int(info[2])
        self.addLink(host, switch)


# HELPER FUNCTIONS:You can write other functions as you need (OUTSIDE CLASS)
######################################################################################
def setup_QoS(bw, switch, port):
  # Calculate premium and normal bandwidth based on percentages
  INTERFACE = '{}-eth{}'.format(switch, port) 
  LINK_SPEED = bw * 10**6 # Total available bandwidth in Mbps 

  X = int(0.8 * bw) # Premium class rate (i.e >= 0.8 x bw)
  Y = int(0.5 * bw) # Regular class rate (i.e <= 0.5 x bw)

  # Configure QoS queues using ovs-vsctl
  # Create QoS Queues
  os.system('sudo ovs-vsctl -- set Port {} qos=@newqos \
            -- --id=@newqos create QoS type=linux-htb other-config:max-rate={} queues=0=@q0,1=@q1,2=@q2 \
            -- --id=@q0 create queue other-config:max-rate={}} other-config:min-rate={} \
            -- --id=@q1 create queue other-config:min-rate={} \
            -- --id=@q2 create queue other-config:max-rate={}'.format(INTERFACE,
                                                                       LINK_SPEED,
                                                                       bw,
                                                                       bw,
                                                                       X,
                                                                       Y))

######################################################################################

def allocate_queues(topo):
    for link in topo.links(sort=True, withKeys=False, withInfo=True):
        host, switch, info = link

        print("\n(" + host + "---" + switch + "):")

        port_1 = info['port1']
        port_2 = info['port2']

        node_1 = info['node1']
        node_2 = info['node2']
        bw = topo.parsed_link_map[node_1][node_2]

        print('%s@Port%i is connected with bandwith of %i to %s@Port%i' %(node_1, port_1, bw, node_2, port_2))
        
        setup_QoS(bw, node_1, port_1)
        setup_QoS(bw, node_2, port_2)

######################################################################################


def startNetwork():
    info('** Creating the tree network\n')
    topo = TreeTopo()

    controllerIP = sys.argv[2] if len(sys.argv) > 2 else '0.0.0.0'

    global net
    net = Mininet(topo=topo, 
                  link = TCLink, 
                  controller=lambda name: RemoteController(name, ip=controllerIP), 
                  listenPort=6633, 
                  autoSetMacs=True)

    info('** Starting the network\n')
    net.start()

    # Create QoS Queues
    ################################################
    # os.system('sudo ovs-vsctl -- set Port [INTERFACE] qos=@newqos \
    #            -- --id=@newqos create QoS type=linux-htb other-config:max-rate=[LINK SPEED] queues=0=@q0,1=@q1,2=@q2 \
    #            -- --id=@q0 create queue other-config:max-rate=[LINK SPEED] other-config:min-rate=[LINK SPEED] \
    #            -- --id=@q1 create queue other-config:min-rate=[X] \
    #            -- --id=@q2 create queue other-config:max-rate=[Y]')
    ################################################

    allocate_queues(topo)

    info('** Running CLI\n')
    print()
    CLI(net)

    net.stop()

def stopNetwork():
    if net is not None:
        net.stop()
        # Remove QoS and Queues
        os.system('sudo ovs-vsctl --all destroy Qos')
        os.system('sudo ovs-vsctl --all destroy Queue')



if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)


    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
