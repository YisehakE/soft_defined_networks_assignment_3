'''
Please add your name:
Please add your matric number: 
'''

import sys
import os
#Sfrom sets import Set

from pox.core import core

import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import pox.openflow.spanning_forest

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

import pox.lib.packet as packet

log = core.getLogger()


'''
TODO(s) to account for

  TODO #1 - Figure out how to get firewalls to controller (maybe as argument?)
  TODO #2 - Find the function to parse packet using POX 

Questions (MOVED TO GOOGLE DOC)
  #1 - 
  #2 - 
  #3 - 

'''

# Constants for task 2 and task 3: firewall policies, premium classes

# ==== PRIORITY ==== #
PRIORITY_FW = 80 # Higher has more priority
PRIORITY_QUE = 40

# ==== QUEUES ====
QUEUE_SWITCH = 0
QUEUE_PREM = 1 
QUEUE_REG = 2


class ControllerPolicy():
  def __init__(self):
      self.FIREWALL_POLICIES = [] # Type: List [ Map<str, str> ]
      self.PREMIUM_HOSTS = set()
      self.parse()

  def get_policy_content(self, contents):
    n_rules = int(contents[0])
    m_hosts = int(contents[1])
    rules = contents[2:2 + n_rules]
    hosts = contents[2 + n_rules:]

    log.debug("\n\n # of Premium Hosts: ", m_hosts)
    log.debug("\n Listed Premium Hosts: ", hosts)

    return n_rules, m_hosts, rules, hosts
  

  def parse_fw_policies(self, n_rules, rules):
      
      for i in range(n_rules):    
        rule_info = rules[i].split(',')
        policy = {}
        if len(rule_info) == 2: # Type 1: IP, Port: Deny TCP traffic sent to a certain host on a specified port
            policy["dst_ip"], policy["dst_port"] = rule_info[0], rule_info[1]
        elif len(rule_info) == 3: # Type 2: Deny TCP traffic coming from H1 to H2 on specified port 
            policy["src_ip"], policy["dst_ip"], policy["dst_port"] = rule_info[0], rule_info[1], rule_info[2]
        else:
            log.info("\n >>>>>>>>>>>>>>>>>ERROR: cannot parse firewall rules")
            
        self.FIREWALL_POLICIES.append(policy)
      
  def parse_premium_hosts(self, m_hosts, hosts):
      
      if m_hosts <= 0:
        log.info("\n >>>>>>>>>>>>>>>>>There are no hosts that will receive premium treatment: ")

      for i in range(m_hosts):
          self.PREMIUM_HOSTS.add(hosts[i])
    
  def parse(self):
      
      policy_f = open("policy.in", "r")
      policy_contents = policy_f.read().split()
      n_rules, m_hosts, rules, hosts = self.get_policy_content(policy_contents)
      log.info(policy_contents)

      self.get_policy_content(policy_contents)

      # Parse Firewall
      self.parse_fw_policies(n_rules, rules)
      
      # Parse Premium
      self.parse_premium_hosts(m_hosts, hosts)


POLICIES_OBJ = ControllerPolicy() 

class Controller(EventMixin):
  
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        self.switch_mac_to_port_map = {} # Table to record origins
   
        self.TTL = 30

        log.debug("System arguments %s" % (str(sys.argv)))
   
    
    # You can write other functions as you need.
    ######################################################################################  
    def is_packet_IP(self, packet):
      ip = packet.find('ipv4')

      if ip is None:  return False

      print("Source IP: ", ip.srcip)
      return True

    ######################################################################################
        
    def _handle_PacketIn (self, event):    
      log.debug("\n >>>>>>>>>>>>>>>>>> INCOMING PACKET \n")

      pkt, pkt_in = event.parsed, event.ofp # Parsed packet data | The actual packet
      src_mac, dst_mac = pkt.src, pkt.dst # Mac source address  | Mac destination address
      src_port, dpid = event.port, dpid_to_str(event.dpid)

      log.debug("Packet content:\n  dpid: %s,\n  src: %s,\n   dst: %s,\n   port: %s" % (dpid, src_mac, dst_mac, src_port))

      # install entries to the route table
      def install_enqueue(event, packet, outport, q_id): 

        # Initialize/create message using flow modification table 
        # (Ref. OpenFlow in POX -> OpenFlow Messages -> ofp_flow_mod ) https://noxrepo.github.io/pox-doc/html/#ofp-flow-mod-flow-table-modification)
        msg = of.ofp_flow_mod()
        msg.priority = PRIORITY_QUE

        # Set the match structure to given packet with the input port obtained from the raised event
        # (Ref. OpenFlow in POX -> Match Structure -> ofp_match methods) https://noxrepo.github.io/pox-doc/html/#ofp-match-methods)
        msg.match = of.ofp_match.from_packet(packet, src_port)
        
        # Addition message attributes (optional)
        msg.data = pkt_in
        msg.idle_timeout = msg.hard_timeout = self.TTL

        # Create action for enqueuing actions in flow table
        # (Ref. OpenFlow in POX -> Match Structure -> ofp_match methods) https://noxrepo.github.io/pox-doc/html/#ofp-match-methods)
        enqueue_action = of.ofo_action_enqueue(port = outport, 
                                                queue_id=q_id)
        msg.actions.append(enqueue_action)
        
        # Send this message from this switch to the controller 
        event.connection.send(msg)

        log.debug("S%s: Output data to port %s at queue %d", str(dpid), str(dst_port), qid)

  

    	# Check the packet and decide how to route the packet
      def forward(message = None):
        log.debug("Message content [FORWARD]", message)

        if not self.switch_mac_to_port_map.get(dpid):
          log.debug("(Adding entry into table)S%s:\n  Mac entry %s\n  @Port %s\n: ", 
                                                            str(dpid), str(src_mac), 
                                                            str(src_port)) 
          self.table[dpid][src_mac] = src_port  

        if self.switch_mac_to_port_map.get(dst_mac):
          dst_port = self.table[dpid][dst_mac]
          log.info("Found dst port at: " + str(dst_port))
          qid = getQid() # Part 5 here, get queue location
          install_enqueue(dst_port, qid)
        else:
           flood()


      # When it knows nothing about the destination, flood but don't install the rule
      def flood (message = None):
        print("Message content [FLOOD]: ", message)
        log.debug("Message content [FLOOD]", message)

        # define your message here
        msg = of.ofp_packet_out()
        msg.data = pkt_in
        msg.in_port = src_port
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        event.connection.send(msg)
        log.debug("(FLOODING)S%s: Message sent - Outport %s\n: ", str(dpid), str(of.OFPP_FLOOD)) 
      
      def getQid():
          q_id = QUEUE_REG
          src_ip = "" 

          if pkt.type == packet.IP_TYPE: src_ip = pkt.payload.srcip
          elif pkt.type == packet.ARP_TYPE: src_ip = pkt.payload.protosrc
          
          log.debug("CURRENT PREMIUM HOST SET: ", (POLICIES_OBJ.PREMIUM_HOSTS))
          if str(src_ip) in POLICIES_OBJ.PREMIUM_HOSTS:
              log.debug("Premium host set contains src_ip: " + str(src_ip) + "\n")
              q_id = QUEUE_PREM
  
          queue_str = ""

          if q_id == 0: queue_str = "Standard queue"
          elif q_id == 1: queue_str = "Premium queue"
          elif q_id == 2: queue_str = "Regular queue"

          log.debug("(QUEUE %d [i.e %s] set for host at IP %s)" % (q_id, queue_str, src_ip))
          return q_id

      forward()
      log.debug("\n\n >>>>>>>>>>>>>>>>>> PACKET ROUTED \n\n")  

    def _handle_PortStatus(self, event):
      log.debug(">>>>>>>>>>>>>>> UPDATE PORT OCCURENCE ===")

      if event.added: action = "Included"
      elif event.deleted: action = "Removed"
      else: 
         action = "Updated"
      
      log.debug("Port %s on Switch %s has been %s." % (event.port, event.dpid, action))	

      self.reset_table()
      log.debug("\n >>>>>>>>>>>>>>>>>> TABLE CLEARED \n")  


    def reset_table(self):
      log.debug("Dropped controller's switch-mac-to-port map")

      new_map = {}
      for key in self.switch_mac_to_port_map:
          new_map[key] = {}

      self.switch_mac_to_port_map = new_map

    def _handle_ConnectionUp(self, event):

      # Extract DPID to post as log notifying that switch is online
      dpid = dpid_to_str(event.dpid)
      log.debug("Switch %s has come up.", dpid)
      
      self.switch_mac_to_port_map[dpid] = {} # Use DPID to 


      # Send the firewall policies to the switch
      def sendFirewallPolicy(connection, policy):
        
          # define your message here
          src_ip, dst_ip, dst_port = "", IPAddr(policy.get("dst_ip")), int(policy.get("dst_port"))
          
          block = of.ofp_match(dl_type = 0x0800, 
                               nw_proto = 6,
                               tp_dst = int(dst_port),
                               nw_dst = IPAddr(dst_ip)
                               )
          if "src_ip" in policy:
              src_ip = IPAddr(policy.get("src_ip"))
              block.nw_src = src_ip # IP Source Address


          flood_act = of.ofp_action_output(port=of.OFPP_NONE)

          msg = of.flow_mod(
              match = block,
              priority = PRIORITY_FW,
              actions = [flood_act],

          )
          connection.send(msg)
          log.debug("\n Switch %s: \n  (Firewall rule): \n    - src: %s,\n    dest: %s,\n     dest_port: %s", dpid, src_ip, dst_ip, dst_port) 
          
      log.debug("\n CONNECTION >>>>>>> Firewall processing\n")
      for policy in POLICIES_OBJ.FIREWALL_POLICIES:
        sendFirewallPolicy(event.connection, policy)
      log.debug("\n\n >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

      log.debug("\n CONNECTION >>>>>>> Premium policy showcase\n")
      for policy in POLICIES_OBJ.PREMIUM_HOSTS:
        log.debug("Installing Premium for host at %s" % (policy))

      log.debug("\n\n >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            

def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
