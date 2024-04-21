FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.21.9

RUN apt-get update && apt-get install -y wget git build-essential && \
    apt-get clean -y && apt -y autoremove

# Install go
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz  && tar -xvf go${GO_VERSION}.linux-amd64.tar.gz && \
    mv go /usr/local && rm go${GO_VERSION}.linux-amd64.tar.gz

# ENV GOROOT=/usr/local/go
# ENV GOPATH=/go
ENV PATH=/usr/local/go/bin:$PATH

# Go dependencies for protobuf
RUN apt -y update && apt -y upgrade && apt install --no-install-recommends -y protobuf-compiler curl && \
    go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.26 && \ 
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.1

# These need to be on the LD_LIBRARY_PATH for the server to find at runtime
WORKDIR /go/src/sniffer
COPY . .

RUN make proto && \
    go mod tidy && \
    go mod vendor && \
    make sniffer
