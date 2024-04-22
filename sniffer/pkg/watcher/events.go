package watcher

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/converged-computing/scheduler-sniffer/sniffer/pkg/types"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/klog"
)

var (
	ignoreNs = "kube-system"
)

// saveDatum is a generic function to serialize and save the data
func (w *Watcher) saveDatum(datum types.SnifferDatum) {
	out, err := datum.ToJson()
	if err == nil {
		w.log.Debug("%s", out)
	} else {
		fmt.Errorf("Issue with saving datum: %s", err)
	}
}

// savePodData saves events for a pod
func (w *Watcher) savePodData(pod *corev1.Pod, endpoint string) {
	w.saveDatum(
		types.SnifferDatum{
			Name:     pod.Name,
			Object:   "Pod",
			Endpoint: endpoint,
			Node:     pod.Status.NominatedNodeName,
			Event:    string(pod.Status.Phase),
		},
	)

	for _, condition := range pod.Status.Conditions {
		if condition.Status != "True" {
			continue
		}

		// Assume these are empty
		ts := ""
		timestamp := condition.LastProbeTime
		if timestamp.IsZero() {
			timestamp = condition.LastTransitionTime
		}
		if !timestamp.IsZero() {
			ts = timestamp.String()
		}

		w.saveDatum(
			types.SnifferDatum{
				Name:      pod.Name,
				Reason:    condition.Reason,
				Message:   condition.Message,
				Object:    "Pod",
				Endpoint:  endpoint,
				Node:      pod.Status.NominatedNodeName,
				Event:     string(condition.Type),
				Timestamp: ts,
			},
		)
	}
}

// saveNodeData saves events for a node
func (w *Watcher) saveNodeData(node *corev1.Node, endpoint string) {

	// Generate capacity and allocatable
	extra := "{"
	for name, quantity := range node.Status.Capacity {
		extra = fmt.Sprintf(`%s "capacity-%s": "%s",`, extra, name, quantity.String())
	}
	for name, quantity := range node.Status.Allocatable {
		extra = fmt.Sprintf(`%s "allocatable-%s": "%s",`, extra, name, quantity.String())
	}
	extra = strings.TrimRight(extra, ",") + "}"
	fmt.Println(extra)
	w.saveDatum(
		types.SnifferDatum{
			Name:     node.Name,
			Object:   "Node",
			Endpoint: endpoint,
			Event:    string(node.Status.Phase),
			Extra:    json.RawMessage(extra),
		},
	)

	for _, condition := range node.Status.Conditions {
		if condition.Status != "True" {
			continue
		}

		// Assume these are empty
		ts := ""
		timestamp := condition.LastHeartbeatTime
		if timestamp.IsZero() {
			timestamp = condition.LastTransitionTime
		}
		if !timestamp.IsZero() {
			ts = timestamp.String()
		}

		w.saveDatum(
			types.SnifferDatum{
				Name:      node.Name,
				Reason:    condition.Reason,
				Message:   condition.Message,
				Object:    "Node",
				Endpoint:  endpoint,
				Event:     string(condition.Type),
				Timestamp: ts,
			},
		)
	}
}

func (w *Watcher) podAdd(obj interface{}) {
	pod := obj.(*corev1.Pod)
	if pod.Namespace == ignoreNs {
		return
	}
	w.savePodData(pod, "podAdd")
	klog.Infof("POD CREATED: %s/%s", pod.Namespace, pod.Name)
}

func (w *Watcher) podUpdate(oldObj interface{}, newObj interface{}) {
	oldPod := oldObj.(*corev1.Pod)
	newPod := newObj.(*corev1.Pod)

	if oldPod.Namespace == ignoreNs || newPod.Namespace == ignoreNs {
		return
	}
	w.savePodData(newPod, "podUpdate")
}

func (w *Watcher) podDelete(obj interface{}) {
	pod := obj.(*corev1.Pod)
	if pod.Namespace == ignoreNs {
		return
	}
	w.savePodData(pod, "podDelete")
	klog.Infof("POD DELETED: %s/%s", pod.Namespace, pod.Name)
}

func (w *Watcher) nodeAdd(obj interface{}) {
	node := obj.(*corev1.Node)
	w.saveNodeData(node, "nodeAdd")
	klog.Infof("NODE CREATED: %s", node)
}

func (w *Watcher) nodeUpdate(oldObj interface{}, newObj interface{}) {
	oldNode := oldObj.(*corev1.Node)
	newNode := newObj.(*corev1.Node)
	w.saveNodeData(newNode, "nodeUpdate")
	klog.Infof(
		"NODE UPDATED. %s/%s %s",
		oldNode, newNode, newNode.Status.Phase,
	)
}

func (w *Watcher) nodeDelete(obj interface{}) {
	node := obj.(*corev1.Node)
	w.saveNodeData(node, "nodeDeleted")
	klog.Infof("NODE DELETED: %s", node)
}
