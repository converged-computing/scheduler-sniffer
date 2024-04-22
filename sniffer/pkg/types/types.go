package types

import (
	"encoding/json"
	"fmt"
)

// A SnifferDatum holds one entry of data
type SnifferDatum struct {
	Object    string          `json:"object"`
	Name      string          `json:"name"`
	Endpoint  string          `json:"endpoint,omitempty"`
	Reason    string          `json:"reason,omitempty"`
	Message   string          `json:"message,omitempty"`
	Node      string          `json:"node,omitempty"`
	Event     string          `json:"event,omitempty"`
	Extra     json.RawMessage `json:"extra,omitempty"`
	Timestamp string          `json:"timestamp,omitempty"`
}

// ToJson serializes to json
func (d *SnifferDatum) ToJson() (string, error) {
	out, err := json.Marshal(&d)
	if err != nil {
		fmt.Printf("error marshalling: %s\n", err)
		return "", err
	}
	return string(out), nil
}
