
INSTALL_PREFIX ?= /usr
LIB_PREFIX ?= /usr/lib
LOCALBIN ?= $(shell pwd)/bin
LOCAL_REGISTRY=localhost:5000
LOCAL_IMAGE=sniffer-sidecar:latest
RELEASE_VERSION?=v$(shell date +%Y%m%d)

.PHONY: all
all: build

.PHONY: $(LOCALBIN)
$(LOCALBIN):
	mkdir -p $(LOCALBIN)

.PHONY: proto build
build:
	docker build -f Dockerfile --build-arg ARCH="amd64" --build-arg RELEASE_VERSION="$(RELEASE_VERSION)" -t $(LOCAL_REGISTRY)/$(LOCAL_IMAGE) .

.PHONY: sniffer
sniffer: service watcher notifier

.PHONY: service
service: 
	go build -ldflags '-w' -o bin/sniffer cmd/service/service.go

.PHONY: watcher
watcher: 
	go build -ldflags '-w' -o bin/watcher cmd/watcher/watcher.go

.PHONY: notifier
notifier: 
	go build -ldflags '-w' -o bin/notifier cmd/notifier/notifier.go

.PHONY: protoc
protoc: $(LOCALBIN)
	GOBIN=$(LOCALBIN) go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.28
	GOBIN=$(LOCALBIN) go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.2
	
# You can use make protoc to download proto
.PHONY: proto
proto: protoc
	PATH=$(LOCALBIN):${PATH} protoc --go_out=. --go_opt=paths=source_relative --go-grpc_out=. --go-grpc_opt=paths=source_relative api/sniffer.proto
