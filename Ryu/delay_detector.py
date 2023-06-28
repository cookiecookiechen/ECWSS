# -*- coding:utf-8 -*-

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.base.app_manager import lookup_service_brick
from ryu.lib import hub
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller import ofp_event
from ryu.topology.switches import Switches
from ryu.topology.switches import LLDPPacket
import time
import setting
import numpy as np


class DelayDetector(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DelayDetector, self).__init__(*args, **kwargs)
        self.name = "DelayDetector"
        self.sending_echo_request_interval = 0.05

        self.topology_awareness = lookup_service_brick("TopologyAwareness")
        self.sw_module = lookup_service_brick('switches')

        self.detect_num = 0
        self.history_delay_dic = {}
        self.datapaths = {}
        self.echo_latency = {}
        self.discover_thread = hub.spawn(self._discover)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('Register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('Unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _discover(self):
        """
            Delay detecting functon.
            Send echo request and calculate link delay periodically
        """
        # hub.sleep(1)
        while True:
            self._send_echo_request()
            self.create_link_delay()

            if self.detect_num == 0:
                print("------ delay information refresh !!! + time_now:", time.time())

            self.show_delay_statis()
            time.sleep(setting.DELAY_DETECTING_PERIOD)

    def _send_echo_request(self):
        """
            Seng echo request msg to datapath.
        """
        for datapath in list(self.datapaths.values()):
            parser = datapath.ofproto_parser
            echo_req = parser.OFPEchoRequest(datapath,
                                             data="%.12f" % time.time())
            datapath.send_msg(echo_req)
            # Important! Don't send echo request together, Because it will
            # generate a lot of echo reply almost in the same time.
            # which will generate a lot of delay of waiting in queue
            # when processing echo reply in echo_reply_handler.

            hub.sleep(self.sending_echo_request_interval)

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def echo_reply_handler(self, ev):
        """
            Handle the echo reply msg, and get the latency of link.
        """
        now_timestamp = time.time()
        try:
            latency = now_timestamp - eval(ev.msg.data)
            self.echo_latency[ev.msg.datapath.id] = latency
        except:
            return

    def create_link_delay(self):
        """
            Create link delay data, and save it into graph object.
        """
        self.detect_num = self.detect_num + 1
        try:
            for src in self.topology_awareness.graph:
                for dst in self.topology_awareness.graph[src]:
                    if src == dst:
                        self.topology_awareness.graph[src][dst]['delay'] = 0
                        continue
                    delay_now = self.get_delay(src, dst)

                    if src not in self.history_delay_dic:
                        self.history_delay_dic.setdefault(src, {})
                    if dst not in self.history_delay_dic[src]:
                        self.history_delay_dic[src].setdefault(dst, [])
                    self.history_delay_dic[src][dst].append(delay_now)

                    # if src == 1 and dst == 2:
                    #     print "history_delay_dic[1][2]", self.history_delay_dic[1][2]

                    if self.detect_num % 3 == 0:
                        delay = np.mean(self.history_delay_dic[src][dst])

                        # if src == 1 and dst == 2:
                        #     print "median_delay_dic[1][2]", delay

                        self.topology_awareness.graph[src][dst]['delay'] = delay
                        self.history_delay_dic[src][dst] = []
            if self.detect_num == 3:
                self.detect_num = 0

        except:
            if self.topology_awareness is None:
                self.topology_awareness = lookup_service_brick('TopologyAwareness')
            return

    def get_delay(self, src, dst):
        """
            Get link delay.
                        Controller
                        |        |
        src echo latency|        |dst echo latency
                        |        |
                   SwitchA-------SwitchB

                    fwd_delay--->
                        <----reply_delay
            delay = (forward delay + reply delay - src datapath's echo latency
        """
        try:
            fwd_delay = self.topology_awareness.graph[src][dst]['lldpdelay']
            re_delay = self.topology_awareness.graph[dst][src]['lldpdelay']
            src_latency = self.echo_latency[src]
            dst_latency = self.echo_latency[dst]

            delay = (fwd_delay + re_delay - src_latency - dst_latency) / 2
            return max(delay, 0)
        except:
            return float('inf')

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
            Parsing LLDP packet and get the delay of link.
        """
        recv_timestamp = time.time()
        msg = ev.msg
        try:
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
        except LLDPPacket.LLDPUnknownFormat as e:
            # This handler can receive all the packtes which can be
            # not-LLDP packet. Ignore it silently
            return

        dpid = msg.datapath.id
        # only support ofproto_v1_3.OFP_VERSION
        dst_port_no = msg.match['in_port']

        # get the lldp delay, and save it into port_data.
        if self.sw_module is None:
            self.sw_module = lookup_service_brick('switches')

        for port in list(self.sw_module.ports.keys()):
            if src_dpid == port.dpid and src_port_no == port.port_no:
                send_timestamp = self.sw_module.ports[port].timestamp
                if send_timestamp:
                    delay = recv_timestamp - send_timestamp
                    self._save_lldp_delay(src=src_dpid, dst=dpid,
                                          lldpdelay=delay)

    def _save_lldp_delay(self, src=0, dst=0, lldpdelay=0):
        try:
            self.topology_awareness.graph[src][dst]['lldpdelay'] = lldpdelay
        except:
            if self.topology_awareness is None:
                self.topology_awareness = lookup_service_brick('TopologyAwareness')
            return

    def show_delay_statis(self):
        if setting.TOSHOW and self.topology_awareness is not None:
            self.logger.info("\nsrc   dst      delay")
            self.logger.info("---------------------------")
            for src in self.topology_awareness.graph:
                for dst in self.topology_awareness.graph[src]:
                    delay = self.topology_awareness.graph[src][dst]['delay']
                    self.logger.info("%s<-->%s : %s" % (src, dst, delay))
                    print("src,dst,delay:",src,dst,delay)

