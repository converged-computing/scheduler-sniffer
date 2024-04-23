# Testing Sniffer on GKE

I don't have a good means to test with other custom schedulers yet, but I want to see here how to get a log
of sniffer events. I'm first going to try with just the sniffer on GKE, and to record some jobs. 
  
## Experiments

Create a cluster:

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=8 \
    --no-enable-autorepair \
    --no-enable-autoupgrade \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8
```

Then install the sniffer from here:

```bash
./hack/quick-build-gke.sh
```

Make sure they are all running:

```bash
kubectl get pods
```
```console
NAME                                            READY   STATUS    RESTARTS   AGE
scheduler-plugins-controller-5ddb8bcb55-6kzwq   1/1     Running   0          26s
sniffer-86dbcfbf45-9vgdb                        3/3     Running   0          26s
```

### Basic Experiment

Let's run a basic experiment to collect data. You'll need the service address of the pod with the sniffer service.

```bash
kubectl get pods -o wide
```

Note that the address is local to the cluster and has the port 4242.

```bash
mkdir -p ./results
time python run_experiments.py --outdir ./results --config-name mixed --batches 1 --iters 5 --address 10.96.0.15:4242
```

This one only requires one core per pod, so it's much less likely to clog. Watch for the running pods to stop moving.
Save the sniffer logs

```bash
$ kubectl exec -it sniffer-86dbcfbf45-9vgdb -c watcher -- cat /tmp/logs/sniffer.log > sniffer.log
```

Note that conditions are always present, so you might see the same conditions twice (with the same timestamp)
and should parse accordingly.

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

### Questions

- should we use scheduleCycle event or bindingEvent (in this experiment they are very close, but not clear if clogging)
- if we can establish relationship (diff) between the container start and binding (likely related to pull) we can simplify this into a deployment to run in the cluster, or an operator with a mutating webhook to add the sidecar (much better design)
- going to be problematic with preStop hook if we have to kill (delete) the job, in testing I didn't see it fire. We need to have the job success policy

### Visualization

We need to take the [sniffer.log](sniffer.log) and convert into data that will populate our graph.
We will put this a few levels up in [docs/_clusters](../../_clusters). We can use this converter script:

```bash
python convert.py sniffer.log gke-3-nodes.json --intervals 100
```
