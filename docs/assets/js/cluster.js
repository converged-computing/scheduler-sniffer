---
layout: null
---

function _1(md){return(
md`<div style="color: grey; font: 13px/25.5px var(--sans-serif); text-transform: uppercase;"></div>`
)}

function _experiment(Inputs, running){return(
Inputs.select(running.map(d => d.experiment), {unique: true, label: "Experiment"})
)}

function _3(Plot, width, running, experiment, introductions){return(
Plot.plot({
  width,
  height: 930,
  marginBottom: 30,
  padding: 0,
  round: false,
  label: null,
  x: {axis: "top"},
  color: {
    scheme: "purd",
//    legend: true,
//    type: "sqrt",
//    label: "Node "
  },
  marks: [
    Plot.barX(running.filter(d => d.experiment === experiment), {
      x: "interval",
      y: "node",
      interval: 1,
      inset: 0.5,
      fill: "occupied",
      title: "occupied"
    }),
    // These are lines to show intervals when jobs and experiments finished
    Plot.ruleX([introductions.find(d => d.experiment === experiment)], {
      x: "jobs_finished"
    }),
    Plot.text([introductions.find(d => d.experiment === experiment)], {
      x: "jobs_finished",
      dy: 4,
      lineAnchor: "top",
      frameAnchor: "bottom",
      text: (d) => `\nJobs Finished`
    }),
    // These are lines to show intervals when jobs and experiments finished
    Plot.ruleX([introductions.find(d => d.experiment === experiment)], {
      x: "experiment_finished"
    }),
    Plot.text([introductions.find(d => d.experiment === experiment)], {
      x: "experiment_finished",
      dy: -30,
      lineAnchor: "top",
      frameAnchor: "top",
      text: (d) => `Experiment Finished`
    })
  ]
})
)}


async function ETtoDate (et) {
  return new Date(Date.UTC(1970,0,1,0,0,et))
}

async function _running(FileAttachment, nodes)
{
  const running = await FileAttachment("nodes.json").json();
  return running
    .flatMap(({title: experiment, data: {values: {data}}}) => data
    .map(([interval, nodeIndex, occupied]) => ({
      experiment, 
      interval: interval,
//      interval: new Date(`${interval}`), 
//      interval: ETtoDate(interval),
      node: parseInt(nodeIndex), 
      occupied
    })));
}


async function _introductions(FileAttachment)
{
  const running = await FileAttachment("nodes.json").json();
  return running
    .map(({title: experiment, data: {chart_options: {jobs_finished, experiment_finished}}}) => ({
      experiment,
      experiment_finished: 0,
      jobs_finished: 0,
    }));
}


// This should not be being used..
function _nodes(){return(
['0', '1', '2', '3', '4', '5', '6', '7']
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  function toString() { return this.url; }
  // TODO this is hard coded for now, need to have this generated with the collection
  const fileAttachments = new Map([
    ["nodes.json", {url: new URL("{{ site.baseurl }}/clusters/gke-experiment/nodes.json", import.meta.url), mimeType: "application/json", toString}]
  ]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer()).define(["md"], _1);
  main.variable(observer("viewof experiment")).define("viewof experiment", ["Inputs", "running"], _experiment);
  main.variable(observer("experiment")).define("experiment", ["Generators", "viewof experiment"], (G, _) => G.input(_));
  main.variable(observer()).define(["Plot","width","running","experiment","introductions"], _3);
  main.variable(observer("running")).define("running", ["FileAttachment", "nodes"], _running);
  main.variable(observer("introductions")).define("introductions", ["FileAttachment"], _introductions);
  main.variable(observer("nodes")).define("nodes", _nodes);
  return main;
}
