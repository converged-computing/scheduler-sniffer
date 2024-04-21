package service

import (
	"fmt"

	pb "github.com/converged-computing/scheduler-sniffer/sniffer/api"

	"context"
)

type Sniffer struct {
	pb.UnimplementedSnifferServiceServer
}

// TODO data gets written here - parse send request based on data
func (s *Sniffer) Send(ctx context.Context, in *pb.SendRequest) (*pb.SendResponse, error) {
	fmt.Println("Send endpoint hit")
	return &pb.SendResponse{}, nil
}
