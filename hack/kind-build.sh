#!/bin/bash

# Before running this, you should:
# 1. create the kind cluster (needs more than one node, fluence does not scheduler to the control plane)
# 2. Install cert-manager
# 3. Customize the script to point to your registry if you intend to push

REGISTRY="${1:-ghcr.io/converged-computing}"
HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT=$(dirname ${HERE})

# Go to the script directory
cd ${ROOT}

make

# We load into kind so we don't need to push/pull and use up internet data ;)
kind load docker-image ${REGISTRY}/scheduler-sniffer:latest
kind load docker-image ${REGISTRY}/sniffer:latest

# And then install using the charts. The pull policy ensures we use the loaded ones
cd ${ROOT}/upstreams/sig-scheduler-plugins/manifests/install/charts
helm uninstall sniffer || true
helm install \
  --set sniffer.pullPolicy=Never \
  --set sniffer.image=${REGISTRY}/sniffer:latest \
  --set scheduler.image=${REGISTRY}/scheduler-sniffer:latest \
  --set scheduler.pullPolicy=Never sniffer as-a-second-scheduler/
