# MuleSoft Tracing Platform (Mule → Artemis MQ → Logstash → Elasticsearch → UI)

This repository contains the implementation of a **generic tracing platform** originally built around MuleSoft, but designed to be **platform-agnostic**.  
It enables **end-to-end visual tracing** of integration flows using:

- MuleSoft JSON Logger (or any JSON-emitting producer)
- Apache Artemis MQ
- Logstash JMS pipeline
- Elasticsearch
- A Python-based visual trace UI (block-diagram style)

The platform lets you trace a request across multiple steps and systems, inspect payloads, headers, and variables, and quickly identify failures and bottlenecks.

---

## ✨ Key Features

- **Cross-system trace model** – not limited to MuleSoft
- **Correlation ID–based tracing** across multiple steps
- **Visual block diagram UI** (Python) for each trace
- **Asynchronous, decoupled pipeline** via Apache Artemis MQ
- **Normalized Elasticsearch schema** for querying and analytics
- **Logstash filter pipeline** with strict whitelisting & validation
- Ready for **multi-environment** and **multi-API** setups

---

## 🧱 High-Level Architecture

```text
MuleSoft / Other Apps
   │
   │  JSON trace events (JMS / HTTP / TCP)
   ▼
+-----------------------+
|   Apache Artemis MQ   |
|  Queue: dev.es.audit. |
|         flow.trace    |
+-----------------------+
            │
            ▼
+-----------------------+
|       Logstash        |
|  JMS / TCP / HTTP     |
|  Filters & Output     |
+-----------------------+
            │
            ▼
+-------------------------------+
|        Elasticsearch          |
|  dev-mule-flow-trace-* index  |
+-------------------------------+
            │
            ▼
+-------------------------------+
|     Python Trace UI (Web)     |
|  Visual flow block diagrams   |
+-------------------------------+
