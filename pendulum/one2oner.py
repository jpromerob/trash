import numpy as np
import math
import pyNN.spiNNaker as p
import pdb
import socket
from struct import pack
import matplotlib.pyplot as plt



SUB_WIDTH = 16
SUB_HEIGHT = 8
# WIDTH = 640
# HEIGHT = int(WIDTH*3/4)

WIDTH = 300
HEIGHT = WIDTH



SPIF_IP = "172.16.223.2"
SPIF_PORT = 3332
MY_PC_IP = "172.16.222.199"
MY_PC_PORT = 3331
POP_LABEL = "target"
RUN_TIME = 1000*60*20
CHIP = (0, 0)

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
                        # print(f"{lut_ix} -> ({x},{y})")
                        lut[lut_ix] = [x,y]
                        lut_ix += 1

        
    return lut

kernel = np.ones((2, 2))*0.1


for x in range(len(kernel)):
    print(list(kernel[x]))

convolution = p.ConvolutionConnector(kernel_weights=kernel)
out_width, out_height = convolution.get_post_shape((WIDTH, HEIGHT))

print(f"Output {out_width} x {out_height}")

# pdb.set_trace()

P_SHIFT = 15
Y_SHIFT = 0
X_SHIFT = 16
NO_TIMESTAMP = 0x80000000


global sock 
global lut
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lut = create_lut(out_width, out_height, SUB_WIDTH, SUB_HEIGHT)


def recv(label, spikes):
    global sock
    data = b""
    np_spikes = np.array(spikes)
    xs = np_spikes // out_height
    ys = np_spikes - (xs * out_height)
    for x, y in zip(xs, ys):
        polarity = 1
        packed = (NO_TIMESTAMP + (polarity << P_SHIFT) + (y << Y_SHIFT) + (x << X_SHIFT))
        data += pack("<I", packed)
    sock.sendto(data, (MY_PC_IP, MY_PC_PORT))


def recv_nid(label, spikes):
    global sock
    global lut
    data = b""
    np_spikes = np.array(spikes)
    # print(np_spikes.shape)
    for i in range(np_spikes.shape[0]):
        x = lut[np_spikes[i]][0]
        y = lut[np_spikes[i]][1]
        polarity = 1
        # print(f"{np_spikes[i]} --> ({lut[np_spikes[i]][0]}, {lut[np_spikes[i]][1]})")
        packed = (NO_TIMESTAMP + (polarity << P_SHIFT) + (y << Y_SHIFT) + (x << X_SHIFT))
        data += pack("<I", packed)
    sock.sendto(data, (MY_PC_IP, MY_PC_PORT))



conn = p.external_devices.SPIFLiveSpikesConnection(
    [POP_LABEL], SPIF_IP, SPIF_PORT)
conn.add_receive_callback(POP_LABEL, recv_nid)


p.setup(timestep=1.0, n_boards_required=24)
# p.setup(1)
p.set_number_of_neurons_per_core(p.IF_curr_exp, (SUB_WIDTH, SUB_HEIGHT))

spif_retina = p.Population(
    WIDTH * HEIGHT, p.external_devices.SPIFRetinaDevice(
        pipe=0, width=WIDTH, height=HEIGHT,
        sub_width=SUB_WIDTH, sub_height=SUB_HEIGHT, chip_coords=CHIP),
    label="retina")

target_pop = p.Population(
    out_width * out_height, p.IF_curr_exp(),
    structure=p.Grid2D(out_width / out_height), label=POP_LABEL)
# target_pop.record("spikes")

p.Projection(spif_retina, target_pop, convolution, p.Convolution())

spif_output = p.Population(None, p.external_devices.SPIFOutputDevice(
    database_notify_port_num=conn.local_port, chip_coords=CHIP), label="output")
p.external_devices.activate_live_output_to(target_pop, spif_output)

# pdb.set_trace()

p.run(RUN_TIME)
# spikes = target_pop.get_data("spikes").segments[0].spiketrains
# for i, s in enumerate(spikes):
#     if len(s):
#         x = i // out_height
#         y = i - (x * out_height)
#         print(f"{x}, {y}: {s}")
p.end()

