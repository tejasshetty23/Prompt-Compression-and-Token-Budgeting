# Benchmark Dataset Specification and Provenance

## 1. Overview
The benchmark dataset consists of 60 curated incident investigation cases designed to rigorously evaluate prompt compression and token budgeting using LLMLingua-2. The dataset is a curated synthetic benchmark designed to resemble telemetry, diagnostic logs, and postmortem records. It is not a collection of production incident records, and no external production provenance is claimed.

## 2. Dataset Composition
The dataset contains exactly 60 cases divided equally across three core downstream LLM evaluation tasks:

| Task Type | Case Count | Case IDs | Primary Evaluation Metric | Secondary Metrics |
| :--- | :---: | :--- | :--- | :--- |
| **Extractive QA** | 20 | `extract-001` - `extract-020` | Exact Match (EM) | Token F1 |
| **Multi-Hop QA** | 20 | `multi-001` - `multi-020` | Token F1 | ROUGE-L, Semantic Coverage |
| **Summarization**| 20 | `summary-001` - `summary-020` | ROUGE-L | ROUGE-1, ROUGE-2 |

## 3. Incident Taxonomy & Coverage
The dataset spans 9 major enterprise infrastructure and system archetypes:
1. **Container Orchestration & Kubernetes**: Pod crashes (OOMKilled exit 137, CrashLoopBackOff), CNI IP exhaustion, kubelet eviction policies, ingress certificate management, and Helm rollbacks.
2. **Distributed Messaging & Streaming**: Apache Kafka broker disk exhaustion, consumer group rebalance lag, partition leader lockups, and RabbitMQ network partitions / memory high watermarks.
3. **Relational & NoSQL Databases**: PostgreSQL transaction ID wraparound risks, HikariCP connection pool starvation, streaming replication lag, Cassandra tombstone saturation, and ClickHouse read-only disk fills.
4. **Caching & In-Memory Stores**: Redis cluster split-brain failover, `noeviction` OOM set rejections, and Memcached socket connection leaks.
5. **Networking & Cloud Infrastructure**: BGP route flapping / ISP prefix leaks, IPsec VPN tunnel phase-2 re-keying certificate expiry, CoreDNS resolution storms, and AWS Direct Connect fiber cut failover.
6. **API Gateways & Ingress Traffic**: HTTP 503 circuit breaking, HTTP 504 gateway timeouts, Envoy cascading thread exhaustion, and edge firewall rate limiting (HTTP 429).
7. **Identity, Security & IAM**: Expired TLS certificates, AWS IAM role permission stripping (drift correction), and corporate NAT gateway IP rotation blocking SMTP/OAuth relays.
8. **CI/CD & Release Engineering**: Docker Hub unauthenticated rate limits, container registry filesystem saturation, and database schema migration table lockouts.
9. **Search & Analytics Engines**: Elasticsearch JVM garbage collection pauses, split-brain master node elections, and unassigned replica shards.

## 4. Task Specifications and Reference Standards

### A. Extractive QA
* **Objective**: Evaluate retrieval of precise operational entities under token reduction.
* **Question Archetypes**: Specific error codes, IP addresses, namespaces, timestamps, volume names, commit hashes, and component names.
* **Ground Truth**: Ground-truth strings are canonical target answers defined for the curated synthetic cases.

### B. Multi-Hop QA
* **Objective**: Evaluate retention of causal relationships, cross-event temporal sequences, and multi-component dependencies.
* **Question Archetypes**: Requires synthesizing at least two distinct events (e.g., initial root cause $\to$ intermediate failure symptom $\to$ administrative intervention $\to$ system stabilization).
* **Ground Truth**: Comprehensive, factual statements detailing both the initiating cause and the exact remediation action.

### C. Summarization
* **Objective**: Evaluate retention of overarching incident narrative under severe token compression.
* **Structure**: Each summary covers four canonical postmortem facets:
  1. *Cause*: Initiating fault or configuration defect.
  2. *Impact*: Affected services, user symptoms, and degraded metrics.
  3. *Resolution*: SRE/engineering mitigation and corrective patch.
  4. *Outcome*: Verification of service recovery, data integrity, and preventive follow-ups.

## 5. Token Statistics
* **Mean Context Length**: 165.4 tokens (tiktoken `cl100k_base`).
* **Minimum Context Length**: 130 tokens.
* **Maximum Context Length**: 218 tokens.
* **Standard Deviation**: 22.8 tokens.
* **Preservation Guarantees**: System instructions and user questions are preserved intact at all times; token compression and budgeting operate exclusively on context.
