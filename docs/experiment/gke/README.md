# Testing Sniffer on GKE

I don't have a good means to test with other custom schedulers yet, but I want to see here how to get a log
of sniffer events. I'm first going to try with just the sniffer on GKE, and to record some jobs (that don't fail)
and some that do. I want to determine if we are able to get everything we need from events (and don't need the scheduler sniffer)
or if the complexity is warranted.
  
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
./hack/quick-install-gke.sh
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

Let's run a basic experiment to collect data.

```bash
mkdir -p ./results
time python run_experiments.py --outdir ./results --config-name mixed --batches 1 --iters 10
```

It will clog sooner or later.

```console
$ kubectl get pods | grep Running
$ kubectl get pods | grep Running
job-0-0-size-5-0-pggwc                          1/1     Running   0          3m11s
job-0-0-size-5-1-5ts8f                          1/1     Running   0          3m11s
job-0-1-size-3-0-gmvj6                          1/1     Running   0          3m9s
job-0-1-size-6-0-dj5bf                          1/1     Running   0          3m4s
job-0-1-size-6-1-ljd7q                          1/1     Running   0          3m4s
job-0-1-size-6-3-qn6d7                          1/1     Running   0          3m4s
job-0-1-size-6-4-sgrrm                          1/1     Running   0          3m4s
job-0-2-size-4-0-dz466                          1/1     Running   0          3m2s
scheduler-plugins-controller-5ddb8bcb55-6kzwq   1/1     Running   0          6m50s
sniffer-86dbcfbf45-9vgdb                        3/3     Running   0          6m50s
```

Save the sniffer logs

```bash
$ kubectl exec -it sniffer-86dbcfbf45-9vgdb -c watcher -- cat /tmp/logs/sniffer.log > docs/gke/sniffer.log
```

Note that conditions are always present, so you might see the same conditions twice (with the same timestamp)
and should parse accordingly.

```bash
$ kubectl get pods | grep Pending | wc -l
175
$ kubectl get pods | grep Running | wc -l
10
```

Cancel the experiment and clean up.

```bash
kubectl delete jobs --all
kubectl delete service --all
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

### Visualization

We need to take the [sniffer.log](sniffer.log) and convert into data that will populate our graph.
We will put this a few levels up in [docs/_clusters](../../_clusters). We can use this converter script:

```bash
# TODO write this script
python convert.py sniffer.log gke-nodes.json --intervals 100
```
