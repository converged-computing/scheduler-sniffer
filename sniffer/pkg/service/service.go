package service

import (
	"encoding/json"
	"fmt"

	"context"

	pb "github.com/converged-computing/scheduler-sniffer/sniffer/api"
	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/logger"
)

type Sniffer struct {
	pb.UnimplementedSnifferServiceServer
	Logger *logger.DebugLogger
}

// A SnifferDatum holds one entry of data
type SnifferDatum struct {
	Pod       string `json:"pod"`
	Endpoint  string `json:"endpoint"`
	Node      string `json:"node"`
	Event     string `json:"event"`
	Timestamp string `json:"timestamp"`
}

// ToJson serializes to json
func (d *SnifferDatum) ToJson() (string, error) {
	out, err := json.Marshal(d)
	if err != nil {
		fmt.Printf("error marshalling: %s\n", err)
		return "", err
	}
	return string(out), nil
}

// Send receives data from Kubernetes->scheduler module, specifically when a bind is successful
// We are currently not using the in.Payload
func (s *Sniffer) Send(ctx context.Context, in *pb.SendRequest) (*pb.SendResponse, error) {
	datum := SnifferDatum{Pod: in.Pod, Endpoint: in.Endpoint, Node: in.Node, Event: in.Event, Timestamp: in.Timestamp}
	out, err := datum.ToJson()
	if err == nil {
		s.Logger.Debug("%s", out)
	} else {
		fmt.Errorf("Issue with saving datum: %s", err)
	}
	return &pb.SendResponse{}, nil
}
