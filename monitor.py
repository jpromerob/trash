import multiprocessing
import argparse
import time
import time


from stimulation import *

def parse_args():


    parser = argparse.ArgumentParser(description='Generator of Synthetic Events')
    

    # General parameters
    parser.add_argument('-w', '--width', type=int, help="Image size (in px)", default=16)

    # Stimulation Parameters
    parser.add_argument('-l', '--len', type=int, help="length of activity square", default=16)
    parser.add_argument('-x', '--cx', type=int, help="x coordinate of top left corner", default=0)
    parser.add_argument('-y', '--cy', type=int, help="y coordinate of top left corner", default=0)
    parser.add_argument('-z', '--zzz', type=int, help="sleep time ms", default=20)
    
    # SPIF Parameters
    parser.add_argument('-i', '--ip', type= str, help="SPIF's IP address", default="172.16.222.199")
    parser.add_argument('-p', '--port', type=int, help="SPIF's port", default=3331)
    parser.add_argument('-s', '--simulate-spif', action="store_true", help="Simulate SPIF")


    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    manager = multiprocessing.Manager()
    end_of_sim = manager.Value('i', 0)
    output_q = multiprocessing.Queue() # events


    stim = Stimulator(args, end_of_sim)

    with stim:
        time.sleep(5)


