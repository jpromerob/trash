
import multiprocessing
import time



class Counter:

    def __init__(self, args, labels, output_q, end_of_sim):
        self.labels = labels
        self.n = len(labels)
        self.output_q = output_q
        self.end_of_sim = end_of_sim
        self.p_o_data = multiprocessing.Process(target=self.get_outputs, args=())

    def __enter__(self):
        self.p_o_data.start()

    def __exit__(self, e, b, t):
        self.end_of_sim.value = 1
        self.p_o_data.join()

    def get_outputs(self):
        
        print("Starting to count some stuff\n")

        # ev_counter = 0
        while self.end_of_sim.value == 0:
            while not self.output_q.empty():
                out = self.output_q.get(False)
                # ev_counter += 1
                # print(f"Event #{ev_counter} received ...")



        print("No more outputs to be received")


    
