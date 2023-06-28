# -*- coding:utf-8 -*-

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
import networkx as nx
import networkx.algorithms.approximation as algrithm_approximation
import copy
#import pandas as pd
import numpy as np
from ryu.lib import hub
import time
import random
import math
import socket
import re
import threading
import concurrent.futures

import topology_awareness
import delay_detector
import bandwidth_detector
import steiner_creator

import setting

class ErasureWrite(app_manager.RyuApp):#ErasureWriteAlgorithm
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        "TopologyAwareness": topology_awareness.TopologyAwareness,
        "DelayDetector": delay_detector.DelayDetector,
        "BandwidthDetector": bandwidth_detector.BandwidthDetector,
        "SteinerCreator": steiner_creator.Steiner_Creator
    }

    def __init__(self, *args, **kwargs):
        super(ErasureWrite, self).__init__(*args, **kwargs)
        self.name = "ErasureWriteAlgorithm"
        self.topology_awareness = kwargs["TopologyAwareness"]
        self.delay_detector = kwargs["DelayDetector"]
        self.bandwidth_detector = kwargs["BandwidthDetector"]
        self.steiner_creator=kwargs["SteinerCreator"]
        self.datapaths = {}
        self.flow_table = {}
        #self.pack_in_history = set()
        self.pack_in_history = []
        
        self.path_delay_history = {}

         
        self.alternative_path_discover_thread = hub.spawn(self._all_path_discover)  # During program initialization, the available paths between all nodes are calculated

        self.CtoP_path_history = []
        self.DtoC_path_history=[]
        self.all_path_history=[]
        self.DtoC_dataVolume=0
        self.CtoP_dataVolume=0
        
        self.DtoC_result=[]
        self.CtoP_result=[]
        
        
        self.temp_num=0
        #self.network_topo=nx.Graph()
        #get args of write
        t1=threading.Thread(target=self.getWriteArg)
        t1.start()
        t2=threading.Thread(target=self.get_multi_writeArgs)
        t2.start()
        t3=threading.Thread(target=self.getTradArg)
        t3.start()


    def get_multi_writeArgs(self):
        ny_graph=nx.Graph()
        '''   test data: 
        topo_list=[[1,3],[1,4],[1,5],[1,9],[1,11],[2,4],[2,5],[2,6],[4,5],[4,6],[4,7],[4,9],[4,11],[5,6],[5,7],[5,8],[5,9],[7,8],[7,9],[8,14],[9,10],[9,13],[12,13],[12,14]] 
        ML_weight_topo_list=[[1,3,105],[1,4,122],[1,5,57],[1,9,137],[1,11,90],[1,20,143],[2,4,126],[2,5,122],[2,6,132],[3,21,162],[3,22,181],[4,5,118],[4,6,168],[4,7,168],[4,9,162],[4,11,156],[5,6,160],[5,7,189],[5,8,99],[5,9,73],[7,8,163],[7,9,160]
    ,[8,14,102],[9,10,26],[9,13,28],[10,14,76],[10,15,154],[10,16,124],[11,19,124],[12,13,134],[12,14,114],[13,17,124],[13,18,124],[14,15,158]]
        FL_weight_topo_list=[[1,3,300],[1,4,300],[1,5,300],[1,9,300],[1,11,300],[1,20,300],[2,4,300],[2,5,300],[2,6,300],[3,21,300],[3,22,300],[4,5,300],[4,6,300],[4,7,300],[4,9,300],[4,11,300],[5,6,300],[5,7,300],[5,8,300],[5,9,300],[7,8,300],[7,9,300]
    ,[8,14,300],[9,10,300],[9,13,300],[10,14,300],[10,15,300],[10,16,300],[11,19,300],[12,13,300],[12,14,300],[13,17,300],[13,18,300],[14,15,300]]
        weight_topo_list=FL_weight_topo_list'''      
        weight_topo_list=self.topology_awareness.graph

        total_bw=0
        for edge in weight_topo_list:
             ny_graph.add_edge(edge[0],edge[1])
             ny_graph[edge[0]][edge[1]]['bandwidth']=edge[2]
             total_bw+=edge[2]
        avg_bw=total_bw/len(weight_topo_list)
        print("avg_bw=",avg_bw)
        for edge in weight_topo_list:
             ny_graph[edge[0]][edge[1]]['true_weight']=float(avg_bw)/float(edge[2])
        #print(ny_graph.edges)
        
        executor=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        
        #multi thread
        address=('127.0.0.1',8888)
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(address)
        parityNodeNum,addr=s.recvfrom(2048)
        print("parityNodeNum test 111111111111111111111",parityNodeNum,addr)
        for i in range(int(parityNodeNum)):
            sendPort=6000+i
            receivePort=7000+i
            threading.Thread(target=self.get_single_writeArg,args=(sendPort,receivePort,ny_graph,executor)).start()
        
        
    
    
    def get_single_writeArg(self,sendPort,receivePort,ny_graph,executor):#get writeArgs of erasureCode
        
        address=('127.0.0.1',receivePort)
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(address)
        
       
        
        while 1:
            cloud=[]
            print("start receive")
            data,addr=s.recvfrom(2048)
            print("receive data 111",data)
            
            data=data.split('+')
            print("convert data",data)
            nodedata=data[0]
            self.dataNodeList=list(map(int,nodedata[1:-1].split(',')))#nodedata=datap[0]='[10,3,4,6]' convert to [10,3,4,6]
            
            cloud.append(int(data[1]))#edge: data[1]='5'
            self.cloud=cloud
            print("ttttttttt",self.dataNodeList,self.cloud)
            #dataV=data[2]
            dataVolum=int(data[2][0:-1])
            tos=int(data[3])
            write_topo=int(data[4])
            name_parameter=data[5]
            
            print("tttttttttttttos tos ",tos)
            
            #graph_now = self.topology_awareness.graph
            cloud=self.cloud
            dataNode=self.dataNodeList
            if self.temp_num==0:
                self.network_topo=self.topology_awareness.graph#get topo
                print("network_topo= ",self.network_topo)
                self.temp_num=1
            print("network_topo= ",self.network_topo.edges)
            print("ttttttttttttttttt write_topo_mode=   ",write_topo)
            
            if write_topo==1:
                MetaData,flow_path=self.steiner_creator.GetDistributStarTopo(dataNode,cloud)
            elif write_topo==2:
                MetaData,flow_path=self.steiner_creator.GetPipelineTopo(dataNode,cloud)
            elif write_topo==3:
                MetaData,flow_path=self.steiner_creator.getSteinerTree_and_NodeRole(dataNode,cloud,ny_graph,3,dataVolum)
            elif write_topo==4:
                
                executor_result=executor.submit(self.steiner_creator.getSteinerTree_and_NodeRole,dataNode,cloud,ny_graph,4,dataVolum)
                #print("executor_result --->>>>>>>>>",executor_result.result())
                MetaData=executor_result.result()[0]
                flow_path=executor_result.result()[1]
            print("MetaData  ",MetaData,"flow_path",flow_path)
            self.install_steiner_Flow(flow_path,tos)
            
            #print("metameta type",type(TreeFunctionNode_MetaData))
            byteDict=bytes('{}'.format(MetaData))
            
            #BsendData=bytes(str(TreeFunctionNode_MetaData))
            
            net_address=('127.0.0.1',sendPort)
            s2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s2.sendto(byteDict,net_address)
            s2.close()
            
            
            
            if int(write_topo)==1:
                fileName_topo="distribute_star"
            elif int(write_topo)==2:
                fileName_topo="pipeline"
            elif int(write_topo)==3:
                fileName_topo="nx_steiner_tree"
            elif int(write_topo)==4:
                fileName_topo="Greedy_steiner_tree"  
                
            fpWrite=open("/home/guet/newSpace/result/WriteTime/"+"flow_use_result_"+fileName_topo+"_"+name_parameter+"_"+str(dataVolum)+"M"+".txt","a+")
            fpWrite.write("write_mode:"+str(write_topo)+" network_comsumption:"+str(len(flow_path))+ " tos: "+str(tos)+" flow: "+str(flow_path)+"\n\n")
            print("result record ok")
            fpWrite.close()
            

        s.close()
        
        
    
    
    
    
    
    def getTradArg(self):
        address=('127.0.0.1',1234)
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(address)
        while 1:
            data,addr=s.recvfrom(2048)
            print("trad_write ---------",str(data))
            self.trad_write_name=str(data)
            fpWrite=open(self.trad_write_name,"a+")#"_"+name_parameter+"_"+str(dataVolum)+"M"+".txt"
            fpWrite.write("\n\n\n")
            fpWrite.close()
        
    def getWriteArg(self):#get writeArgs of erasureCode
        
        address=('127.0.0.1',12345)
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(address)
        
        while 1:
            cloud=[]
            print("start receive")
            data,addr=s.recvfrom(2048)
            print("receive data 111",data)
            
            data=data.split('+')
            print("convert data",data)
            nodedata=data[0]
            self.dataNodeList=list(map(int,nodedata[1:-1].split(',')))#nodedata=datap[0]='[10,3,4,6]' convert to [10,3,4,6]
            
            cloud.append(int(data[1]))#edge: data[1]='5'
            self.cloud=cloud
            print("ttttttttt",self.dataNodeList,self.cloud)
            #dataV=data[2]
            dataVolum=int(data[2][0:1])
            tos=int(data[3])
            
            
            graph_now = self.topology_awareness.graph
            cloud=self.cloud
            dataNode=self.dataNodeList
            if self.temp_num==0:
                self.network_topo=self.topology_awareness.graph#get topo
                print("network_topo= ",self.network_topo)
                self.temp_num=1
            print("network_topo= ",self.network_topo.edges)
            
            
            #TreeFunctionNode_MetaData,steiner_path=self.steiner_creator.getSteinerTree_and_NodeRole(dataNode,cloud,self.network_topo)
            TreeFunctionNode_MetaData,steiner_path=self.steiner_creator.GetDistributStarTopo(dataNode,cloud)
            
            print(" MetaData!!!!!!!  ",TreeFunctionNode_MetaData,"flow_Path",steiner_path)
            self.install_steiner_Flow(steiner_path,tos)
            
            #print("metameta type",type(TreeFunctionNode_MetaData))
            byteDict=bytes('{}'.format(TreeFunctionNode_MetaData))
            
            #BsendData=bytes(str(TreeFunctionNode_MetaData))
            net_address=('127.0.0.1',9999)
            s2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s2.sendto(byteDict,net_address)
            s2.close()
  
            
            for testpath in steiner_path:
                for i in range(len(testpath)-1):
                    print("path bw:",graph_now[testpath[i]][testpath[i+1]]["bandwidth"])       
            
        s.close()
            
    def install_steiner_Flow(self,steiner_path,tos):
        for path in steiner_path:
                ip_srcx="10.0.0."+str(path[0])
                ip_dstx="10.0.0."+str(path[-1])
                eth_type=2048
                msg=self.testmsg#test
                in_portx=1#Since each path starts sending data locally, the start port must be 1
                #in_portx=msg.match["in_port"]
                #print("inport inport test !!!!!!!!!!!!!",in_portx)#
                flow_info=(eth_type,ip_srcx,ip_dstx,in_portx)#inport default=1
                #datapath.id = path1[0]
                result = self.get_sw(path[0], in_portx, ip_srcx, ip_dstx)
                #print("msg  test !!!!!!!!!!!!!msg",msg)
                #print("result !!!!!!!!!!",result)
                if result:
#                    print("test data",self.datapaths,
#                                      self.topology_awareness.link_to_port,
#                                      self.topology_awareness.access_table,path,
#                                      flow_info,msg.buffer_id,msg.data,tos,"\n222222222222222")
                    self.install_flow(self.datapaths,
                                      self.topology_awareness.link_to_port,
                                      self.topology_awareness.access_table,path,
                                      flow_info,msg.buffer_id,msg.data,tos)
                else:
                    print("install steiner Flow erro, result result is none")
        print("steinreFlow install ok tos =",tos)        
        
        
        
        
    def refresh_path_history(self):
        while True:
            self.CtoP_path_history=[]
            print("CtoP_path_history clear")     
            self.DtoC_path_history=[]
            print("DtoC_path history clear") 
            time.sleep(10)

    def _all_path_discover(self):
        i = 0
        j = 0
        x=0
        while x<10:#while true
            if i == 10:
                graph_now = self.topology_awareness.graph
                hub.sleep(1)
                self.all_path_list = self.get_all_paths(graph_now)
                #print(self.all_path_list)
                

                bandwidth_list = list(self.topology_awareness.graph.edges.data("bandwidth")) 
                delay_list=list(self.topology_awareness.graph.edges.data("delay"))
                if x<10:
                    print("graph.nodes:", graph_now.nodes)
                    print("graph.edges:", graph_now.edges)
                    print("graph_now:",graph_now)
                    print(delay_list)
                
                    print(bandwidth_list)
                    #print("888888888888888",self.topology_awareness.link_to_port)
                x=x+1
                i=0

                
            hub.sleep(1)
            i = i + 1
            j = j + 1


        
    def show_bandwidth(self):
        bandwidth_list = list(self.topology_awareness.graph.edges.data("bandwidth"))  # Is the remaining bandwidth list;
        link_utilization_list = []
        re_bandwidth_list = []
        for i in range(len(bandwidth_list)):
            bandwidth_list_value_i = list(bandwidth_list[i])
            if bandwidth_list_value_i[0] < bandwidth_list_value_i[1]:
                if bandwidth_list_value_i[0] == 1:
                    link_utilization = (setting.MAX_CAPACITY/1000*2-bandwidth_list_value_i[2])/(setting.MAX_CAPACITY/1000*2)
                else:
                    link_utilization = (setting.MAX_CAPACITY/1000-bandwidth_list_value_i[2])/(setting.MAX_CAPACITY/1000)
                if bandwidth_list_value_i[0] == 1:
                    link_utilization_list.append(link_utilization)
                    link_utilization_list.append(link_utilization)
                else:
                    link_utilization_list.append(link_utilization)
                list1 = []
                list1.append(bandwidth_list_value_i[0])
                list1.append(bandwidth_list_value_i[1])
                list1.append(bandwidth_list_value_i[2])
                list1.append(str(link_utilization*100)+"%")
                graph = self.topology_awareness.graph
                delay = graph[bandwidth_list_value_i[0]][bandwidth_list_value_i[1]]["delay"]
                list1.append(delay)
                re_bandwidth_list.append(list1)
        link_utilization_mean = np.mean(link_utilization_list)
        link_utilization_std = np.std(link_utilization_list, ddof=1)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Collect datapath information.
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        '''
            In packet_in handler, we need to learn access_table by ARP.
            Therefore, the first packet from UNKOWN host MUST be ARP.
        '''
        msg = ev.msg
        self.testmsg=msg#test
        datapath = msg.datapath
        in_port = msg.match["in_port"]
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if isinstance(arp_pkt, arp.arp):  # if "arp_pkt" is a instance of "arp.arp", return true
            self.logger.debug("----------------ARP processing---------------")
            self.arp_forwarding(msg, arp_pkt.src_ip, arp_pkt.dst_ip)

        if isinstance(ip_pkt, ipv4.ipv4):
            self.logger.debug("----------------IPV4 Processing----------------")
            tos = ip_pkt.tos
            if len(pkt.get_protocols(ethernet.ethernet)):  # if pkt.get_protocols(ethernet.ethernet) != None, return True
                eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype  # eth_type,  IP 2048, ARP 2054
                #print("packet in tos is :",tos)
                self.flow_forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst, tos)
  
                

    def flow_forwarding(self, msg, eth_type, ip_src, ip_dst, tos):
        """
            To calculate best forwarding path and install them into datapaths.
        """
        tos_ecn = tos# & 0b00000011  # tos_ecn Indicates the traffic type
            
        datapath = msg.datapath
        in_port = msg.match["in_port"]
        #print("flow forwarding tos: ",tos)
        history=str(ip_src)+' '+str(ip_dst)+' '+str(tos)
            
        if ((tos>119) and (history not in self.pack_in_history)) or tos == 0  :  # Filter the data stream that has been sent to packet_in
        #if  tos ==0:  #if tos==0

                if tos !=0:
                    history=str(ip_src)+' '+str(ip_dst)+' '+str(tos)
                    self.pack_in_history.append(history)
                result = self.get_sw(datapath.id, in_port, ip_src, ip_dst)
                tos_dscp = (tos & 0b11111100)/4
                tos_ecn = tos #& 0b00000011
                print("tos_dscp={0},tos_ecn={1}".format(tos_dscp,tos_ecn))
                if result:
                    src_sw, dst_sw = result[0], result[1]
                    if dst_sw:
                        path = self.get_best_path(ip_src,ip_dst,src_sw, dst_sw, tos_ecn)
                        # path: [1,3,7,11,15]
                        flow_info = (eth_type, ip_src, ip_dst, in_port)
        
                         
                        self.install_flow(self.datapaths,
                                          self.topology_awareness.link_to_port,
                                          self.topology_awareness.access_table, path,
                                          flow_info, msg.buffer_id, msg.data, tos)



    def get_k_best_path(self, src_sw, dst_sw, tos_ecn, k):   # Take the first k best paths
        all_paths = self.all_path_list[src_sw][dst_sw]
        # all_paths = [[1, 2, 4, 8, 12], [1, 2, 5, 8, 12], [1, 3, 6, 9, 12], [1, 3, 7, 9, 12]]

        path_dic = self.mfstm_path_dic_selection(all_paths, tos_ecn)
        # path_dic: {0: 0.675, 1: 0.554, 2: 0.399, 3: 0.942}

        sorted_path_list = sorted(list(path_dic.items()), key=lambda kv: (kv[1], kv[0]), reverse=True)
        # sorted_path_list：[(3, 0.942), (0, 0.675), (1, 0.554), (2, 0.399)]

        k_best_path = []
        k_best_path_value = []
        for i in range(k):
            k_best_path_num = sorted_path_list[i][0]
            k_best_path.append(all_paths[k_best_path_num])
            k_best_path_value.append(sorted_path_list[i][1])
        return k_best_path, k_best_path_value


    def count_path(self,path,path_history):
        count=0
        for ele in path_history:
            if(ele==path):
                count=count+1
        return count


    def get_best_path(self,src_ip,dst_ip, src_sw, dst_sw, tos_ecn):
        ##test
        #print("start------ select path!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
        all_paths = self.all_path_list[src_sw][dst_sw]

        if tos_ecn==0:
            best_path=all_paths[0]
            print("ping select tos",tos_ecn)
        else:
            best_path=self.ecmp_selection(all_paths)
            
            
            fpWrite=open(self.trad_write_name,"a+")#"_"+name_parameter+"_"+str(dataVolum)+"M"+".txt"
            fpWrite.write("Trad_write:"+" network_comsumption:"+str(len(best_path))+ " tos: "+str(tos_ecn)+" flow: "+str(best_path)+"\n")
            print("result record ok")
            fpWrite.close()
            
            print("ecmp select tos = ",tos_ecn)
            
        print("slect path:",best_path)
        self.all_path_history.append(best_path)

        
        
        return best_path


    
    
    def DtoC_delay_pathselection(self,all_path):
        i=0
        path_value={}
        for path in all_path:
            path_value.setdefault(i,{"delay":0})
            path_value[i]["delay"]=self.refresh_delay(path,self.DtoC_path_history,self.DtoC_dataVolume)
#            k = self.count_path(path,self.DtoC_path_history)
#            path_value[i]["delay"]=path_value[i]["delay"]+k
            print("path",path)

            print(("path delay:{0}".format(path_value[i]["delay"])))
            i=i+1
        index = min(zip(path_value.values(),path_value.keys()))[1]
        return all_path[index]
    
    def CtoP_delay_pathselection(self,all_path):
        i=0
        path_value={}
        for path in all_path:
            path_value.setdefault(i,{"delay":0})
            path_value[i]["delay"]=self.refresh_delay(path,self.CtoP_path_history,self.CtoP_dataVolume)
#            k = self.count_path(path,self.CtoP_path_history)
#            path_value[i]["delay"]=path_value[i]["delay"]+k
            print("path",path)

            print(("path delay:{0}".format(path_value[i]["delay"])))
            i=i+1
        index = min(zip(path_value.values(),path_value.keys()))[1]
        return all_path[index]
        
    
    
    def bandwidth_selection(self,all_path):
        start_time=time.time()
        i=0
        path_value={}
        for path in all_path:
            path_value.setdefault(i,{"bandwitdh":0})#dacuo l ..
            path_value[i]["bandwitdh"]=self.get_rbw(path,self.CtoP_path_history,self.CtoP_dataVolume)
            print("path={0},bandwitdh={1}".format(path,path_value[i]["bandwitdh"]))
            i=i+1
        index = max(zip(path_value.values(),path_value.keys()))[1]
        print("select path={0},bw={1}".format(all_path[index],path_value[index]["bandwitdh"]))
        print("use time",time.time()-start_time)
        return all_path[index]
    
    def adjacent_node_count(self,start,end,path_history):
        count=0
        for path in path_history:
            for i in range(len(path)-1):
                if(path[i]==start and path[i+1]==end):
                    count=count+1
                if(path[i+1]==start and path[i]==end):
                    count=count+1
#        print("rbw_adj_count",count)
        return count

    def get_rbw(self, path,this_history,dataVolum):
        graph = self.topology_awareness.graph
        #zaizheli gengxin tu !mei suanwan yige lujing jiu mashang jiandaikuan
        min_rbw = setting.MAX_CAPACITY
        
        for i in range(len(path)-1):
            count=self.adjacent_node_count(path[i],path[i+1],this_history)
            #print("graph[path[i]][path[i+1]]",graph[path[i]][path[i+1]]["bandwidth"])
            rbw = graph[path[i]][path[i+1]]["bandwidth"]-count*dataVolum#self.singleUpdateData
            
            #print("rbw",rbw)
            min_rbw = min(min_rbw, rbw)
            
        #print("min_rbw",min_rbw)
        return min_rbw




    
    
    def get_hop(self,path):
        hop = len(path)
        return hop
        
    
    
    def getFlowHistory(self):
        pass    
    
    
    def refresh_flow_table(self,path):
        if 4 in path :
            self.s4_table_num=self.s4_table_num+2
        if 5 in path :
            self.s5_table_num=self.s5_table_num+2
        if 6 in path :
            self.s6_table_num=self.s6_table_num+2
        if 7 in path : 
            self.s7_table_num=self.s7_table_num+2
        
    def get_flow_table(self,thisPath):
       

        s4=self.s4_table_num
        s5=self.s5_table_num
        s6=self.s6_table_num
        s7=self.s7_table_num
        
        flow_table_num=0
        
        if 4 in thisPath:
            flow_table_num=s4+2
        if 5 in thisPath:
            flow_table_num=s5+2
        if 6 in thisPath:
            flow_table_num=s6+2
        if 7 in thisPath:
            flow_table_num=s7+2
    
        return flow_table_num
    
    

    
    
    def get_delay(self, path):
        graph = self.topology_awareness.graph
        delay = 0
        for i in range(len(path)-1):
            delay = delay + graph[path[i]][path[i+1]]["delay"]
        return delay
    
    
    def delay_adjacent_node_count(self,count,start,end,path_history):
        
        for path in path_history:
            for i in range(len(path)-1):
                if(path[i]==start and path[i+1]==end):
                    count=count+1
                if(path[i+1]==start and path[i]==end):
                    count=count+1
        return count
    
    
    def refresh_delay(self,path,history,dataVolume):
        graph = self.topology_awareness.graph
        delay=0
        count=0
        for i in range(len(path)-1):
            count=self.delay_adjacent_node_count(count,path[i],path[i+1],history)
            delay=graph[path[i]][path[i+1]]["delay"]+delay

        delay=delay+count*dataVolume*0.00015#0.0005 0.0002   most 0.00015
        print("count={0},dataVolume={1},add delay={2} ".format(count,dataVolume,str(count*dataVolume*0.00015)))
        
        return delay
 

    def ecmp_selection(self, all_paths):
        path = all_paths[random.randint(0, len(all_paths)-1)]
        return path

    def get_all_paths(self, graph):
        """
            return all paths among all nodes. 
            eg: cycle_graph nodes:[0,1,2,3], all_paths:
             {0: {0: [0], 1: [[0, 1], [0, 3, 2, 1]], 2: [[0, 1, 2], [0, 3, 2]], 3: [[0, 3], [0, 1, 2, 3]]}, 
             1: {0: [[1, 0], [1, 2, 3, 0]], 1: [1], 2: [[1, 2], [1, 0, 3, 2]], 3: [[1, 0, 3], [1, 2, 3]]},
             2: {0: [[2, 1, 0], [2, 3, 0]], 1: [[2, 1], [2, 3, 0, 1]], 2: [2], 3: [[2, 3], [2, 1, 0, 3]]}, 
             3: {0: [[3, 0], [3, 2, 1, 0]], 1: [[3, 0, 1], [3, 2, 1]], 2: [[3, 2], [3, 0, 1, 2]], 3: [3]}}
        """
        _graph = copy.deepcopy(graph)
        paths = {}
        # print "+++++++++++++_graph.edges():", _graph.edges()

        for src in _graph.nodes():
            paths.setdefault(src, {src: [[src]]})
            for dst in _graph.nodes():
                if src == dst:
                    continue
                paths[src].setdefault(dst, [])

                paths[src][dst] = self.get_m_shortest_simple_paths(_graph, src, dst)  
        return paths

    def get_m_shortest_simple_paths(self, graph, src, dst):
        """use the function shortest_simple_paths() in networkx to get all paths from src to dst."""
        generator = nx.shortest_simple_paths(graph, source=src, target=dst)
        m = setting.m
        m_shortest_simple_paths = []
        i = 0
        try:
            for path in generator:
                if len(path) > 16:  
                    break
                m_shortest_simple_paths.append(path)
                i = i + 1
                if i == m:
                    break
            return m_shortest_simple_paths
        except:
            self.logger.debug("No path between")



    def install_flow(self, datapaths, link_to_port, access_table, path,
                     flow_info, buffer_id, data=None, tos=0):
        ''' 
            Install flow entires for roundtrip: go and back.
            @parameter: path=[dpid1, dpid2...]
                        flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        #data=None#test
        if path is None or len(path) == 0:
            self.logger.info("Path error!")
            return
        in_port = flow_info[3]
        first_dp = datapaths[path[0]]
        out_port = first_dp.ofproto.OFPP_LOCAL
        back_info = (flow_info[0], flow_info[2], flow_info[1])

        # inter_link
        if len(path) > 2:
            for i in range(1, len(path)-1):
                port = self.get_port_pair_from_link(link_to_port,
                                                    path[i-1], path[i])
                port_next = self.get_port_pair_from_link(link_to_port,
                                                         path[i], path[i+1])
                if port and port_next:
                    src_port, dst_port = port[1], port_next[0]  # the in_port and out_port in one switch
                    datapath = datapaths[path[i]]
                    self.send_flow_mod(datapath, flow_info, src_port, dst_port, tos)
                    self.send_flow_mod(datapath, back_info, dst_port, src_port, tos)
                    self.logger.debug("inter_link flow install")

        # the last flow entry: tor -> host
        if len(path) > 1:
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[-2], path[-1])
            if port_pair is None:
                self.logger.info("Port is not found")
                return
            src_port = port_pair[1]

            dst_port = self.get_port(flow_info[2], access_table)
            if dst_port is None:
                self.logger.info("Last port is not found.")
                return

            last_dp = datapaths[path[-1]]
            self.send_flow_mod(last_dp, flow_info, src_port, dst_port, tos)
            self.send_flow_mod(last_dp, back_info, dst_port, src_port, tos)

            # the first flow entry
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[0], path[1])
            if port_pair is None:
                self.logger.info("Port not found in first hop.")
                return
            out_port = port_pair[0]
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, tos)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, tos)
            self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)

        # src and dst on the same datapath
        else:
            out_port = self.get_port(flow_info[2], access_table)
            if out_port is None:
                self.logger.info("Out_port is None in same dp")
                return
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, tos)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, tos)
            self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)

    def send_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Send packet out packet to assigned datapath.
        """
        out = self._build_packet_out(datapath, buffer_id,
                                     src_port, dst_port, data)
        if out:
            datapath.send_msg(out)

    def get_port(self, dst_ip, access_table):
        """
            Get access port if dst host.
            access_table: {(sw,port) :(ip, mac)}
        """
        if access_table:
            if isinstance(list(access_table.values())[0], tuple):
                for key in list(access_table.keys()):
                    if dst_ip == access_table[key][0]:
                        dst_port = key[1]
                        return dst_port
        return None

    def send_flow_mod(self, datapath, flow_info, src_port, dst_port, tos):
        """
            Build flow entry, and send it to datapath.
        """
        tos_dscp = (tos & 0b11111100)/4
        tos_ecn = tos & 0b00000011

        parser = datapath.ofproto_parser
        actions = []
        actions.append(parser.OFPActionOutput(dst_port))
        # actions.append(parser.OFPActionOutput(dst_port+1))

        match = parser.OFPMatch(
            in_port=src_port, eth_type=flow_info[0], ipv4_src=flow_info[1],
            ipv4_dst=flow_info[2], ip_dscp=tos_dscp, ip_ecn=tos_ecn)

        self.add_flow(datapath, 1, match, actions,
                      idle_timeout=setting.idle_timeout, hard_timeout=setting.hard_timeout)


    def add_flow(self, dp, p, match, actions, idle_timeout=0, hard_timeout=0):
        """
            Send a flow entry to datapath.
        """
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=p,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    def get_port_pair_from_link(self, link_to_port, src_dpid, dst_dpid):
        """
            Get port pair of link, so that controller can install flow entry.
        """
        if (src_dpid, dst_dpid) in link_to_port:
            return link_to_port[(src_dpid, dst_dpid)]
        else:
            self.logger.info("dpid:%s->dpid:%s is not in links" % (
                             src_dpid, dst_dpid))
            return None

    def get_sw(self, dpid, in_port, src, dst):
        """
            Get pair of source and destination switches.
        """
        # print "datapath.id:", dpid, "in_port:", in_port, "ip_src:", src, "ip_dst:", dst

        src_sw = dpid
        dst_sw = None

        src_location = self.topology_awareness.get_host_location(src)
        if in_port in self.topology_awareness.access_ports[dpid]:
            if (dpid, in_port) == src_location:
                #print("test dpid inport srclocation",src_location)
                src_sw = src_location[0]
            else:
                print("test dpid inport srclocation None 222222",dpid,in_port,src,dst)
                return None
        dst_location = self.topology_awareness.get_host_location(dst)
        if dst_location:
            dst_sw = dst_location[0]

        return src_sw, dst_sw

    def arp_forwarding(self, msg, src_ip, dst_ip):
        """ Send ARP packet to the destination host,
            if the dst host record is existed,
            else, flow it to the unknow access port.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        result = self.topology_awareness.get_host_location(dst_ip)
        if result:  # host record in access table.
            datapath_dst, out_port = result[0], result[1]
            datapath = self.datapaths[datapath_dst]
            out = self._build_packet_out(datapath, ofproto.OFP_NO_BUFFER,
                                         ofproto.OFPP_CONTROLLER,
                                         out_port, msg.data)
            datapath.send_msg(out)
            self.logger.debug("Reply ARP to knew host")
        else:
            self.flood(msg)

    def flood(self, msg):
        """
            Flood ARP packet to the access port
            which has no record of host.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dpid in self.topology_awareness.access_ports:
            for port in self.topology_awareness.access_ports[dpid]:
                if (dpid, port) not in list(self.topology_awareness.access_table.keys()):
                    datapath = self.datapaths[dpid]
                    out = self._build_packet_out(
                        datapath, ofproto.OFP_NO_BUFFER,
                        ofproto.OFPP_CONTROLLER, port, msg.data
                    )
                    datapath.send_msg(out)
        self.logger.debug("Flooding msg")

    def _build_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Build packet out object.
        """
        actions = []
        if dst_port:
            actions.append(datapath.ofproto_parser.OFPActionOutput(dst_port))

        msg_data = None
        if buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            if data is None:
                return None
            msg_data = data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=buffer_id,
            data=msg_data, in_port=src_port, actions=actions
        )
        return out

