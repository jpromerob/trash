import numpy
import math
import pyNN.spiNNaker as p
import pdb

def make_kernel_circle(r, weight, kernel):
    a = numpy.arange(0, 2 * math.pi, 0.01)
    dx = numpy.round(r * numpy.sin(a)).astype("uint32")
    dy = numpy.round(r * numpy.cos(a)).astype("uint32")
    kernel[20 + dx, 20 + dy] = weight


WIDTH = 640
HEIGHT = 480
SUB_WIDTH = 16
SUB_HEIGHT = 8
SPIF_IP = "172.16.222.199"
SPIF_PORT = 3331
POP_LABEL = "target"
RUN_TIME = 1000*20
CHIP = (0, 0)

kernel = numpy.zeros((39, 39))
make_kernel_circle(18, 0.8, kernel)
make_kernel_circle(16, -1.0, kernel)
make_kernel_circle(14, 0.8, kernel)
make_kernel_circle(10, -1.0, kernel)

for x in range(len(kernel)):
    print(list(kernel[x]))

convolution = p.ConvolutionConnector(kernel_weights=kernel)
out_width, out_height = convolution.get_post_shape((WIDTH, HEIGHT))

print(f"Output {out_width} x {out_height}")


def recv(label, spikes):
    np_spikes = numpy.array(spikes)
    xs = np_spikes // out_height
    ys = np_spikes - (xs * out_height)
    for x, y in zip(xs, ys):
        print(x, y)


conn = p.external_devices.SPIFLiveSpikesConnection(
    [POP_LABEL], SPIF_IP, SPIF_PORT)
conn.add_receive_callback(POP_LABEL, recv)


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

