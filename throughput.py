
import multiprocessing
import argparse
import sys, os, time
import pdb
import time
import matplotlib.pyplot as plt

#toto

from evaluation import *
from stimulation import *
from computation import *


def parse_args():

    parser = argparse.ArgumentParser(description='SpiNNaker-SPIF Simulation with Artificial Data')

    # General parameters
    parser.add_argument('-w', '--width', type=int, help="Image size (in px)", default=16)
    parser.add_argument('-r', '--runtime', type=int, help="Run Time, in seconds", default=2)

    # Stimulation Parameters
    parser.add_argument('-l', '--len', type=int, help="length of activity square", default=4)
    parser.add_argument('-x', '--cx', type=int, help="x coordinate of top left corner", default=0)
    parser.add_argument('-y', '--cy', type=int, help="y coordinate of top left corner", default=0)
    parser.add_argument('-z', '--zzz', type=int, help="sleep time ms", default=20)

    # SPIF Parameters
    parser.add_argument('-i', '--ip', type= str, help="SPIF's IP address", default="172.16.223.2")
    parser.add_argument('-p', '--port', type=int, help="SPIF's port", default=3333)
    parser.add_argument('-s', '--simulate-spif', action="store_true", help="Simulate SPIF")

    # Computation Parameters
    parser.add_argument('-d', '--dimensions', type=int, help="Dimensions (1D, 2D)", default=2)
    parser.add_argument('-f', '--fov', type=float, help="w fovea", default=4.8)
    parser.add_argument('-n', '--npc', type=int, help="# Neurons Per Core", default=16)
    parser.add_argument('-o', '--pool', type=int, help="Pool size", default=0)
    parser.add_argument('-q', '--board-quantity', type=int, help="boards required", default=1)
    parser.add_argument('-t', '--tau', type=int, help="tau_m", default=20)
    parser.add_argument('-v', '--vth', type=int, help="v_th", default=-50)

    
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    manager = multiprocessing.Manager()
    end_of_sim = manager.Value('i', 0)
    output_q = multiprocessing.Queue() # events


    stim = Stimulator(args, end_of_sim)
    spin = Computer(args, output_q, stim.port.value)
    cntr = Counter(args, spin.labels, output_q, end_of_sim)


    with spin:
        with stim:
            with cntr:

                spin.run_sim()
                end_of_sim.value = 1 # Let other processes know that simulation stopped
                spin.wrap_up()
    



    ##################################################################################################
    #                                           SOME PLOTTING
    ##################################################################################################
    
    vrst = -65
    fig, axs = plt.subplots(4, figsize=(8, 8))
    for i in range(4):
        sample = spin.voltages[i]
        axs[i].plot(spin.voltages[i])                
        
        axs[i].set_xlabel('Time')
        axs[i].set_ylabel('V_m')

        axs[i].set_ylim([vrst-5, args.vth+5])
        axs[i].set_xlim([0,min(2000, len(sample))])
        axs[i].grid()
    
    fig.suptitle(f"l: {min(args.len, args.width)} | f: {args.fov} | w: {args.width}  | o: {args.pool} | z: {args.zzz} | x: {args.cx} | y: {args.cy}")
    
    plt.show()


    # spikes_displayed = 8
    # sample = spin.voltages[0]
    # idx = []
    # spike_count = 0
    # for i in range(len(sample)-3):
    #     if abs(sample[i] - sample[i+1]) > 0.8*(args.vth-vrst):
    #         idx.append(i+2)
    #         spike_count += 1
    #         if spike_count >= spikes_displayed:
    #             break
    
    # if len(idx) > 0:
    #     idx = np.flip(np.asarray(idx))
    #     for j in range(len(idx)):
    #         plt.plot(sample[0:idx[j]])
    #         plt.xlim(0,np.max(idx))
    # else:
    #     plt.xlim(0,min(200, len(sample)))
    
    # plt.ylim(vrst-5, args.vth+5)
    # plt.grid()
    # plt.show()
