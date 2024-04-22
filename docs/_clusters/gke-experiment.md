---
title: Prototyping Scheduler Sniffer
nodes: nodes.json
---


This shows early work to make a plot for the scheduler sniffer. We are looking at only a few minutes of data running Jobs (that need groups) on GKE c2d-standard-8 before the cluster clogged. Since we set the resource limit, we only have one pod per node (why it's all pink). Some quick notes:

- The data generation interface is started (but not finished yet) - the JavaScript logic needs to be added as an include in the collection.
- We likely want to have lines (timestamps) for when things clogged
- The time intervals are broken into 100 over those 4 minutes
- We have to decide if we want to include "other" pods (not job related) - right now they aren't included
- Node 5 likely has operator stuff (and other stuff) installed on it, and was chosen later

For the timestamp when we assume a pod is on a node, we use the bindingSuccess event. We use the PodCompleted status for when it is done.