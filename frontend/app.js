function getApiBase() {
var stored = window.localStorage.getItem("mnemoApiBase");
if (stored && stored.length > 0) {
return stored;
}
return "http://localhost:8000";
}
function setApiBase(value) {
window.localStorage.setItem("mnemoApiBase", value);
}
function formatJson(value) {
try {
return JSON.stringify(value, null, 2);
} catch (e) {
return String(value);
}
}
function callApi(path, body) {
var base = getApiBase();
return fetch(base + path, {
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify(body)
}).then(function (res) {
return res.json();
});
}
function wireApiConfig() {
var input = document.getElementById("api-base-input");
var button = document.getElementById("api-base-save");
input.value = getApiBase();
button.addEventListener("click", function () {
var value = input.value.trim();
if (!value) {
return;
}
setApiBase(value);
});
}
function wireIngest() {
var textEl = document.getElementById("ingest-text");
var sourceEl = document.getElementById("ingest-source");
var profileEl = document.getElementById("ingest-profile");
var tsEl = document.getElementById("ingest-timestamp");
var storeEl = document.getElementById("ingest-store");
var submit = document.getElementById("ingest-submit");
var output = document.getElementById("ingest-output");
submit.addEventListener("click", function () {
var text = textEl.value.trim();
var source = sourceEl.value;
var profile = profileEl.value;
var timestamp = tsEl.value.trim();
var store = storeEl.value.trim() || "data/memories.json";
if (!text) {
output.textContent = "Text is required.";
return;
}
var payload = {
text: text,
source: source,
store: store,
profile: profile
};
if (timestamp) {
payload.timestamp = timestamp;
}
output.textContent = "Ingesting...";
callApi("/ingest", payload).then(function (data) {
output.textContent = formatJson(data);
}).catch(function (err) {
output.textContent = "Error: " + String(err);
});
});
}
function wireQuestion() {
var questionEl = document.getElementById("question-text");
var storeEl = document.getElementById("question-store");
var submit = document.getElementById("question-submit");
var output = document.getElementById("question-output");
submit.addEventListener("click", function () {
var question = questionEl.value.trim();
var store = storeEl.value.trim() || "data/memories.json";
if (!question) {
output.textContent = "Question is required.";
return;
}
var payload = {
question: question,
store: store
};
output.textContent = "Asking...";
callApi("/answer", payload).then(function (data) {
output.textContent = data.answer || formatJson(data);
}).catch(function (err) {
output.textContent = "Error: " + String(err);
});
});
}
function wireSession() {
var topicEl = document.getElementById("session-topic");
var storeEl = document.getElementById("session-store");
var startEl = document.getElementById("session-start");
var endEl = document.getElementById("session-end");
var submit = document.getElementById("session-submit");
var output = document.getElementById("session-output");
submit.addEventListener("click", function () {
var topic = topicEl.value.trim();
var store = storeEl.value.trim() || "data/memories.json";
var start = startEl.value.trim();
var end = endEl.value.trim();
if (!topic) {
output.textContent = "Topic is required.";
return;
}
var payload = {
topic: topic,
store: store
};
if (start) {
payload.start = start;
}
if (end) {
payload.end = end;
}
output.textContent = "Running session...";
callApi("/session", payload).then(function (data) {
output.textContent = data.answer || formatJson(data);
}).catch(function (err) {
output.textContent = "Error: " + String(err);
});
});
}
function wireGraphAndTimeline() {
var storeEl = document.getElementById("graph-store");
var topicEl = document.getElementById("timeline-topic");
var graphBtn = document.getElementById("graph-submit");
var timelineBtn = document.getElementById("timeline-submit");
var graphOut = document.getElementById("graph-output");
var timelineOut = document.getElementById("timeline-output");
graphBtn.addEventListener("click", function () {
var store = storeEl.value.trim() || "data/memories.json";
var payload = {
store: store
};
graphOut.textContent = "Loading graph...";
callApi("/graph", payload).then(function (data) {
graphOut.textContent = formatJson(data);
}).catch(function (err) {
graphOut.textContent = "Error: " + String(err);
});
});
timelineBtn.addEventListener("click", function () {
var store = storeEl.value.trim() || "data/memories.json";
var topic = topicEl.value.trim();
var payload = {
store: store
};
if (topic) {
payload.topic = topic;
}
timelineOut.textContent = "Loading timeline...";
callApi("/timeline", payload).then(function (data) {
timelineOut.textContent = formatJson(data.items || data);
}).catch(function (err) {
timelineOut.textContent = "Error: " + String(err);
});
});
}
window.addEventListener("DOMContentLoaded", function () {
wireApiConfig();
wireIngest();
wireQuestion();
wireSession();
wireGraphAndTimeline();
});

