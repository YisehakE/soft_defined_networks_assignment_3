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

import pox.lib.packet as pkt

log = core.getLogger()


'''
TODO(s) to account for

  TODO #1 - Figure out how to get firewalls to controller (maybe as argument?)
  TODO #2 - Find the function to parse packet using POX 
  TODO #3 - 

Questions (MOVED TO GOOGLE DOC)
  #1 - 
  #2 - 
  #3 - 


'''
class Controller(EventMixin):
    
    # def getPolicyContent(self, contents):
    #   n_rules = int(contents[0])
    #   m_hosts = int(contents[1])
    #   rules = contents[2:2 + n_rules]
    #   hosts = contents[2 + n_rules:]

    #   return n_rules, m_hosts, rules, hosts

    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)


        self.FIREWALL_POLICIES = [] # MY TODO: Figure out how to actualize this into the class for event handler for connection
        

    
    # You can write other functions as you need.
    ######################################################################################  
    def getPolicyContent(self, contents):
      n_rules = int(contents[0])
      m_hosts = int(contents[1])
      rules = contents[2:2 + n_rules]
      hosts = contents[2 + n_rules:]

      return n_rules, m_hosts, rules, hosts
    

    def is_packet_IP(self, packet):
      ip = packet.find('ipv4')

      if ip is None:  # This packet isn't IP!
        return False
      else:
        print("Source IP: ", ip.srcip)
        return True


      
    ######################################################################################
        
    def _handle_PacketIn (self, event):    
        
    	# install entries to the route table
        def install_enqueue(event, packet, outport, q_id): 

          # TODO 3 - Attach a reference mark to the documentation where commands were found

          # Initialize/create message using flow modification table 
          # (Ref. OpenFlow in POX -> OpenFlow Messages -> ofp_flow_mod ) https://noxrepo.github.io/pox-doc/html/#ofp-flow-mod-flow-table-modification)
          msg = of.ofp_flow_mod()

          # Set the match structure to given packet with the input port obtained from the raised event
          # (Ref. OpenFlow in POX -> Match Structure -> ofp_match methods) https://noxrepo.github.io/pox-doc/html/#ofp-match-methods)
          msg.match = of.ofp_match.from_packet(packet, event.port)


          # Create action for enqueuing actions in flow table
          # (Ref. OpenFlow in POX -> Match Structure -> ofp_match methods) https://noxrepo.github.io/pox-doc/html/#ofp-match-methods)
          enqueue_action = of.ofo_action_enqueue(port = outport, 
                                                 queue_id=q_id)
          msg.actions.append(enqueue_action)
          

          # Send this message from this switch to the controller 
          event.connection.send(msg)
          

    	# Check the packet and decide how to route the packet
        def forward(message = None):
          print("Message content[FORWARD]: ", message)
          log.debug("Message content [FORWARD]", message)

          pkt = event.parsed # TODO 2 - Find the function to parse packet using POX 

          # Check what protocol the packet is
          if self.is_packet_IP(pkt):
            # TODO: figure out how 

            # Check to see if packet falls under any of the firewall policies 
            src_addr = pkt.srcip
            dst_addr = pkt.dstip


            if (dst_addr, PORT) in self.FIREWALL_POLICIES: # 1st type of firewall 
               pass
            elif (src_addr, dst_addr, PORT) in self.FIREWALL_POLICIES: # 2nd type of firewall
               pass
            else:
            
              # TODO: see what & how to send this message OR packet if it's safe from firewall restrictions
              # Send this message from this switch to the controller 
              event.connection.send(message)
            
          else:
                # TODO: figure out if 1) this would ever be the case and 2) what to do if pkt is NOT IP
             pass
              
          
          
          # # TODO: see what format the message would come in 
          # # TODO: see if checking message is necessary
          # if message:
          #   print("Message content: ", message)

          #   #TODO: extract values from message
          # else:
          #   print("No message!")


          event.connection.send(msg)

            


        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
          print("Message content [FLOOD]: ", message)
          log.debug("Message content [FORWARD]", message)

          # define your message here
          msg = of.ofp_flow_mod()

          if not message.match.dl or (not message.match.nw_dst and not message.match.tp_dst):
            # Case 1: Nothing is known about the destination from the message match structure
            # Essentially, somewhat like ff:ff:ff:ff:ff or 255.255.255.0 as the broadcast address in ARP or DHCP
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
  
          else:
             # Case 2: Message destination is known from match structure 
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            pkt = event.parsed
            install_enqueue(event, pkt, event.)
        

          # ofp_action_output: forwarding packets out of a physical or virtual port
          # OFPP_FLOOD: output all openflow ports expect the input port and those with flooding disabled via the OFPPC_NO_FLOOD port config bit

          # Essentially, somewhat like ff:ff:ff:ff:ff or 255.255.255.0 as the broadcast address in ARP or DHCP
          msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        



        forward(event.ofp)




    def _handle_ConnectionUp(self, event):

      # Extract DPID to post as log notifying that switch is online
      dpid = dpid_to_str(event.dpid)
      log.debug("Switch %s has come up.", dpid)
      

      # TODO #1 - Figure out how to get firewalls to controller (maybe as argument?)
      policy_f = open(sys.argv[3],"r")
      policy_contents = policy_f.read().split()
      n_rules, m_hosts, rules, hosts = self.getPolicyContent(policy_contents)


      print("N =  ", n_rules)
      print("M =  ", m_hosts)
      print("rules: ", str(rules))
      print("hosts: ", str(hosts))

      # Send the firewall policies to the switch
      def sendFirewallPolicy(connection, policy):
          # define your message here

          msg = of.flood_mod()

          msg
          
          # OFPP_NONE: outputting to nowhere
          # msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))
          
          pass



      for policy in self.FIREWALL_POLICIES:
        sendFirewallPolicy(event.connection, policy)

      event.connection.send(msg)
            

def launch():
    # Run discovery and spanning tree modules
    pox.openflow.discovery.launch()
    pox.openflow.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
