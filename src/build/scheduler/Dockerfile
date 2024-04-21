FROM ubuntu:latest as base

RUN apt-get update && apt-get install -y wget git vim build-essential

# Install Go
ENV GO_VERSION=1.22.2
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz  && tar -xvf go${GO_VERSION}.linux-amd64.tar.gz && \
         mv go /usr/local && rm go${GO_VERSION}.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin
WORKDIR /go/src/sigs.k8s.io/scheduler-plugins
COPY . .
ARG ARCH
ARG RELEASE_VERSION
RUN RELEASE_VERSION=${RELEASE_VERSION} make build-scheduler.$ARCH

WORKDIR /go/src/sigs.k8s.io/scheduler-plugins/_kubernetes
RUN make WHAT=cmd/kube-scheduler

# https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/
FROM busybox
COPY --from=base /go/src/sigs.k8s.io/scheduler-plugins/_kubernetes/_output/local/go/bin/kube-scheduler /bin/kube-scheduler
WORKDIR /bin
CMD ["kube-scheduler"]
