
import multiprocessing
import socket
import pdb
import math
import sys
import os
import datetime
import time
import numpy as np
import random
from struct import pack

# SpiNNaker imports
import pyNN.spiNNaker as p
from pyNN.space import Grid2D

PORT_SPIN2CPU = int(random.randint(12000,15000))




'''
This function creates a list of weights to be used when connecting pixels to motor neurons
'''
def create_weight_list(w_fovea, w, h):

    weight_list = []

    for y in range(h):
        for x in range(w):
            for post_idx in range(4):
                weight = 0.00001
                if post_idx == 0 and x == 0 and y == 0:
                    weight = w_fovea
                weight_list.append(weight)

    return weight_list


class Computer:

    def __init__(self, args, output_q, database_port):
        self.run_time = int(args.runtime)*1000 # in [ms]
        self.w_fovea = args.fov
        self.width = args.width
        self.height = math.ceil(self.width*3/4)
        self.pipe = args.port-3333
        self.chip_coords = (0,0)
        self.x_shift = 16
        self.y_shift = 0
        self.output_q = output_q
        self.subheight = 2
        self.subwidth = 2*self.subheight
        self.nb_neurons_core = args.npc
        self.dimensions = args.dimensions
        self.celltype = p.IF_curr_exp
        self.tau = args.tau
        self.vth = args.vth
        self.cell_params = {'tau_m': self.tau,
                            'tau_syn_E': 5.0,
                            'tau_syn_I': 5.0,
                            'v_rest': -65.0,
                            'v_reset': -65.0,
                            'v_thresh': self.vth,
                            'tau_refrac': 0.0, # 0.1 originally
                            'cm': 1,
                            'i_offset': 0.0
                            }
        self.labels = ["go_right", "go_left", "go_up", "go_down"]
        self.database_port = database_port
        self.use_spif = not args.simulate_spif
        self.ev_counter = 0

    def __enter__(self):

        # Set up PyNN
        p.setup(timestep=1.0, n_boards_required=1)

        # Set the number of neurons per core
        if self.dimensions == 1:
            p.set_number_of_neurons_per_core(p.IF_curr_exp, self.nb_neurons_core)

        if self.dimensions == 2:
            p.set_number_of_neurons_per_core(p.IF_curr_exp, (self.nb_neurons_core, self.nb_neurons_core))

        # Set SPIF
        if self.use_spif:
            dev = p.Population(None, p.external_devices.SPIFRetinaDevice(
                pipe=self.pipe, width=self.width, height=self.height, sub_width=self.subwidth,
                sub_height=self.subheight, input_x_shift=self.x_shift, input_y_shift=self.y_shift,
                chip_coords=self.chip_coords, base_key=None, board_address=None))
        else:
            dev = p.Population(self.width * self.height, p.external_devices.SpikeInjector(
                database_notify_port_num=self.database_port), label="retina",
                structure=Grid2D(self.width / self.height))

        pool_shape = (4,3)
        post_w, post_h = p.PoolDenseConnector.get_post_pool_shape((self.width, self.height), pool_shape)
        weights = np.array(create_weight_list(self.w_fovea, post_w, post_h))
        motor_conn = p.PoolDenseConnector(weights, pool_shape)
        motor_neurons = p.Population(len(self.labels), self.celltype(**self.cell_params), label="motor_neurons")
        con_move = p.Projection(dev, motor_neurons, motor_conn, p.PoolDense())

        # Spike reception (from SpiNNaker to CPU)
        live_spikes_receiver = p.external_devices.SpynnakerLiveSpikesConnection(receive_labels=["motor_neurons"], local_port=PORT_SPIN2CPU)
        _ = p.external_devices.activate_live_output_for(motor_neurons, database_notify_port_num=live_spikes_receiver.local_port)
        live_spikes_receiver.add_receive_callback("motor_neurons", self.receive_spikes_from_sim)

    def __exit__(self, e, b, t):
        p.end()

    def receive_spikes_from_sim(self, label, time, neuron_ids):

        for n_id in neuron_ids:
            self.ev_counter += 1
            if n_id == 0:
                print(f"Spike --> MN[{n_id}]")
            self.output_q.put(n_id, False)

    def run_sim(self):
        p.run(self.run_time)
        print(f"{self.ev_counter} events were output")
        # p.external_devices.run_forever(sync_time=0)

    def wrap_up(self):
        time.sleep(1)
        # Get recordings from populations (in case they exist)