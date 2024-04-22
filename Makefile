# Local Directory for upstreams
UPSTREAMS ?= ./upstreams

# Local repository directories
UPSTREAM ?= $(UPSTREAMS)/sig-scheduler-plugins
UPSTREAM_K8S ?= $(UPSTREAMS)/kubernetes

# Remote repositories
UPSTREAM_REPO ?= https://github.com/kubernetes-sigs/scheduler-plugins
UPSTREAM_K8S_REPO ?= https://github.com/kubernetes/kubernetes

BASH ?= /bin/bash
TAG ?= latest
VERSION ?= v0.0.0
ARCH ?= "amd64"

# These are passed to build the sidecar
REGISTRY ?= ghcr.io/converged-computing
SCHEDULER_IMAGE ?= scheduler-sniffer
SIDECAR_IMAGE ?= sniffer:latest

.PHONY: all build clone update
all: prepare build-sidecar build

upstreams: 
	mkdir -p $(UPSTREAMS)

clone: upstreams
	if [ -d "$(UPSTREAM)" ]; then echo "SIG upstream is cloned"; else git clone $(UPSTREAM_REPO) $(UPSTREAM); fi

clone-k8s: upstreams
	if [ -d "$(UPSTREAM_K8S)" ]; then echo "Kubernetes upstream is cloned"; else git clone --depth 1 $(UPSTREAM_K8S_REPO) $(UPSTREAM_K8S); fi

prepare: clone clone-k8s
	# This ensures the sig-scheduler image has the same grpc
	cp -R sniffer/api $(UPSTREAM_K8S)/pkg/sniffer

	# These basically allow us to wrap the default scheduler so we can run the command (and trace it)
	cp scheduler/* $(UPSTREAM_K8S)/pkg/scheduler/
	cp src/cmd/scheduler/main.go $(UPSTREAM)/cmd/scheduler/main.go
	cp src/manifests/install/charts/as-a-second-scheduler/templates/*.yaml $(UPSTREAM)/manifests/install/charts/as-a-second-scheduler/templates/
	cp src/manifests/install/charts/as-a-second-scheduler/values.yaml $(UPSTREAM)/manifests/install/charts/as-a-second-scheduler/values.yaml

build: prepare
	docker build -t ${REGISTRY}/${SCHEDULER_IMAGE} --build-arg ARCH=$(ARCH) --build-arg VERSION=$(VERSION) --build-arg sig_upstream=$(UPSTREAM) --build-arg k8s_upstream=$(UPSTREAM_K8S) .

build-sidecar: 
	make -C ./sniffer LOCAL_REGISTRY=${REGISTRY} LOCAL_IMAGE=${SIDECAR_IMAGE}

