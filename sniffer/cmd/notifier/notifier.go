package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	"context"

	"google.golang.org/grpc"

	pb "github.com/converged-computing/scheduler-sniffer/sniffer/api"
)

const (
	defaultPort = ":4242"
)

// getPodname derive the pod name, falling back to hostname
func getPodname() (string, error) {
	podname := os.Getenv("SNIFFER_POD_NAME")
	var err error
	if podname == "" {
		podname, err = os.Hostname()
	}
	return podname, err
}

/*
Try to get node and hostname from environment

	env:
	  - name: MY_NODE_NAME
	    valueFrom:
	      fieldRef:
	        fieldPath: spec.nodeName
	  - name: MY_POD_NAME
	    valueFrom:
	      fieldRef:
	        fieldPath: metadata.name
*/
func main() {
	address := flag.String("address", "", "Address for the sniffer service")
	stage := flag.String("stage", "preStop", "Stage to alert for (e.g., start, stop)")
	event := flag.String("event", "preStop", "Event to alert for")
	flag.Parse()

	node := os.Getenv("SNIFFER_NODE_NAME")
	pod, err := getPodname()
	if err != nil {
		fmt.Printf("SNIFFER NOTIFIER: ERROR: %s\n", err)
		os.Exit(1)
	}
	Send(context.TODO(), *address, *stage, pod, node, *event)
}

// Send returns data to the sniffer
func Send(ctx context.Context, address, endpoint, pod, node, event string) error {
	conn, err := grpc.Dial(address, grpc.WithInsecure())
	if err != nil {
		fmt.Printf("SNIFFER NOTIFIER: ERROR: %s\n", err)
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
		fmt.Printf("SNIFFER NOTIFIER: ERROR: %s\n", err)
		return err
	}
	return nil
}
