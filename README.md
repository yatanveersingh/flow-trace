# Flow Trace – End‑to‑End Integration Tracing Platform

## Overview
Flow Trace is a **platform‑agnostic tracing and visualization framework** designed to provide **end‑to‑end observability** for integration workflows. It captures structured trace events from integration runtimes (such as MuleSoft), streams them through a message broker, indexes them into Elasticsearch, and renders them in a **Python‑based visual UI** that clearly represents execution flow, branching, retries, errors, and timing.

This project is ideal for:
- Integration architects
- Platform engineering teams
- Observability / tracing use cases
- Debugging complex async workflows

---

## High‑Level Architecture

```
Producer (Mule / Any Platform)
        │
        ▼
 JSON Trace Events
        │
        ▼
Apache Artemis MQ
        │
        ▼
   Logstash (JMS)
        │
        ▼
 Elasticsearch
        │
        ▼
 Python UI (Flow Trace)
```

Each trace event represents a **step in a workflow**, allowing Flow Trace to reconstruct the execution path visually.

---

## Key Features

- 🔍 **End‑to‑end flow visualization** (block‑diagram style)
- ⏱️ **Timing & latency tracking** per step
- 🔁 **Retry / Until‑Successful awareness**
- ❌ **Error & exception highlighting**
- 🌳 **Branching support** (Scatter‑Gather, Choice, Sub‑flows)
- 🔌 **Platform‑agnostic** (not Mule‑only)
- ⚙️ **Zero vendor lock‑in**

---

## Repository Structure

```
flow-trace/
├── app.py                 # Flask application entry
├── wsgi.py                # Production WSGI entry
├── elastic.py             # Elasticsearch query layer
├── models.py              # Trace / node data models
├── utils.py               # Helper & transformation utilities
├── static/
│   ├── css/               # UI styling
│   ├── js/                # UI logic
│   └── images/            # Flow icons (scatter, retry, error, etc.)
├── templates/
│   ├── index.html         # Landing page
│   ├── login.html         # Auth screen (if enabled)
│   └── workflow.html      # Flow visualization UI
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
└── README.md              # Project documentation
```

---

## Trace Event Model

Each trace event is expected to be **JSON‑structured** and minimally contain:

```json
{
  "trace_id": "uuid",
  "flow_name": "order-processing",
  "component": "http:listener",
  "event_type": "START | END | ERROR",
  "timestamp": "ISO‑8601",
  "metadata": {
    "attempt": 1,
    "payload_size": 1024
  }
}
```

This allows Flow Trace to:
- Correlate steps
- Reconstruct execution order
- Detect retries and failures

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/flow-trace.git
cd flow-trace
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=flow-trace
FLASK_ENV=production
SECRET_KEY=change-me
```

> ⚠️ Never commit `.env` files to version control.

---

## Running the Application

### Development

```bash
python app.py
```

### Production (Gunicorn)

```bash
gunicorn wsgi:app
```

Access the UI at:

```
http://localhost:5000
```

---

## UI Walkthrough

- **Trace List View** – Displays all available trace IDs
- **Flow Canvas** – Visual execution graph
- **Node Details Panel** – Metadata, payload size, timing
- **Error Highlighting** – Failed nodes rendered distinctly

Icons are mapped to common integration constructs such as:
- HTTP Listener
- Transform
- Scatter‑Gather
- Try / Catch
- Until‑Successful
- Sub‑Flows

---

## Security & Best Practices

- No credentials stored in code
- Environment‑based configuration
- Read‑only Elasticsearch access recommended
- Branch protection enabled for public repo

---

## Extending Flow Trace

You can extend Flow Trace by:
- Adding new component icon mappings
- Supporting OpenTelemetry events
- Adding trace comparison view
- Introducing role‑based access

---

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Please include clear commit messages and documentation updates.

---

## License

MIT License – free to use, modify, and distribute.

---

## Author & Vision

Flow Trace was built to **demystify complex integration flows** and give teams **clarity, confidence, and control** over their distributed systems.

If this project helped you, consider ⭐ starring the repository and sharing feedback.

