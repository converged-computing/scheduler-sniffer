package service

import (
	"fmt"

	"context"

	pb "github.com/converged-computing/scheduler-sniffer/sniffer/api"
	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/logger"
	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/types"
)

type Sniffer struct {
	pb.UnimplementedSnifferServiceServer
	Logger *logger.DebugLogger
}

// Send receives data from Kubernetes->scheduler module, specifically when a bind is successful
// We are currently not using the in.Payload
func (s *Sniffer) Send(ctx context.Context, in *pb.SendRequest) (*pb.SendResponse, error) {
	datum := types.SnifferDatum{Name: in.Pod, Object: "Pod", Endpoint: in.Endpoint, Node: in.Node, Event: in.Event, Timestamp: in.Timestamp}
	out, err := datum.ToJson()
	if err == nil {
		s.Logger.Debug("%s", out)
	} else {
		fmt.Errorf("Issue with saving datum: %s", err)
	}
	return &pb.SendResponse{}, nil
}
