package watcher

import (
	"fmt"
	"time"

	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/logger"

	"k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/cache"
)

type Watcher struct {
	logfile string
	log     *logger.DebugLogger
	client  *kubernetes.Clientset
}

func NewWatcher(logfile string) *Watcher {
	if logfile == "" {
		logfile = logger.DefaultLogFile
	}
	l := logger.NewDebugLogger(logger.LevelDebug, logfile)

	return &Watcher{logfile: logfile, log: l}
}

// Run the watcher, saving events to the log file
func (w *Watcher) Run() {
	config, err := rest.InClusterConfig()
	if err != nil {
		panic(err)
	}

	// create the clientset
	clientSet, err := kubernetes.NewForConfig(config)
	if err != nil {
		panic(err)
	}
	// Set the client for future calling functions
	w.client = clientSet

	// stop signal for the informer
	stopper := make(chan struct{})
	defer close(stopper)

	// create shared informers for pods and nodes
	factory := informers.NewSharedInformerFactoryWithOptions(clientSet, 10*time.Second)
	podInformer := factory.Core().V1().Pods().Informer()
	nodeInformer := factory.Core().V1().Nodes().Informer()

	defer runtime.HandleCrash()

	// start informer ->
	go factory.Start(stopper)

	// start to sync and call list
	if !cache.WaitForCacheSync(stopper, podInformer.HasSynced) {
		runtime.HandleError(fmt.Errorf("Timed out waiting for pod caches to sync"))
		return
	}
	if !cache.WaitForCacheSync(stopper, nodeInformer.HasSynced) {
		runtime.HandleError(fmt.Errorf("Timed out waiting for node caches to sync"))
		return
	}

	podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc:    w.podAdd,
		UpdateFunc: w.podUpdate,
		DeleteFunc: w.podDelete,
	})
	nodeInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc:    w.nodeAdd,
		UpdateFunc: w.nodeUpdate,
		DeleteFunc: w.nodeDelete,
	})

	// block the main go routine from exiting
	<-stopper
}
