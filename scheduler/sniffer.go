package scheduler

import (
	"context"
	"fmt"
	"time"

	"google.golang.org/grpc"

	pb "k8s.io/kubernetes/pkg/sniffer"
)

// Send returns data to the sniffer
func Send(ctx context.Context, endpoint, pod, node, event string) error {
	conn, err := grpc.Dial("127.0.0.1:4242", grpc.WithInsecure())
	if err != nil {
		fmt.Println("SNIFFER 1: ERROR: %s", err)
		return nil
	}
	defer conn.Close()
	grpcclient := pb.NewSnifferServiceClient(conn)

	_, cancel := context.WithTimeout(context.Background(), 200*time.Second)
	defer cancel()

	// Generate the timestamp
	request := &pb.SendRequest{
		Endpoint:  endpoint,
		Pod:       pod,
		Node:      node,
		Event:     event,
		Timestamp: time.Now().String(),
	}
	// An error here is an error with making the request
	_, err = grpcclient.Send(context.Background(), request)
	if err != nil {
		fmt.Println("SNIFFER 2: ERROR: %s", err)
		return err
	}
	return nil
}
