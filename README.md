# Scheduler Sniffer

> Smells like HPC!👃️

The scheduler-sniffer is an attempt to build a custom-scheduler plugin that mimics using the default scheduler, but adds in the ability
to see what is going on. This is a work in progress and I've already changed the design several times - expect that to happen again! Currently I'm taking an approach of creating a custom scheduler plugin, but largely making it empty. It only serves as a means to provide a custom entrypoint to the main scheduler code, and I'll customize this to add pings to a gRPC service that can record decisions at each step.

🚧️ Under Development 🚧️

## Development

Try making a kind cluster first.

```bash
kind create cluster
```

Courtesy scripts are provided to build the sniffer and load into your local kind cluster.

```bash
./hack/kind-build.sh
```

Try submitting a job.

```bash
kubectl apply -f example/job.yaml
```

You can see from events that it was scheduled to the sniffer:

```bash
kubectl get events -o wide |  awk {'print $4" " $5" " $6'} | column -t | grep sniffer
```

### Organization

- [src](src) has code intending to be moved into the sig-scheduler-plugins repository
- [sniffer](sniffer) is the sniffer service

It would be cool to do this with eBPF, but I haven't found a good, working container base yet.

## Notes

Things to track for the simulator:
- keep track of pod to node mappings (this is the basic unit of what we need)
- node occupancy and time (which nodes contain which pods at what point)

This will be a replacement for the in-tree Kubernetes scheduler, with the intention of adding a small service to ping and communicate
scheduling decisions. This is not meant for production use cases, but rather understanding what is happening in the scheduler. It 
will also serve as a prototype for me to understand developing an in-tree scheduler so we can eventually do one, for realsies.


## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614
