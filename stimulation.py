
import multiprocessing
import socket
import pdb
import math
import sys
import datetime
import time
import numpy as np
import random
from struct import pack
import os
import ctypes
from time import sleep
import pyNN.spiNNaker as p



# An event frame has 32 bits <t[31]><x [30:16]><p [15]><y [14:0]>
P_SHIFT = 15
Y_SHIFT = 0
X_SHIFT = 16

class Stimulator:
    def __init__(self, args, end_of_sim):
        self.display = []
        self.ip_addr = args.ip
        self.spif_port = args.port
        self.width = args.width
        self.height = self.width # int(math.ceil(args.width*3/4))
        self.zzz = args.zzz
        self.cx = args.cx
        self.cy = args.cy
        self.len = min(int(args.len), int(args.width))
        self.input_q = multiprocessing.Queue()
        self.end_of_sim = end_of_sim
        self.use_spif = not args.simulate_spif
        self.running = multiprocessing.Value(ctypes.c_bool)
        self.running.value = False
        self.port = multiprocessing.Value(ctypes.c_uint32)
        self.port.value = 0
        self.ev_count = 0
        self.start_t = 0

        self.p_i_data = multiprocessing.Process(target=self.set_inputs_classic, args=())
        self.p_stream = multiprocessing.Process(target=self.launch_input_handler, args=())
        self.p_stream.start()
        if not self.use_spif:
            while self.port.value == 0:
                sleep(0.1)

    def start_handler(self, label, connection):
        self.running.value = True

    def end_handler(self, label, connection):
        self.running.value = False

    def __enter__(self):
        # self.p_i_data.start()
        a = 1

    def __exit__(self, e, b, t):
        self.end_of_sim.value = 1
        # self.p_i_data.join()
        self.p_stream.join()

    def generate_events(self, cx, cy):
        
        events = []
        for x in range(self.len):
            for y in range(self.len):
                events.append((cx + x, cy + y))
        
        return events

    # This function is in charge of adding lists of events to buffer
    def set_inputs_sweep(self):

        while self.end_of_sim.value == 0:  
            it_x = int(self.width/2/self.len)
            it_y = int(self.height/2/self.len)
            for iy in range(it_y):
                cy = self.len*iy
                for ix in range(it_x):
                    cx = self.len*ix
                    events = self.generate_events(cx, cy)
                    self.input_q.put(events)
                    time.sleep(self.zzz/1000)
        print("No more inputs to be sent")
        
    # This function is in charge of adding lists of events to buffer
    def set_inputs_noise(self):
        while self.end_of_sim.value == 0:  
            array_sz = self.len**2
            x_array = np.random.randint(self.width, size=array_sz)
            y_array = np.random.randint(self.height, size=array_sz)
            
            events = []
            for i in range(array_sz):
                events.append((x_array[i], y_array[i]))
            
            self.input_q.put(events)
            time.sleep(self.zzz/1000)

        print("No more inputs to be sent")

    # This function is in charge of adding lists of events to buffer
    def set_inputs_classic(self):
        while self.end_of_sim.value == 0:  
            events = []
            for x in range(self.len):
                for y in range(self.len):
                    events.append((self.cx + x, self.cy + y))
            self.input_q.put(events)
            time.sleep(self.zzz/1000)
            
    def get_inputs_classic(self):
        
        while self.end_of_sim.value == 0:  
            for x in range(self.len):
                for y in range(self.len):
                    yield(self.cx + x, self.cy + y)
            
        print("No more inputs to be sent")

    
    # This function is in charge of adding lists of events to buffer
    def get_inputs_noise(self):
        while self.end_of_sim.value == 0:  
            x = np.random.randint(self.width, size=1)[0]
            y = np.random.randint(self.height, size=1)[0]
            yield(x,y)

        print("No more inputs to be sent")

    # This function is in charge of cerating UDP event frames and send them to SPIF
    def launch_input_handler(self):

        NO_TIMESTAMP = 0x80000000
        polarity = 1

        looking_for_first_ev = True

        if self.use_spif:
            print(f"Using SPIF on {self.ip_addr}:{self.spif_port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            connection = p.external_devices.SpynnakerLiveSpikesConnection(send_labels=["retina"], local_port=None)
            self.port.value = connection.local_port
            connection.add_start_resume_callback("retina", self.start_handler)
            connection.add_pause_stop_callback("retina", self.end_handler)

        ev_source_classic = self.get_inputs_classic()
        ev_source_noise = self.get_inputs_noise()
        
        pack_sz = 16*16
        while self.end_of_sim.value == 0:
            
            if not self.use_spif and not self.running.value:
                continue

            if self.use_spif:
                data = b""
            else:
                spikes = []

            for idx in range(pack_sz):
                
                if looking_for_first_ev:
                    looking_for_first_ev = False
                    self.start_t = time.time()
                if self.ev_count%1000 == 0:
                    e = next(ev_source_noise)    
                else:
                    e = next(ev_source_classic)
                x = e[0]
                y = e[1]
                self.ev_count += 1
                if self.use_spif:

                    packed = (
                        NO_TIMESTAMP + (polarity << P_SHIFT) +
                        (y << Y_SHIFT) + (x << X_SHIFT))
                    data += pack("<I", packed)
                else:
                    spikes.append((y * self.width) + x)

            if self.use_spif:
                sock.sendto(data, (self.ip_addr, self.spif_port))
                
            elif spikes:
                connection.send_spikes("retina", spikes)

        if self.use_spif:
            diff_t = round(time.time() - self.start_t,3)
            print(f"{self.ev_count} events sent in {diff_t} seconds")
            print(f"{int(self.ev_count/diff_t)} ev/sec")
            sock.close()
        else:
            connection.close()
        print("No more events to be created")


