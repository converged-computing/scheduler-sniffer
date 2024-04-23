#!/usr/bin/env python3

import argparse
import random
import copy
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime

from jinja2 import Template
from kubernetes import client, config, watch

here = os.path.dirname(os.path.abspath(__file__))

# Hard coded experiment templates
job_template = os.path.join(here, "crd", "job.yaml")

mixed_config = [
    {"cpu_limit": 1, "size": 2},
    {"cpu_limit": 1, "size": 3},
    {"cpu_limit": 1, "size": 4},
    {"cpu_limit": 1, "size": 5},
    {"cpu_limit": 1, "size": 6},
]

# Pair up configs and named templates
configs = {
    "mixed": {"config": mixed_config, "template": job_template},
}

# This must work to continue
config.load_kube_config()
kube_client = client.CoreV1Api()

# Try using a global watcher
watcher = watch.Watch()


def write_file(content, filename):
    """
    Write content to file.
    """
    with open(filename, "w") as fd:
        fd.write(content)


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def get_cluster_config(logfile):
    """
    Get cluster node configuration and build
    the zone topology map.
    """
    cluster_nodes = kube_client.list_node()
    nodes = cluster_nodes.to_str()
    write_file(nodes, logfile)

    # Assemble topology that includes nodes
    # Note that I removed memory and cpu, manually defining them could be erroneous
    node_topology = {"nodes": {}}
    for node in cluster_nodes.items:
        # Mock for local testing, this label won't be in a kind cluster
        label = "local"
        if "topology.kubernetes.io/zone" in node.metadata.labels:
            label = node.metadata.labels["topology.kubernetes.io/zone"]
        node_topology["nodes"][node.metadata.name] = label
    return node_topology


def submit_job(job_yaml):
    """
    Create the job in Kubernetes.
    """
    fd, filename = tempfile.mkstemp(suffix=".yaml", prefix="job-")
    os.remove(filename)
    os.close(fd)
    write_file(job_yaml, filename)

    # Create the job
    o, e = run_command(["kubectl", "apply", "-f", filename])
    os.remove(filename)


def run_command(command, allow_fail=False):
    """
    Call a command to subprocess, return output and error.
    """
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    o, e = p.communicate()
    print(o)
    if p.returncode and not allow_fail:
        print(e)
        print(f"WARNING error in subprocess: {e}")
    return o, e


def delete_job(uid):
    """
    Deletea job by name.
    """
    # --wait=true is default, but I want to be explicit
    run_command(["kubectl", "delete", "job", uid, "--wait=true"])


def delete_podgroup(uid):
    """
    Delete the podgroup
    """
    run_command(["kubectl", "delete", "podgroup", uid], allow_fail=True)


def delete_service(uid):
    """
    Delete the service
    """
    run_command(["kubectl", "delete", "service", uid], allow_fail=True)


def record_line(filename, status, content):
    """
    Record (write with append) one entry to a file.
    """
    with open(filename, "a") as f:
        f.write(f"\n===\n{status}: recorded-at: {datetime.utcnow()}\n{content}")


def get_namespace_logs(pod_name, namespace):
    """
    Get logs for a pod in a namespace.

    This doesn't watch (stream) but assumes we are done.
    """
    config.load_kube_config()
    kube_client = client.CoreV1Api()
    return kube_client.read_namespaced_pod_log(name=pod_name, namespace=namespace)


def get_pod_mapping(uid, pods, scheduler, node_topology):
    """
    Get the pod topology based on node assignment, format into
    string to save back to log.
    """
    mapping = f"Mapping for job {uid} for scheduler {scheduler}\n"
    mapping_dict = defaultdict(int)
    for pod in pods.items:
        mapping_dict[pod.spec.node_name] += 1
        mapping += f"{pod.metadata.name} --> {pod.spec.node_name}\n"
    for worker_name, count in mapping_dict.items():
        mapping += f"{worker_name} ran {str(count)} pods in zone "
        mapping += f"{node_topology['nodes'][worker_name]}\n"
    return mapping


def get_run_configuration(uid, meta, node_topology):
    """
    The run configuration is a json dump of metadata
    plus snippets of the node_topology.
    """
    rconfig = f"Run configuration for job {uid}:\n===\n"
    rconfig += json.dumps(meta, indent=4) + "\n====\n"
    return rconfig


def get_logs(uid, meta, submit_time, batch_end_time, log_dir, node_topology):
    """
    Get the application mapping and performance logs
    """
    log_file = os.path.join(log_dir, f"{uid}.log")

    # scheduler is in meta->params or we assume default
    scheduler = meta["params"].get("scheduler") or "default"

    # Find pods for job
    label = meta["params"]["name"]

    # Start time is based on first running
    start_time = None

    # And then the 0th index (leader) and the rest are workers
    # We don't have success policy so we are watching the leader complete
    # and then cleaning up the workers
    zero_index = f"{label}-0"

    # Only the index 0 is timing, the rest are sleeping
    keep_going = True
    while keep_going:
        pods = kube_client.list_namespaced_pod(
            label_selector=f"app={label}", namespace="default"
        )
        # Phases here:
        phases = [x.status.phase for x in pods.items]

        # This is just an estimate of running based on seeing the first pod running
        # We can do better to get a timestamp, I'm just testing now
        if start_time is None and "Running" in phases or "Succeeded" in phases:
            start_time = datetime.utcnow()
        elif (
            "Running" not in phases
            and "Succeeded" not in phases
            and "Failed" not in phases
        ):
            continue

        leader = [x for x in pods.items if x.metadata.name.startswith(zero_index)]
        if leader:
            leader = leader[0]
            print(f"Found leader pod {leader.metadata.name} to watch 👀️")
            if leader.status.phase in ["Succeeded", "Failed"]:
                print(f"Leader pod {leader.metadata.name} is done")
                keep_going = False

    log = get_namespace_logs(leader.metadata.name, namespace="default")

    # Record the end time for getting all pods to our file
    end_time = datetime.utcnow()

    # It's important to get here otherwise we are accounting for events!

    record_line(log_file, "Output", log)

    # Calculate the end time
    total_time = (end_time - start_time).total_seconds()

    # Time to run is submit to completion
    time_to_run = (end_time - submit_time).total_seconds()

    times = {
        "end_time": str(end_time),
        "start_time": str(start_time),
        "batch_done_submit_time": str(batch_end_time),
        "submit_time": str(submit_time),
        "submit_to_completion": time_to_run,
        "total_time": total_time,
        "uid": uid,
    }
    record_line(log_file, "Times", json.dumps(times))
    name = meta["params"]["name"]

    # We need to delete the job because pods 1-N will remain running
    delete_job(name)

def process_error_handler(e):
    """
    A simple process that prints and raises the error.
    """
    print(e)
    raise e


def save_pod_events(events_file, label, leader):
    """
    Get events for a pod based on a label

    TODO: we aren't currently using this because it didn't reliably
    return events, need to look into why.
    """
    # These should be able to get them after the pod finishes
    # Do we need these events, want to compare with the ones below?
    # This gets pod events, and then events for the leader (scheduler too)
    pod_events = []
    for event in watcher.stream(
        kube_client.list_namespaced_event,
        "default",
        label_selector=f"app={label}",
        timeout_seconds=10,
    ):
        pod_events.append(event)
    print(f"Events for pod {label}: {len(pod_events)}")
    events_dump = json.dumps([x["raw_object"] for x in pod_events], indent=4)
    record_line(events_file, "PodEvents", events_dump)


def run(args, config_name, node_topology):
    """
    Run the experiments for the input apps.

    This is going to basically launch a crapton of experiments to run, much more than the
    scheduler can handle at once, and then we will monitor what it does. This script needs
    to be run twice, once with fluence and one without (one with the default scheduler)
    """
    # Unwrap arguments
    batches = args.batches
    iters = args.iters
    outdir = args.outdir

    # If we are using fluence we need to add this to the Minicluster CRD to add to the Pod
    scheduler = "sniffer"

    # Read in the template once
    experiment = configs[config_name]
    cfgs = experiment["config"]
    template = Template(read_file(experiment["template"]))

    # Keep record of all specs across batches
    specs = {}

    # Make a directory for the logs
    log_dir = os.path.join(outdir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Keep raw submit times
    submit_times = {}

    # Prepare jobs in advance

    # For each batch
    for b in range(batches):
        # Keep a record of the uids we submit for this batch
        batch = set()

        for i in range(iters):
            # Do we want to shuffle jobs?
            if args.shuffle:
                random.shuffle(cfgs)

            for cfg in cfgs:
                size = cfg["size"]

                # uid is the iteration, size, x,y,z and scheduler
                uid = f"{scheduler}-batch-{b}-iter-{i}-size-{size}"
                batch.add(uid)

                # name is just the batch, iteration, and size
                job_name = f"job-{b}-{i}-size-{size}"

                # The flux service needs to be unique for the minicluster
                service_name = f"s{i}{b}{size}"

                print(f"Starting job {uid}: {cfg}")
                render = copy.deepcopy(cfg)
                render.update(
                    {
                        "name": job_name,
                        "size": size,
                        "size_range": " ".join([str(x) for x in range(0, size)]),
                        "service_name": service_name,
                        "scheduler": scheduler,
                        "address": args.address,
                    }
                )

                # TODO: what else do we want to save here?
                specs[uid] = {"params": render, "iter": i}

                # Generate and submit the template...
                job_yaml = template.render(render)
                print(job_yaml)

                # This submits the job, doesn't do more than that (e.g., waiting)
                submit_time = datetime.utcnow()
                submit_job(job_yaml)
                specs[uid]["submit_time"] = str(submit_time)
                submit_times[uid] = submit_time

        # END of size loop
        batch_end_time = datetime.utcnow()

        # Here we start an asynchronous process pool to monitor the sizes in parallel
        with multiprocessing.Pool(processes=len(batch)) as pool:
            results = []
            for uid in batch:
                results.append(
                    pool.apply_async(
                        get_logs,
                        args=(
                            uid,
                            specs[uid],
                            submit_times[uid],
                            batch_end_time,
                            log_dir,
                            node_topology,
                        ),
                        error_callback=process_error_handler,
                    )
                )
            [result.wait() for result in results]

    # Stop the watcher just once
    watcher.stop()
    print(f"🧪️ Experiments are finished. See output in {outdir}")


def confirm_action(question):
    """
    Ask for confirmation of an action
    """
    response = input(question + " (yes/no)? ")
    while len(response) < 1 or response[0].lower().strip() not in "ynyesno":
        response = input("Please answer yes or no: ")
    if response[0].lower().strip() in "no":
        return False
    return True


def get_parser():
    parser = argparse.ArgumentParser(description="Test Kubernetes Sniffer Scheduler")
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="shuffle all experiments first",
    )
    parser.add_argument(
        "--config-name",
        default="mixed",
        help="config name to use (defaults to mixed)",
    )
    parser.add_argument(
        "--address",
        help="Sniffer service address for containers to query",
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=1,
        help="batches to do (defaults to 1)",
    )
    parser.add_argument(
        "--iters",
        type=int,
        default=3,
        help="iterations to run per batch (defaults to 3)",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join(here, "results"),
        help="output directory for results",
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Ensure our template directory and templates exist
    if not os.path.exists(job_template):
        sys.exit(f"{job_template} does not exist.")

    if not args.address:
        sys.exit("The --address of the sniffer service is required")

    outdir = os.path.abspath(args.outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Ensure the config is known
    if args.config_name not in configs:
        sys.exit(f"{args.config_name} is not a known configuration")

    # Show parameters to the user
    print(f"▶️  Output directory: {outdir}")
    print(f"▶️       Config name: {args.config_name}")
    print(f"▶️        Iterations: {args.iters}")
    print(f"▶️           Address: {args.address}")
    print(f"▶️           Batches: {args.batches}")
    print(f"▶️           Shuffle: {args.shuffle}")

    if not confirm_action("Would you like to continue?"):
        sys.exit("Cancelled!")

    # Write the topology to this file
    topology_file = os.path.join(outdir, "topology.json")

    # Write cluster node configuration and return mapping
    node_topology = get_cluster_config(topology_file)

    try:
        run(args, args.config_name, node_topology)
    except Exception as e:
        print("Error with run, inspect!")
        print(e)
        import IPython

        IPython.embed()


if __name__ == "__main__":
    main()
