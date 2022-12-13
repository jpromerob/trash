
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
        self.w = args.width
        self.zzz = args.zzz
        self.len = int(args.len)
        self.h = self.w + 0*int(math.ceil(args.width*3/4))
        self.input_q = multiprocessing.Queue()
        self.end_of_sim = end_of_sim
        self.use_spif = not args.simulate_spif
        self.monitor = args.monitor
        self.running = multiprocessing.Value(ctypes.c_bool)
        self.running.value = False
        self.port = multiprocessing.Value(ctypes.c_uint32)
        self.port.value = 0
        self.ev_count = 0
        self.start_t = 0

        self.p_i_data = multiprocessing.Process(target=self.set_inputs, args=())
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
        self.p_i_data.start()

    def __exit__(self, e, b, t):
        self.end_of_sim.value = 1
        self.p_i_data.join()
        self.p_stream.join()

    def generate_events(self, cx, cy, l):
        
        events = []
        for x in range(l):
            for y in range(l):
                events.append((x+cx, y+cy))
        
        return events

    # This function is in charge of adding lists of events to buffer
    def set_inputs(self):

        if self.monitor:
            print("Monitor!!!")
            time.sleep(1)
        else:
            time.sleep(4)
            print("\n\n\n")
            print("Waking up")
            print("\n\n\n")
            time.sleep(1)



        # ev_per_pack = 1
        # delta_t = (self.zzz/1000)/(self.w*self.h)*ev_per_pack
        # while self.end_of_sim.value == 0:            
            
        #     events = []
        #     ev_count = 0
        #     for x in range(self.w): 
        #         for y in range(self.h):  
        #             events.append((0,0))
        #             ev_count +=1 
        #             if(ev_count >= ev_per_pack):
        #                 self.input_q.put(events)
        #                 events = []
        #                 ev_count = 0
        #                 time.sleep(delta_t)

        # print("No more inputs to be sent")

        while self.end_of_sim.value == 0:  
            events = []
            for x in range(self.len):
                for y in range(self.len):
                    events.append((x, y))
            self.input_q.put(events)
            time.sleep(self.zzz/1000)
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

        while self.end_of_sim.value == 0:
            events = []
            available_data = False
            while not self.input_q.empty():
                if looking_for_first_ev:
                    looking_for_first_ev = False
                    self.start_t = time.time()
                events = self.input_q.get(False)
                available_data = True

            if not self.use_spif and not self.running.value:
                continue

            if self.use_spif:
                data = b""
            else:
                spikes = []

            for e in events:
                x = e[0]
                y = e[1]
                self.ev_count += 1
                if self.use_spif:

                    packed = (
                        NO_TIMESTAMP + (polarity << P_SHIFT) +
                        (y << Y_SHIFT) + (x << X_SHIFT))
                    data += pack("<I", packed)
                else:
                    spikes.append((y * self.w) + x)

            if self.use_spif:
                if available_data:
                    sock.sendto(data, (self.ip_addr, self.spif_port))
                    # if self.ev_count%1000 == 0:
                    #     print(f"Event #{self.ev_count}  sent")
                    available_data = False
                
            elif spikes:
                connection.send_spikes("retina", spikes)

        print("No more events to be created")
        if self.use_spif:
            print(f"start: {self.start_t}")
            print(f"end: {time.time()}")
            diff_t = (time.time() - self.start_t)
            print(f"{self.ev_count} events sent in {diff_t} seconds")
            print(f"{self.ev_count/diff_t} ev/sec")
            sock.close()
        else:
            connection.close()


