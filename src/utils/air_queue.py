import multiprocessing
from time import sleep
import os, sys, time
import logging
import coloredlogs

# Locals
dirname = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(dirname)

from src.models.icestupaClass import Icestupa
from src.utils.settings import config

# define worker function
def calculate(process_name, tasks, results):
    print("[%s] evaluation routine starts" % process_name)

    while True:
        new_value = tasks.get()
        if new_value == "None":
            print("[%s] evaluation routine quits" % process_name)

            # Indicate finished
            results.put(-1)
            break
        else:
            # Initialise icestupa object
            icestupa = Icestupa(*new_value)

            # Derive all the input parameters
            icestupa.gen_input()

            # Generate results
            icestupa.sim_air()

            # Summarise and save model results
            icestupa.gen_output()

            # Create figures for web interface
            icestupa.summary_figures()

            # Compute result and mimic a long-running task
            compute = icestupa.df.iceV.max()

            # Output which process received the value
            print("[%s] received value: %s" % (process_name, new_value))
            print("[%s] calculated max ice volume: %.1f" % (process_name, compute))

            # Add result to the queue
            results.put(compute)

    return


if __name__ == "__main__":
    # Main logger
    logger = logging.getLogger(__name__)
    logger.setLevel("ERROR")

    # Define IPC manager
    manager = multiprocessing.Manager()

    # Define a list (queue) for tasks and computation results
    tasks = manager.Queue()
    results = manager.Queue()
    # Create process pool with four processes
    num_processes = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_processes)
    processes = []
    # Initiate the worker processes
    for i in range(num_processes):

        # Set process name
        process_name = "P%i" % i

        # Create the process, and connect it to the worker function
        new_process = multiprocessing.Process(
            target=calculate, args=(process_name, tasks, results)
        )

        # Add new process to the list of processes
        processes.append(new_process)

        # Start the process
        new_process.start()

    # Fill task queue
    task_list = []
    locations = ["guttannen22", "guttannen21", "guttannen20", "gangles21"]
    # locations = [ "guttannen20", "gangles21"]
    # sprays = ["dynamic", "static", "manual"]
    sprays = ["dynamic", "static"]
    # sprays = ["auto"]

    for spray in sprays:
        for loc in locations:
             task_list.append([loc,spray])


    for single_task in task_list:
        tasks.put(single_task)

    # Wait while the workers process
    sleep(5)

    # Quit the worker processes by sending them -1
    for i in range(num_processes):
        tasks.put("None")

    # Read calculation results
    num_finished_processes = 0

    while True:
        # Read result
        new_result = results.get()

        # Have a look at the results
        if new_result == -1:
            # Process has finished
            num_finished_processes += 1

            if num_finished_processes == num_processes:
                break
