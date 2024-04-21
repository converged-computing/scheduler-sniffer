package main

import (
	"flag"
	"fmt"
	"net"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"

	pb "github.com/converged-computing/scheduler-sniffer/sniffer/api"
	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/service"
)

const (
	defaultPort = ":4242"
)

var responsechan chan string

func main() {
	grpcPort := flag.String("port", defaultPort, "Port for grpc service")

	flag.Parse()

	// Ensure our port starts with :
	port := *grpcPort
	if !strings.HasPrefix(":", port) {
		port = fmt.Sprintf(":%s", port)
	}
	sniffer := service.Sniffer{}

	lis, err := net.Listen("tcp", port)
	if err != nil {
		fmt.Printf("[GRPCServer] failed to listen: %v\n", err)
	}

	responsechan = make(chan string)
	s := grpc.NewServer(
		grpc.KeepaliveParams(keepalive.ServerParameters{
			MaxConnectionIdle: 5 * time.Minute,
		}),
	)
	pb.RegisterSnifferServiceServer(s, &sniffer)
	fmt.Printf("[GRPCServer] gRPC Listening on %s\n", lis.Addr().String())
	if err := s.Serve(lis); err != nil {
		fmt.Printf("[GRPCServer] failed to serve: %v\n", err)
	}
	fmt.Printf("[GRPCServer] Exiting\n")
}
