
import multiprocessing
import argparse
import sys, os, time
import pdb
import time

#toto

from evaluation import *
from stimulation import *
from computation import *


def parse_args():


    parser = argparse.ArgumentParser(description='SpiNNaker-SPIF Simulation with Artificial Data')

    parser.add_argument('-d', '--dimensions', type=int, help="Dimensions (1D, 2D)", default=2)
    parser.add_argument('-f', '--fov', type=int, help="w fovea", default=8)
    parser.add_argument('-i', '--ip', type= str, help="SPIF's IP address", default="172.16.223.10")
    parser.add_argument('-l', '--len', type=int, help="length of activity square", default=1)
    parser.add_argument('-m', '--monitor', action="store_true", help="Monitor Stimulation")
    parser.add_argument('-n', '--npc', type=int, help="# Neurons Per Core", default=4)
    parser.add_argument('-p', '--port', type=int, help="SPIF's port", default=3333)
    parser.add_argument('-r','--runtime', type=int, help="Run Time, in seconds", default=20)
    parser.add_argument('-s', '--simulate-spif', action="store_true", help="Simulate SPIF")
    parser.add_argument('-t', '--tau', type=int, help="tau_m", default=20)
    parser.add_argument('-v', '--vth', type=int, help="v_th", default=-50)
    parser.add_argument('-w', '--width', type=int, help="Image size (in px)", default=16)
    parser.add_argument('-z', '--zzz', type=int, help="sleep time ms", default=4)


    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    manager = multiprocessing.Manager()
    end_of_sim = manager.Value('i', 0)
    output_q = multiprocessing.Queue() # events


    stim = Stimulator(args, end_of_sim)
    # spin = Computer(args, output_q, stim.port.value)
    # cntr = Counter(args, spin.labels, output_q, end_of_sim)


    with stim:
        time.sleep(30)


