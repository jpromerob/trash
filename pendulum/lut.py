
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
def create_lut(w, h, sw, sh):
    

    delay = 1 # 1 [ms]
    nb_col = math.ceil(w/sw)
    nb_row = math.ceil(h/sh)

    lut = np.zeros((w*h,2), dtype='uint16')

    lut_ix = 0
    for h_block in range(nb_row):
        for v_block in range(nb_col):
            for row in range(sh):
                for col in range(sw):
                    x = v_block*sw+col
                    y = h_block*sh+row
                    if x<w and y<h:
                        print(f"{lut_ix} -> ({x},{y})")
                        lut[lut_ix] = [x,y]
                        lut_ix += 1

        
    return lut


SUB_WIDTH = 8
SUB_HEIGHT = 4
WIDTH = 48
HEIGHT = WIDTH

if __name__ == '__main__':

    lut = create_lut(WIDTH, HEIGHT, SUB_WIDTH, SUB_HEIGHT)
    pdb.set_trace()
    