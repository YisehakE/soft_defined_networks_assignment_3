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
        linksInfo = contents[3:]
        return hosts, switch, links, linksInfo
    
	  # You can write other functions as you need.

    # Add hosts
      # > self.addHost('h%d' % [HOST NUMBER])
        
    # Add switches
      # > sconfig = {'dpid': "%016x" % [SWITCH NUMBER]}
      # > self.addSwitch('s%d' % [SWITCH NUMBER], **sconfig)

    # Add links
      # > self.addLink([HOST1], [HOST2])
      
    def getPolicyContent(self, contents):
      n_rules = int(contents[0])
      m_hosts = int(contents[1])
      rules = contents[2:2 + n_rules]
      hosts = contents[2 + n_rules:]

      return n_rules, m_hosts, rules, hosts


    def build(self):
      # Read file contents
      topo_f = open(sys.argv[1],"r")
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
        self.addLink(host, switch, bw=bandwidth) # TODO #1


      ################################################
        
      policy_f = open(sys.argv[3],"r")
      policy_contents = policy_f.read().split()
      n_rules, m_hosts, rules, hosts = self.getPolicyContent(policy_contents)


      print("N =  ", n_rules)
      print("M =  ", m_hosts)
      print("rules: ", str(rules))
      print("hosts: ", str(hosts))


      

def startNetwork():
    info('** Creating the tree network\n')
    topo = TreeTopo()
    controllerIP = sys.argv[2]

    global net
    net = Mininet(topo=topo, 
                  link = TCLink, 
                  controller=lambda name: RemoteController(name, ip=controllerIP), 
                  listenPort=6633, 
                  autoSetMacs=True)

    info('** Starting the network\n')
    net.start()

    print("Dumping host connections")
    dumpNodeConnections( net.hosts )

    print("Testing network connectivity")
    net.pingAll()

    # Create QoS Queues
    os.system('sudo ovs-vsctl -- set Port [INTERFACE] qos=@newqos \
               -- --id=@newqos create QoS type=linux-htb other-config:max-rate=[LINK SPEED] queues=0=@q0,1=@q1,2=@q2 \
               -- --id=@q0 create queue other-config:max-rate=[LINK SPEED] other-config:min-rate=[LINK SPEED] \
               -- --id=@q1 create queue other-config:min-rate=[X] \
               -- --id=@q2 create queue other-config:max-rate=[Y]')
    

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




	
	# # You can write other functions as you need.

	# # Add hosts
  #   # > self.addHost('h%d' % [HOST NUMBER])

	# # Add switches
  #   def build_switch(self, switches):
  #     # Add switch
  #     for x in range(1, int(switches) + 1):
  #       sconfig = {'dpid': "%016x" % x}
  #       self.addSwitch('s%d' % x, **sconfig)
  #     # > sconfig = {'dpid': "%016x" % [SWITCH NUMBER]}
  #     # > self.addSwitch('s%d' % [SWITCH NUMBER], **sconfig)

	# # Add links
        
  #   def build_link(self,)
	# # > self.addLink([HOST1], [HOST2])