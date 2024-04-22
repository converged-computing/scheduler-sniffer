package main

import (
	"flag"

	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/logger"
	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/watcher"
)

func main() {
	logfile := flag.String("logfile", logger.DefaultLogFile, "Default log file to write to")
	flag.Parse()

	// Create a new watcher with the logfile
	w := watcher.NewWatcher(*logfile)
	w.Run()
}
