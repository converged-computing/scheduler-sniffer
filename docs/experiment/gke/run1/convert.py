#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

here = os.path.dirname(os.path.abspath(__file__))


def write_json(content, filename):
    """
    Write content to file.
    """
    with open(filename, "w") as fd:
        fd.write(json.dumps(content, indent=4))


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def format_datetime(x, fmt="%Y-%m-%d %H:%M:%S.%f"):
    return datetime.strptime(x, fmt)


def generate(args):
    """
    Generate nodes.json data from sniffer.log
    """
    log = read_file(args.log)
    lines = [json.loads(x) for x in log.split("\n") if x.strip()]

    # First create a lookup of all nodes - get from node and pod events
    nodes = set([x.get("node") for x in lines if x.get("node")])

    # Create uid (integer) for each node
    reverse_lookup = {node: i for i, node in enumerate(nodes)}

    # First do a sanity check that each pod has one node
    assigned = {}
    for entry in lines:
        if "node" not in entry or entry["object"] != "Pod":
            continue
        node = entry["node"]
        if entry["name"] in assigned and assigned[entry["name"]] != node:
            raise ValueError(f"Pod {entry['name']} was assigned to two nodes!")
        assigned[entry["name"]] = node

    # Now we want to get the earlist and latest timestamps for schedule
    # and pod completed
    schedule_times = [
        x.get("timestamp") for x in lines if x.get("event") == "BindingSuccess"
    ]
    schedule_times = [" ".join(x.split(" ")[0:2]) for x in schedule_times]
    schedule_times = [format_datetime(x[:-3]) for x in schedule_times]

    complete_times = [
        x.get("timestamp") for x in lines if x.get("event") == "preStop"
    ]
    complete_times = [" ".join(x.split(" ")[0:2]) for x in complete_times]
    complete_times = [
        format_datetime(x[:-3]) for x in complete_times
    ]

    min_schedule_time = min(schedule_times)
    max_schedule_time = max(schedule_times)
    min_complete_time = min(complete_times)
    max_complete_time = max(complete_times)
    min_time = min(min_schedule_time, min_complete_time)
    max_time = max(max_schedule_time, max_complete_time)

    # Break into intervals
    diff = (max_time - min_time) / args.intervals
    ts_intervals = []
    intervals = []
    print(f"Interval time is {diff} seconds")
    sys.exit()
    for i in range(args.intervals):
        intervals.append((min_time + diff * i).strftime("%H:%M:%S"))
        ts_intervals.append(min_time + diff * i)
    intervals.append(max_time.strftime("%H:%M:%S"))
    ts_intervals.append(max_time)

    # Get start and end for each pod. This is inefficient
    pods = [x.get("name") for x in lines if x.get("object") == "Pod"]
    pod_times = {}
    pod_string_times = {}
    for pod in set(pods):
        binding_time = None
        schedule_time = None
        post_start_time = None
        complete_time = None
        for line in lines:
            if "timestamp" not in line:
                continue
            # Let's use bindingSuccess since that implies binding to node
            if (
                not schedule_time
                and line.get("event") == "ScheduleSuccess"
                and line.get("name") == pod
            ):
                ts = " ".join(line.get("timestamp").split(" ")[0:2])
                schedule_time = format_datetime(ts[:-3])
            if (
                not binding_time
                and line.get("event") == "BindingSuccess"
                and line.get("name") == pod
            ):
                ts = " ".join(line.get("timestamp").split(" ")[0:2])
                binding_time = format_datetime(ts[:-3])
            if (
                not post_start_time
                and line.get("event") == "postStart"
                and line.get("name") == pod
            ):
                ts = " ".join(line.get("timestamp").split(" ")[0:2])
                post_start_time = format_datetime(ts[:-3])
            if (
                not complete_time
                and line.get("event") == "preStop"
                and line.get("name") == pod
            ):
                ts = " ".join(line.get("timestamp").split(" ")[0:2])
                complete_time = format_datetime(ts[:-3])

        # IMPORTANT: we are missing data here - there are pods that don't have completion timestamps
        # But they do have failures
        if binding_time is not None and complete_time is not None:
            pod_times[pod] = {
                "start": binding_time,
                "end": complete_time,
                "post_start": post_start_time,
                "schedule_time": schedule_time,
            }
            pod_string_times[pod] = {
                "start": str(binding_time),
                "end": str(complete_time),
                "post_start": str(post_start_time),
                "schedule_time": str(schedule_time),
            }

    # Save pod times to look at later:
    outdir = os.path.dirname(args.outfile)
    pod_times_file = os.path.join(outdir, "pod-times.json")
    write_json(pod_string_times, pod_times_file)

    # Keep a count of pods in each interval
    # QUESTION: do we want to filter down to job pods?
    active = {}
    for i, start_interval_dt in enumerate(ts_intervals):
        if intervals[i] not in active:
            active[intervals[i]] = {"nodes": {}, "interval": i}

        end_interval_dt = None
        if i < len(ts_intervals) - 1:
            end_interval_dt = ts_intervals[i + 1]
        else:
            end_interval_dt = ts_intervals[-1] + timedelta(minutes=1)

        # Node id if the pod is added
        for pod, times in pod_times.items():
            # Only consider pods for which we have node assigned
            if pod not in assigned:
                continue
            node_id = reverse_lookup[assigned[pod]]
            if times["start"] < start_interval_dt:
                if node_id not in active[intervals[i]]["nodes"]:
                    active[intervals[i]]["nodes"][node_id] = 0
                if times["end"] is not None and times["end"] >= end_interval_dt:
                    active[intervals[i]]["nodes"][node_id] += 1
                elif times["end"] is None:
                    print("Found end times None")

    # Now construct the final data
    entries = []
    for ts, entry in active.items():
        for node_id, count in entry["nodes"].items():
            if count > 0:
                entries.append([entry["interval"], node_id, count])

    # Note that scheduleSuccess and BindingSuccess are REALLY CLOSE
    # Since we care about scheduler cycle, let's arbitrarily use first
    # event "ScheduleSuccess" for name (Pod) and node (Node)
    # event "PodCompleted" for same pod assigned to node
    # This means we aren't including pods already there
    # Assemble records.
    title = " ".join([x.capitalize() for x in args.name.split("-")])
    data = {
        "id": args.name,
        "title": f"Experiment {title}",
        "data": {
            # TODO what can we add here?
            "chart_options": {},
            "values": {"data": entries},
        },
    }

    write_json([data], args.outfile)
    print(f"Output json written to {args.outfile}")


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
    parser = argparse.ArgumentParser(description="Convert sniffer.log to nodes.json")
    parser.add_argument(
        "log",
        help="sniffer.log file",
    )
    parser.add_argument(
        "outfile",
        default="sniffer-nodes.json",
        help="Output nodes json file to write to",
    )
    parser.add_argument(
        "--name",
        default="gke-experiment",
        help="Name for the experiment",
    )
    parser.add_argument(
        "--intervals",
        type=int,
        default=35,
        help="Number of time intervals",
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Show parameters to the user
    print(f"▶️  Output : {args.outfile}")
    print(f"▶️     Log : {args.log}")

    if not confirm_action("Would you like to continue?"):
        sys.exit("Cancelled!")

    try:
        generate(args)
    except Exception as e:
        print(f"Error with generate, inspect: {e}")


if __name__ == "__main__":
    main()
