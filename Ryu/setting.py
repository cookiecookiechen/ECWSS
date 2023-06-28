# -*- coding:utf-8 -*-

import socket 
import re
import threading


    
DISCOVERY_PERIOD = 600  # 

MONITOR_PERIOD = 30#

DELAY_DETECTING_PERIOD = 1.5  


TOSHOW = False  

MAX_CAPACITY = 30000000  # Max capacity of link (kbit/s)

    
SHOW_Path_Selection = False



idle_timeout = 0
hard_timeout = 0

m = 3 
k = 5  # best k path



