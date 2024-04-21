package scheduler

import (
	"context"
	"time"

	"google.golang.org/grpc"

	pb "k8s.io/kubernetes/pkg/sniffer"
)

// Send returns data to the sniffer
func Send(ctx context.Context, endpoint, payload string) error {
	conn, err := grpc.Dial("127.0.0.1:4242", grpc.WithInsecure())
	if err != nil {
		return nil
	}
	defer conn.Close()
	grpcclient := pb.NewSnifferServiceClient(conn)

	_, cancel := context.WithTimeout(context.Background(), 200*time.Second)
	defer cancel()

	request := &pb.SendRequest{
		Endpoint: endpoint,
		Payload:  payload,
	}
	// An error here is an error with making the request
	_, err = grpcclient.Send(context.Background(), request)
	if err != nil {
		return err
	}
	return nil
}
