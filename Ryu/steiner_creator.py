#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.base.app_manager import lookup_service_brick

import networkx as nx
import networkx.algorithms.approximation as nx_approx
import random
import setting
import copy
import itertools

class Steiner_Creator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    steiner_weight="true_weight"#None#"bw"#steiner_weight="true_weight"
    def __init__(self, *args, **kwargs):
       
        super(Steiner_Creator, self).__init__(*args, **kwargs)
        self.name="Steiner_Creator"
        self.topology_awareness = lookup_service_brick("TopologyAwareness")
        self.bandwith_detector = lookup_service_brick("BandwidthDetector")


        self.topo=self.topology_awareness.graph
        
        self.test_graph=nx.Graph()



    def getSteinerTree_and_NodeRole(self,dataNode,cloud,network_topo,steiner_crator,dataVolume):
        terminal_nodes=dataNode+cloud
        #print("terminal_nodes !!!!!!!!!!!!!!!!!!!!!!!!!!=",terminal_nodes)
        G=network_topo#.to_undirected()# convert topo to undirected 
        #G=self.test_graph.to_undirected()
        print("G edge !!!!!!!!!!!!!!ttttt",G.edges(data='bw'))
        
        
        if steiner_crator==3:
            T=nx_approx.steiner_tree(G,terminal_nodes)#networkx finding SteinerTree
        elif steiner_crator==4:#ECWSS_BA Finding SteinerTree
            T=nx.Graph()
            T_Edge=self.GreedyStree(G,dataNode,cloud,dataVolume)#ECWSS_BA Finding SteinerTree
            '''ECWSS_BA Finding SteinerTree'''
            for edge in T_Edge:
                for i in range(len(edge)-1):
                    #print("edge:",edge[i],'+',edge[i+1])
                    T.add_edge(edge[i],edge[i+1])
        else :
            print("topo mode input erro")

        print("steinerTree node={0},edge={1} ".format(T.nodes,T.edges))
        
        '''Write-DAG, Transfer the T_Edge to DAG'''
        # Identify (functional node) ------ Data node (data node only), coding node, cloud central node
        onlyDataNode=[]#The degree of the data node is only 1, and it is not a point in the center of the cloud, or a point in the data node that is not a coding node
        encodeNode=[]
        for node in T.nodes:
            if T.degree(node)==1:
                #The degree of a data node is only 1 and is not a point in the cloud center
                if node!=cloud[0]:
                    onlyDataNode.append(node)      
            if (node in dataNode and T.degree(node)==2):#If the degree is equal to 2 and it is also a data node, it must be a coding node
                #node is compute node                   
                encodeNode.append(node)
            if (T.degree(node)>=3 and node not in cloud):#If the degree is greater than or equal to 3, it must be a coded node, because there is no loop multigraph case.
                print("encode node apend !!!!!!!!!!!!!!!!!!!!!!!")
                encodeNode.append(node)
        functionNode= encodeNode + onlyDataNode + cloud# Not  dataNode, because dataNode overlaps encodeNode
        passNode=list(T.nodes-set(functionNode))#Passing node
        print("encodeNode",encodeNode)
        print("onlyDataNode",onlyDataNode)
        print("passNode",passNode)
        print("functionNode",functionNode)

        nodeMetaData={}
        

        
        for node in functionNode:#The final returned node role metadata
            if node in onlyDataNode:# onlyDataNode Is a data node in a function node, but not an encoding node.A data node that is only a data node
                direct_Node_path_dict=self.find_direct_connect_functionNodeAndPath(T,node,functionNode)
                for directNode,direct_path in direct_Node_path_dict.items():
                    self.addTwoDimdict(nodeMetaData,node,"dst",directNode)
                    self.addTwoDimdict(nodeMetaData,node,"role","1")#role 0;cloud 1:nolyDataNode 2:onlyEncodeNode 3:DataAndEncodeNode
            if node in encodeNode:
                #Identify the k closest function nodes directly connected to the encode node, with those closer to the cloud serving as the next hop and the rest as source nodes
                #  Direct connection to encodenode does not require passing through the k function nodes of other Functionnodes.
                candidateNodeSet=self.find_direct_connect_functionNodeAndPath(T,node,functionNode)
                
                src_list=[]
                nodeToCloud_path=nx.shortest_path(T,node,cloud[0])
                for key in candidateNodeSet: #If a node's path to the cloud center passes through a certain key node, then that key node 
                    #is the destination of the node. If the node's path does not pass through any key nodes, then the node's destination is the node that is closer to the cloud center.
                    if key in nodeToCloud_path:
                        the_dst=key
                    else:
                        src_list.append(key)
                self.addTwoDimdict(nodeMetaData,node,"dst",the_dst)
                self.addTwoDimdict(nodeMetaData,node,"src",src_list)
                if node in dataNode:
                    self.addTwoDimdict(nodeMetaData,node,"role","3")
                else:
                    self.addTwoDimdict(nodeMetaData,node,"role","2")

            if node in cloud:
                cloud_src=[]
                direct_Node_path_dict=self.find_direct_connect_functionNodeAndPath(T,node,functionNode)
                for key in direct_Node_path_dict:
                    cloud_src.append(key)
                self.addTwoDimdict(nodeMetaData,node,"src",cloud_src)
                self.addTwoDimdict(nodeMetaData,node,"role","0")
                    
        steiner_function_path=[]
        for key in nodeMetaData:
            if 'dst' in nodeMetaData[key]:
                steiner_function_path.append(nx.shortest_path(T,key,nodeMetaData[key]['dst']))
        #print("metadata3 ",nodeMetaData)
        return nodeMetaData,steiner_function_path
        
        #you xiang tu yao zhuan wuxiangtu 
    def find_direct_connect_functionNodeAndPath(self,T,node,functionNode):
        direct_node_path={}
        for node2 in functionNode:
            if node!=node2:
                direct_node_path[node2]=nx.shortest_path(T,source=node,target=node2,weight=None)#If there are functional nodes, then the point must not be directly connected. #shortest path

                direct_node_path[node2].remove(node)
                direct_node_path[node2].remove(node2)
                if set(functionNode) & set(direct_node_path[node2]):# 
                    direct_node_path.pop(node2)
        print("node {0} direct candidate_node is{1} ".format(node,direct_node_path))
        return direct_node_path    #direct_node_path={ the_directNode : the_path_to_directNode}        



    def addTwoDimdict(self,thedict,key_a,key_b,val):# 
        if key_a in thedict:
            thedict[key_a].update({key_b:val})
        else:
            thedict.update({key_a:{key_b:val}})        
        

        
        
        
        
    def get_m_shortest_simple_paths(self, graph, src, dst,m):
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


    def GetPipelineTopo(self,dataNode,cloud):
        ##

        G=self.test_graph.to_undirected()
        T=nx.Graph()
        tree_edge=[]
        
        dataNode=dataNode
        #random dataNode
        random.shuffle(dataNode)
        dataNode_cloud=dataNode+cloud
        print("dataNode_cloud!!!!!!!!!!!!",dataNode_cloud)
        for i in range(len(dataNode_cloud)-1): 
            if i!=len(dataNode_cloud):
                #print("i   !!!!!!!!",i)
                src=dataNode_cloud[i]
                dst=dataNode_cloud[i+1]
                paths=self.get_m_shortest_simple_paths(G, src, dst,1)#Find m shortest paths from source (src) to destination (dst)
                path=paths[random.randint(0,len(paths)-1)]
                print("path!!!!!!!!!!!!!!!!!!",path)
                tree_edge.append(path)

        nodeMetaData={}
        cloud=cloud[0]#cloud=cloud[0]
        #先定role
        self.addTwoDimdict(nodeMetaData,dataNode_cloud[0],"role","1")
        self.addTwoDimdict(nodeMetaData,cloud,"role","0")
        
               

        
        #middle_node为dataNode_cloud去头去尾后的中间节点
        middle_node=copy.deepcopy(dataNode_cloud)
        del middle_node[0]
        del middle_node[-1]
        for node in middle_node:# important 
            self.addTwoDimdict(nodeMetaData,node,"role","3")

        #定encode_node src dst
        for i in range(len(middle_node)):# for i in range(5):  0 1 2 3 4
            src_list=[]
            if i==0:
                src_list.append(dataNode_cloud[0])
                self.addTwoDimdict(nodeMetaData,middle_node[i],"src",src_list)
                self.addTwoDimdict(nodeMetaData,middle_node[i],"dst",middle_node[i+1])
            elif i==len(middle_node)-1:
                src_list.append(middle_node[i-1])
                self.addTwoDimdict(nodeMetaData,middle_node[i],"src",src_list)
                self.addTwoDimdict(nodeMetaData,middle_node[i],"dst",cloud)
            else:
                src_list.append(middle_node[i-1])
                self.addTwoDimdict(nodeMetaData,middle_node[i],"src",src_list)
                self.addTwoDimdict(nodeMetaData,middle_node[i],"dst",middle_node[i+1])
            
            
        # data node has dst
        self.addTwoDimdict(nodeMetaData,dataNode_cloud[0],"dst",dataNode_cloud[1])

        cloud_src=[]
        cloud_src.append(dataNode_cloud[-2])
        self.addTwoDimdict(nodeMetaData,cloud,"src",cloud_src)
            
            


        print("nodeMetaData!!!!!!!!!!!1",nodeMetaData)
        return nodeMetaData,tree_edge

         


    def GetDistributStarTopo(self,dataNode,cloud):

        G=self.test_graph.to_undirected()
        
        tree_edge=[]
        compute_list=list(set(G.nodes)-set(dataNode)-set(cloud)) 
        compute_node=compute_list[random.randint(0,len(compute_list)-1)]
        print("compute node !!!!!!!!!!!!!!!!",compute_node)
        dataNode_cloud=dataNode+cloud
        print("dataNode_cloud!!!!!!!!!!",dataNode_cloud)
        for node in  dataNode_cloud :
            src=node
            dst=compute_node
            paths= self.get_m_shortest_simple_paths(G, src, dst,3)#

            path=paths[random.randint(0,len(paths)-1)]
            tree_edge.append(path)

        
        meta_path=tree_edge
        cloud=cloud[0]#cloud=cloud[0]
        print("tree_edge!!!!!!!!!!!!!!!!!!",tree_edge)
        nodeMetaData={}#
        self.addTwoDimdict(nodeMetaData,cloud,"role","0")
        self.addTwoDimdict(nodeMetaData,compute_node,"role","2")

        for node in dataNode:
            self.addTwoDimdict(nodeMetaData,node,"role","1")
        #define src and dst
        #compute src and dst
        src_list1=dataNode
        self.addTwoDimdict(nodeMetaData,compute_node,"src",src_list1)
        self.addTwoDimdict(nodeMetaData,compute_node,"dst",cloud)
        
        #cloud src
        cloud_src=[]
        cloud_src.append(compute_node)
        self.addTwoDimdict(nodeMetaData,cloud,"src",cloud_src)
        #dataNode dst
        for node in dataNode:
            self.addTwoDimdict(nodeMetaData,node,"dst",compute_node)
        
        
        return nodeMetaData,meta_path
    
        



    def GreedyStree(self,G,dataNode,cloud,dataVolume):
        
        totle=0
        for edge in G.edges:
            
            totle=totle+G[edge[0]][edge[1]]['bw']
        avg_bw=totle/len(G.edges)
        print("avg_bw>>>>>>>>>>>>>>>>.",avg_bw)
        for edge in G.edges:
            G[edge[0]][edge[1]]['true_weight']=float(avg_bw)/float(G[edge[0]][edge[1]]['bw'])
        
        print("\n\n")
        print("Graph bw >>>>",G.edges(data="bw"))
        print("Graph true_weight >>>>",G.edges(data="true_weight"))
        print("\n\n")
        
        
         
        #Order of heartbeat number of data nodes to the cloud:
        TreeNode=[]
        TreeEdge=[]
        new_treeNode=[]
        waite=dataNode+cloud
        x=dataNode+cloud+new_treeNode
        
        edge_to_cloud_nearst=[]

        adjiantNum=0
        #while adjiantNum!=len(x)-1:
        while len(waite)!=0:
                
            #if len(waite)!=0:
                t1_to_cloud_length={}
                t1_t2_length={}
                # take t1,  Farthest from the center
                print("waite------- ",waite)
                for node in waite:
                    length=nx.shortest_path_length(G,node,cloud[0],weight=None)#t1 use distance 
                    t1_to_cloud_length[node]=length
                t1=max(t1_to_cloud_length,key=t1_to_cloud_length.get)
                print("t1_to_cloud_length--",t1_to_cloud_length)
                print("t1--------",t1)



                #take t2
                for node in x:
                    length=nx.shortest_path_length(G,node,t1,weight=self.steiner_weight)
                    if node!=t1:
                        t1_t2_length[node]=length
                print("t1_t2_length--- ",t1_t2_length)


                min_val=min(t1_t2_length.values())
                list_t2=[k for k, v in t1_t2_length.items() if v==min_val]
                print("list_2 !!!",list_t2)
                n_c_length={}
                if len(list_t2)==1:#only 1 t2
                    t2=list_t2[0]
                else:
                    for node in list_t2:
                        n_c_length[node]=nx.shortest_path_length(G,node,cloud[0],weight=self.steiner_weight)# 
                        #print("n_c_length[node]1111",n_c_length[node])

                    min_val2=min(n_c_length.values())# 
                    list_t2_2=[k for k, v in n_c_length.items() if v==min_val2]# 
                    print("list_t2_2!!!",list_t2_2)
                    if len(list_t2_2)==1:
                        t2=list_t2_2[0]
                    else:#Look at the average distance between each t2 and the other nodes
                        n_other_length={}
                        for node in list_t2_2:#
                            n_other_length[node]=self.node_to_waite_length(G,node,waite)# 
                            print("n_other_length[node]  !!!",node,'  + ',n_other_length[node])
                        t2=min(n_other_length,key=n_other_length.get)
                print("t2--------",t2)

                #finding edge
                edge=nx.nx.shortest_path(G,t1,t2,weight=self.steiner_weight)##  
                print("new edge",edge)

                edge_to_cloud={}
                for node in edge:
                    if node!=cloud[0]:
                        edge_to_cloud[node]=nx.shortest_path_length(G,node,cloud[0],weight=self.steiner_weight)
                
                newWaite=min(edge_to_cloud,key=edge_to_cloud.get)
                print("edge_to_cloud--",edge_to_cloud)
                print("newwaite",newWaite)
                edge_to_cloud_nearst.append(newWaite)
                print("edge------- ",edge)
                


                TreeEdge.append(edge)
                waite.remove(t1)
                if t2 in waite:
                    waite.remove(t2)
                x=set(x).union(edge)
                
                #print("waite---after remove t1 t2",waite)
                print("x",x)
                print("treeEdge---- ",TreeEdge)
                adjiantNum=0
                for path in TreeEdge:
                    adjiantNum+=len(path)-1
                print("adjiantEdgeNum>>>>>",adjiantNum)
                print("edge_to_cloud_nearst>>>>>",edge_to_cloud_nearst)
        if adjiantNum!=len(x)-1:
            T=nx.Graph()
            component_list=[]
            for edge in TreeEdge:
                for i in range(len(edge)-1):
                    #print("edge:",edge[i],'+',edge[i+1])
                    T.add_edge(edge[i],edge[i+1])
            #component_num=nx.number_connected_components(T)
            #print("test component_num",component_num)      
            for i in nx.connected_components(T):
                component_list.append(list(i))
                print("node of components ",component_list)

            #get pairwise combinations
            list_combine=list(range(len(component_list)))
            #print(list_combine)
            distance_sequence=list(itertools.combinations(list_combine,2))
            #print(distance_sequence)
            nearst_node_dict={}

            #Connect the two closest nodes between the pairwise components
            for sequence in distance_sequence:
                    dict_d=self.component_distance(G,component_list[sequence[0]],component_list[sequence[1]])
                    print(min(dict_d,key=dict_d.get))# 
                    print(dict_d[min(dict_d,key=dict_d.get)])# 
                    nearst_node_dict[min(dict_d,key=dict_d.get)]=dict_d[min(dict_d,key=dict_d.get)]
            print("nearst_node_dict-----",nearst_node_dict)
            #All it takes to connect k connected components is k - 1 extra edge
            # 
            sorted_nearst_node_list=sorted(nearst_node_dict.items(),key=lambda x: x[1])# 

            if len(sorted_nearst_node_list)>1:
                sorted_nearst_node_list=sorted_nearst_node_list[0:-1]# list
            else :
                sorted_nearst_node_list=sorted_nearst_node_list
            #print("sorted_nearst_node_list >>>",sorted_nearst_node_list)

            sorted__dict=dict(sorted_nearst_node_list)# dict

            waite_connect_nodes_str=list(sorted__dict.keys())#list ['4-7', '1-13']
            #print( waite_connect_nodes_str)
            waite_connect_nodes=[]
            for l in waite_connect_nodes_str:
                    waite_connect_nodes.append(list(map(int,l.split('-'))))#[4, 7] [1, 13]

            for l in waite_connect_nodes:
                    edge=nx.shortest_path(G,l[0],l[1],weight=self.steiner_weight)
                    print("add edge ---------------",edge)
                    TreeEdge.append(edge)
            print("TreeEdge!!!!",TreeEdge)
            print("waite!!!!!!!",waite)
            for link in T.edges:
                if int(dataVolume)>=G[link[0]][link[1]]["bw"]:# avoid negative bw
                    G[link[0]][link[1]]["bw"]=1#avoid /0
                else:
                    G[link[0]][link[1]]["bw"]=G[link[0]][link[1]]["bw"]-int(dataVolume)
            print("\n\ndataVolume >>>>>> ",dataVolume)
            print("\n\n")
        return TreeEdge


    def to_cloud_distance(self,G,path,cloud):#Find the value of the path closest to the cloud center
        to_cloud_distance_dict={}
        for node in path:
            to_cloud_distance_dict[node]=nx.shortest_path_length(G,node,cloud)
        return min(to_cloud_distance_dict,key=to_cloud_distance_dict.get)


    def get_t1_t2_bestPath(self,G,t1,t2,cloud):#Find bestPath for the shortest path connected to t1t2 that is closest to the transport center
        t1_t2_path_generator=nx.all_shortest_paths(G,t1,t2)
        t1_t2_path_candidate={}
        for path in t1_t2_path_generator:
            t1_t2_path_candidate[self.to_cloud_distance(G,path,cloud)]=path
 
        key_list=t1_t2_path_candidate.keys()
        edge=t1_t2_path_candidate[min(key_list)]
        return edge

    def get_best_t2(self,G,t1,wait_connect_node):
        t1_t2_length={}
        for node in wait_connect_node:
            length=nx.shortest_path_length(G,t1,node)
            t1_t2_length[node]=length
        min_val=min(t1_t2_length.itervalues())
        list_t1=[k for k, v in t1_t2_length.iteritems() if v==min_val]
        print(list_t1)
 
    
    def node_to_waite_length(self,G,node,wait):
        n_w_length=0
        for x in wait:
            n_w_length+=nx.shortest_path_length(G,node,x)
            print("n_w_length",n_w_length)
        return n_w_length
        
        
    def node_to_list_length2(self,G,node,wait):
        temp=1000
        for x in wait:
                n_x_length=nx.shortest_path_length(G,node,x,weight=self.steiner_weight)
                #print(n_x_length)
                if n_x_length<temp:
                        temp=n_x_length
                        nearest_wait=x
                dict=str(node)+"-"+str(nearest_wait) 
        return  dict,temp

    def component_distance(self,G,componet1,componet2):
            dict={}
            for i in componet1:
                    index,length=self.node_to_list_length2(G,i,componet2)
                    dict[index]=length
            print(dict)
            return dict
        