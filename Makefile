CLONE_UPSTREAM ?= ./upstream
CLONE_UPSTREAM_K8S ?= ./upstream/_kubernetes
UPSTREAM ?= https://github.com/kubernetes-sigs/scheduler-plugins
UPSTREAM_K8S ?= https://github.com/kubernetes/kubernetes
BASH ?= /bin/bash
DOCKER ?= docker
TAG ?= latest

# These are passed to build the sidecar
REGISTRY ?= ghcr.io/converged-computing
SCHEDULER_IMAGE ?= scheduler-sniffer
SIDECAR_IMAGE ?= sniffer-sidecar:latest

.PHONY: all build clone update

all: prepare build-sidecar build

clone:
	if [ -d "$(CLONE_UPSTREAM)" ]; then echo "Upstream is cloned"; else git clone $(UPSTREAM) $(CLONE_UPSTREAM); fi

clone-k8s:
	if [ -d "$(CLONE_UPSTREAM_K8S)" ]; then echo "Upstream is cloned"; else git clone --depth 1 $(UPSTREAM_K8S) $(CLONE_UPSTREAM_K8S); fi

prepare: clone clone-k8s
	# This ensures the sig-scheduler image has the same grpc
	cp -R sniffer/api ./upstream/_kubernetes/pkg/sniffer

    # These basically allow us to wrap the default scheduler so we can run the command (and trace it)
	cp src/pkg/scheduler/* ./upstream/_kubernetes/pkg/scheduler/
	cp src/cmd/app/server.go ./upstream/cmd/app/server.go
	cp src/build/scheduler/Dockerfile ./upstream/build/scheduler/Dockerfile
	cp src/cmd/scheduler/main.go ./upstream/cmd/scheduler/main.go
	cp src/manifests/install/charts/as-a-second-scheduler/templates/*.yaml $(CLONE_UPSTREAM)/manifests/install/charts/as-a-second-scheduler/templates/
	cp src/manifests/install/charts/as-a-second-scheduler/values.yaml $(CLONE_UPSTREAM)/manifests/install/charts/as-a-second-scheduler/values.yaml

build: prepare
	REGISTRY=${REGISTRY} IMAGE=${SCHEDULER_IMAGE} CONTROLLER_IMAGE=${CONTROLLER_IMAGE} $(BASH) $(CLONE_UPSTREAM)/hack/build-images.sh

build-sidecar: 
	make -C ./sniffer LOCAL_REGISTRY=${REGISTRY} LOCAL_IMAGE=${SIDECAR_IMAGE}

