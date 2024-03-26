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

log = core.getLogger()

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        self.FIREWALL_POLICIES = [] # MY TODO: Figure out how to actualize this into the class for event handler for connection
        
    # You can write other functions as you need.
        
        
    def _handle_PacketIn (self, event):    
        
    	# install entries to the route table
        def install_enqueue(event, packet, outport, q_id): 
          msg = of.ofp_flow_mod()

          parsed_pkt = packet.parsed 

          of.ofo_action_enqueue(outport = outport, 
                                queue_id=q_id)
          

    	# Check the packet and decide how to route the packet
        def forward(message = None):
          print("Message content[FORWARD]: ", message)
          log.debug("Message content [FORWARD]", message)

          if message:
            print("Message content: ", message)

            #TODO: extract values from message
          else:
            print("No message!")
            


        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
          print("Message content [FLOOD]: ", message)
          log.debug("Message content [FORWARD]", message)


          # define your message here
          msg = of.ofp_flow_mod()

          # ofp_action_output: forwarding packets out of a physical or virtual port
          # OFPP_FLOOD: output all openflow ports expect the input port and those with flooding disabled via the OFPPC_NO_FLOOD port config bit

          # Essentially, somewhat like ff:ff:ff:ff:ff or 255.255.255.0 as the broadcast address in ARP or DHCP
          msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))


        
        forward()




    def _handle_ConnectionUp(self, event):

      # Extract DPID to post as log notifying that switch is online
      dpid = dpid_to_str(event.dpid)
      log.debug("Switch %s has come up.", dpid)
      
      # Send the firewall policies to the switch
      def sendFirewallPolicy(connection, policy):
          # define your message here
          
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
