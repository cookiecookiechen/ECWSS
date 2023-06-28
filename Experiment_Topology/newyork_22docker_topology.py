#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from mininet.net import Containernet
from mininet.node import Controller,RemoteController,Docker,OVSSwitch

import time
import threading
import socket

def myNetwork():
    net = Containernet(controller=Controller)

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, dpid='0000000000000001')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, dpid='0000000000000002')
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, dpid='0000000000000003')
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, dpid='0000000000000004')
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch, dpid='0000000000000005')
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch, dpid='0000000000000006')
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch, dpid='0000000000000007')
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch, dpid='0000000000000008')
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch, dpid='0000000000000009')
    s10 = net.addSwitch('S10', cls=OVSKernelSwitch, dpid='000000000000000a')
    s11 = net.addSwitch('s11', cls=OVSKernelSwitch, dpid='000000000000000b')
    s12 = net.addSwitch('s12', cls=OVSKernelSwitch, dpid='000000000000000c')
    s13 = net.addSwitch('s13', cls=OVSKernelSwitch, dpid='000000000000000d')
    s14 = net.addSwitch('s14', cls=OVSKernelSwitch, dpid='000000000000000e')
    
    s15 = net.addSwitch('s15', cls=OVSKernelSwitch, dpid='000000000000000f')
    s16 = net.addSwitch('s16', cls=OVSKernelSwitch, dpid='0000000000000010')
    s17 = net.addSwitch('s17', cls=OVSKernelSwitch, dpid='0000000000000011')
    s18 = net.addSwitch('s18', cls=OVSKernelSwitch, dpid='0000000000000012')
    s19 = net.addSwitch('s19', cls=OVSKernelSwitch, dpid='0000000000000013')
    s20 = net.addSwitch('s20', cls=OVSKernelSwitch, dpid='0000000000000014')
    s21 = net.addSwitch('s21', cls=OVSKernelSwitch, dpid='0000000000000015')
    s22 = net.addSwitch('s22', cls=OVSKernelSwitch, dpid='0000000000000016')

    info( '*** Add hosts\n')

  
    
    
    d1 = net.addDocker('d1', ip='10.0.0.1', dimage="era_write_docker")
    d2 = net.addDocker('d2', ip='10.0.0.2', dimage="era_write_docker")
    d3 = net.addDocker('d3', ip='10.0.0.3', dimage="era_write_docker")#, cpu_period=50000,cpu_quota=40000)#networkstatic/iperf3   sequenceiq/hadoop-docker:2.7.0
    d4 = net.addDocker('d4', ip='10.0.0.4', dimage="era_write_docker")
    d5 = net.addDocker('d5', ip='10.0.0.5', dimage="era_write_docker")
    d6 = net.addDocker('d6', ip='10.0.0.6', dimage="era_write_docker")
    d7 = net.addDocker('d7', ip='10.0.0.7', dimage="era_write_docker")
    d8 = net.addDocker('d8', ip='10.0.0.8', dimage="era_write_docker")
    d9 = net.addDocker('d9', ip='10.0.0.9', dimage="era_write_docker")
    d10 = net.addDocker('d10', ip='10.0.0.10', dimage="era_write_docker")
    d11 = net.addDocker('d11', ip='10.0.0.11', dimage="era_write_docker")
    d12 = net.addDocker('d12', ip='10.0.0.12', dimage="era_write_docker")
    d13 = net.addDocker('d13', ip='10.0.0.13', dimage="era_write_docker")
    d14 = net.addDocker('d14', ip='10.0.0.14', dimage="era_write_docker")
    
    d15 = net.addDocker('d15', ip='10.0.0.15', dimage="era_write_docker")
    d16 = net.addDocker('d16', ip='10.0.0.16', dimage="era_write_docker")
    d17 = net.addDocker('d17', ip='10.0.0.17', dimage="era_write_docker")
    d18 = net.addDocker('d18', ip='10.0.0.18', dimage="era_write_docker")
    d19 = net.addDocker('d19', ip='10.0.0.19', dimage="era_write_docker")
    d20 = net.addDocker('d20', ip='10.0.0.20', dimage="era_write_docker")
    d21 = net.addDocker('d21', ip='10.0.0.21', dimage="era_write_docker")
    d22 = net.addDocker('d22', ip='10.0.0.22', dimage="era_write_docker")









    info( '*** Add links\n')

    
    s1s3 = {'bw':300,'delay':'0.005'}
    net.addLink(s1, s3,port1=6,port2=2 ,cls=TCLink , **s1s3)
    s1s4 = {'bw':300,'delay':'0.0575'}
    net.addLink(s1, s4, port1=5,port2=2 ,cls=TCLink , **s1s4)
    s1s5 = {'bw':300,'delay':'0.0575'}
    net.addLink(s1, s5,port1=4,port2=5, cls=TCLink , **s1s5)
    s1s9 = {'bw':300,'delay':'0.0895'}
    net.addLink(s1, s9, port1=3,port2=7,cls=TCLink , **s1s9)
    s1s11 = {'bw':300,'delay':'0.111'}
    net.addLink(s1, s11,port1=2,port2=3, cls=TCLink , **s1s11)
    s1s20={'bw':300,'delay':'0.05'}
    net.addLink(s1 ,s20,port1=7 ,port2=2,cls=TCLink , **s1s20)
    
    s2s4 = {'bw':300,'delay':'0.001'}
    net.addLink(s2, s4,port1=3,port2=8, cls=TCLink , **s2s4)
    s2s5 = {'bw':300,'delay':'0.001'}
    net.addLink(s2, s5,port1=4,port2=2, cls=TCLink , **s2s5)
    s2s6 = {'bw':300,'delay':'0.001'}
    net.addLink(s2, s6,port1=2,port2=4, cls=TCLink , **s2s6)

    s3s21={'bw':300,'delay':'0.05'}
    net.addLink(s3,s21,port1=3,port2=2,cls=TCLink , **s3s21)
    s3s22={'bw':300,'delay':'0.05'}
    net.addLink(s3,s22,port1=4,port2=2,cls=TCLink , **s3s22)
            
    s4s5 = {'bw':300,'delay':'0.001'}
    net.addLink(s4, s5,port1=7,port2=4, cls=TCLink , **s4s5)
    s4s6 = {'bw':300,'delay':'0.001'}
    net.addLink(s4, s6,port1=9,port2=2, cls=TCLink , **s4s6)
    s4s7 = {'bw':300,'delay':'0.0205'}
    net.addLink(s4, s7, port1=6,port2=4,cls=TCLink , **s4s7)
    s4s9 = {'bw':300,'delay':'0.036'}
    net.addLink(s4, s9, port1=4,port2=6,cls=TCLink , **s4s9)
    s4s11 = {'bw':300,'delay':'0.16'}
    net.addLink(s4, s11,port1=3,port2=2, cls=TCLink , **s4s11)
    #s4s13 = {'bw':800,'delay':'0.065'}
    #net.addLink(s4, s13,port1=5,port2=3, cls=TCLink , **s4s13)
    
    s5s6 = {'bw':300,'delay':'0.001'}
    net.addLink(s5, s6,port1=3,port2=3, cls=TCLink , **s5s6)
    s5s7 = {'bw':300,'delay':'0.0205'}
    net.addLink(s5, s7, port1=7,port2=3,cls=TCLink , **s5s7)
    s5s8 = {'bw':300,'delay':'0.036'}
    net.addLink(s5, s8, port1=8,port2=2,cls=TCLink , **s5s8)
    s5s9 = {'bw':300,'delay':'0.036'}
    net.addLink(s5, s9,port1=6,port2=5, cls=TCLink , **s5s9)
        

    s7s8 = {'bw':300,'delay':'0.021'}
    net.addLink(s7, s8,port1=2,port2=3, cls=TCLink , **s7s8)
    s7s9 = {'bw':300,'delay':'0.021'}
    net.addLink(s7, s9,port1=5,port2=4, cls=TCLink , **s7s9)
    
    s8s14={'bw':300,'delay':'0.05'}
    net.addLink(s8,s14,port1=4,port2=2,cls=TCLink , **s8s14)

    s9S10 = {'bw':300,'delay':'0.035'}
    net.addLink(s9, s10,port1=3,port2=2, cls=TCLink , **s9S10)
    s9s13 = {'bw':300,'delay':'0.0415'}
    net.addLink(s9, s13, port1=2,port2=3,cls=TCLink , **s9s13)
    
    s10s14={'bw':300,'delay':'0.05'}
    net.addLink(s10,s14,port1=5,port2=4,cls=TCLink , **s10s14)
    s10s15={'bw':300,'delay':'0.05'}
    net.addLink(s10,s15,port1=4,port2=2,cls=TCLink , **s10s15)
    s10s16={'bw':300,'delay':'0.05'}
    net.addLink(s10,s16,port1=3,port2=2,cls=TCLink , **s10s16)
    
    s11s19={'bw':300,'delay':'0.05'}
    net.addLink(s11,s19,port1=4,port2=2,cls=TCLink , **s11s19)
    
    s12s13={'bw':300,'delay':'0.05'}
    net.addLink(s12,s13,port1=3,port2=2,cls=TCLink , **s12s13)
    s12s14={'bw':300,'delay':'0.05'}
    net.addLink(s12,s14,port1=2,port2=3,cls=TCLink , **s12s14)
    
    s13s17={'bw':300,'delay':'0.05'}
    net.addLink(s13,s17,port1=4,port2=2,cls=TCLink , **s13s17)
    s13s18={'bw':300,'delay':'0.05'}
    net.addLink(s13,s18,port1=5,port2=2,cls=TCLink , **s13s18)
    
    s14s15={'bw':300,'delay':'0.05'}
    net.addLink(s14,s15,port1=5,port2=3,cls=TCLink , **s14s15)
    
    
    
    
    
    net.addLink(s1,d1,port1=1)
    net.addLink(s2,d2,port1=1)
    net.addLink(s3,d3,port1=1)
    net.addLink(s4,d4,port1=1)
    net.addLink(s5,d5,port1=1)
    net.addLink(s6,d6,port1=1)
    net.addLink(s7,d7,port1=1)
    net.addLink(s8,d8,port1=1)
    net.addLink(s9,d9,port1=1)
    net.addLink(s10,d10,port1=1)
    net.addLink(s11,d11,port1=1)
    net.addLink(s12,d12,port1=1)
    net.addLink(s13,d13,port1=1)
    net.addLink(s14,d14,port1=1)
    
    net.addLink(s15,d15,port1=1)
    net.addLink(s16,d16,port1=1)
    net.addLink(s17,d17,port1=1)
    net.addLink(s18,d18,port1=1)
    net.addLink(s19,d19,port1=1)
    net.addLink(s20,d20,port1=1)
    net.addLink(s21,d21,port1=1)
    net.addLink(s22,d22,port1=1)
    


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s6').start([c0])
    net.get('s7').start([c0])
    net.get('s11').start([c0])
    net.get('s13').start([c0])
    net.get('S10').start([c0])
    net.get('s1').start([c0])
    net.get('s5').start([c0])
    net.get('s9').start([c0])
    net.get('s8').start([c0])
    net.get('s12').start([c0])
    net.get('s14').start([c0])
    
    net.get('s15').start([c0])
    net.get('s16').start([c0])
    net.get('s17').start([c0])
    net.get('s18').start([c0])
    net.get('s19').start([c0])
    net.get('s20').start([c0])
    net.get('s21').start([c0])
    net.get('s22').start([c0])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

