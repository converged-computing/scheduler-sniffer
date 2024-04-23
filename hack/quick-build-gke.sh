#!/bin/bash

REGISTRY="${1:-vanessa}"
HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT=$(dirname ${HERE})

# Go to the script directory
cd ${ROOT}

# Push to vanessa/<image>
make REGISTRY=${REGISTRY}

# We load into kind so we don't need to push/pull and use up internet data ;)
docker push ${REGISTRY}/scheduler-sniffer:latest
docker push ${REGISTRY}/sniffer:latest

# And then install using the charts. The pull policy ensures we use the loaded ones
cd ${ROOT}/upstreams/sig-scheduler-plugins/manifests/install/charts
helm uninstall sniffer || true
helm install \
  --set sniffer.image=${REGISTRY}/sniffer:latest \
  --set scheduler.image=${REGISTRY}/scheduler-sniffer:latest \
  sniffer as-a-second-scheduler/
