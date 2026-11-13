"""Construct the expanded 60-case enterprise incident benchmark dataset.

Covers 20 Extractive QA, 20 Multi-hop QA, and 20 Summarization cases
across diverse infrastructure archetypes: Kubernetes, Kafka, PostgreSQL,
Redis, CoreDNS, OAuth/IAM, gRPC microservices, CI/CD pipelines, and cloud networking.
"""
import json
from pathlib import Path
from prompt_budget.tokenization import count_tokens

cases = [
    # =========================================================================
    # EXTRACTIVE QA (20 cases: extract-001 to extract-020)
    # =========================================================================
    {
        "id": "extract-001",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which service returned HTTP 503?",
        "context": "2026-10-01 09:00:02 INFO api-gateway accepted request id R-441. 2026-10-01 09:00:03 INFO auth-service validated the session. 2026-10-01 09:00:04 INFO inventory-service queried warehouse stock. 2026-10-01 09:00:05 WARN inventory-service retry 1 of 3 after upstream timeout. 2026-10-01 09:00:06 WARN inventory-service retry 2 of 3 after upstream timeout. 2026-10-01 09:00:07 ERROR inventory-service returned HTTP 503 after three retries. 2026-10-01 09:00:08 WARN api-gateway opened its circuit breaker for inventory requests. 2026-10-01 09:00:09 INFO notification-service remained healthy. The checkout page continued to load, but stock availability could not be refreshed. The on-call engineer began investigating the inventory dependency.",
        "reference": "inventory-service"
    },
    {
        "id": "extract-002",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "At what time did payment processing return to normal?",
        "context": "2026-10-03 09:15 INFO payment-api latency increased above the alert threshold. 09:18 WARN database connection pool reached its configured maximum. 09:22 ERROR new payment requests began timing out. 09:31 INFO the on-call engineer identified an incorrect pool limit in the deployment configuration. 09:42 INFO the pool limit was increased from 20 to 60 connections and the payment-api service was restarted. 09:55 INFO database connection wait time began decreasing. 10:05 INFO payment processing returned to normal. 10:12 INFO the team confirmed that no customer payment records were permanently lost. Other services, including email and reporting, remained healthy throughout the incident.",
        "reference": "10:05"
    },
    {
        "id": "extract-003",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which Kubernetes namespace contained the failing worker?",
        "context": "2026-10-04 14:00 INFO cluster autoscaler completed a routine check. 14:03 INFO batch-worker deployment started a rolling update. 14:04 WARN pod batch-worker-7d9f entered CrashLoopBackOff. 14:05 ERROR container exited with code 137 after exceeding its memory limit. 14:07 INFO platform engineer inspected pod metadata and confirmed namespace data-processing. 14:10 INFO the team compared memory usage across worker replicas. 14:15 INFO a separate analytics-worker in namespace analytics continued processing normally. 14:20 INFO the failed pod remained isolated while the deployment was paused.",
        "reference": "data-processing"
    },
    {
        "id": "extract-004",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "How many messages were waiting in the notification queue at 11:30?",
        "context": "2026-10-05 11:00 INFO notification scheduler started normally. 11:05 INFO email-provider response time increased to 2.4 seconds. 11:10 WARN notification queue began accumulating messages. 11:15 INFO queue depth reached 420 messages. 11:20 WARN retry policy delayed delivery attempts for temporary provider errors. 11:25 INFO engineers confirmed that SMS delivery was unaffected. 11:30 INFO notification queue depth measured 680 messages. 11:35 INFO provider response time returned below one second. 11:40 INFO queue drain rate exceeded the incoming message rate. 11:48 INFO all queued notifications were delivered.",
        "reference": "680"
    },
    {
        "id": "extract-005",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What was the exit code of the crashed container in pod order-worker-99a?",
        "context": "2026-10-14 02:12:00 INFO kubelet detected container state change on node worker-k8s-node-04. 2026-10-14 02:12:05 WARN container order-worker in pod order-worker-99a consumed 4096MiB exceeding limits. 2026-10-14 02:12:06 ERROR container terminated by Linux OOM killer with exit code 137. 2026-10-14 02:12:15 INFO kubelet scheduled pod restart with backoff. 2026-10-14 02:13:00 INFO platform team verified persistent volume claims pvc-order-data remained bound without corruption.",
        "reference": "137"
    },
    {
        "id": "extract-006",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which host IP address triggered the firewall rate limit ban?",
        "context": "2026-10-14 04:30:11 INFO edge-waf ingress traffic rate was 14,200 req/sec. 2026-10-14 04:30:15 WARN suspicious credential stuffing activity detected on /api/v2/auth/login. 2026-10-14 04:30:18 ERROR client 198.51.100.42 exceeded sliding window threshold with 850 failed authentication attempts in 10 seconds. 2026-10-14 04:30:19 INFO edge-waf firewall added IP 198.51.100.42 to temporary drop table rule-drop-992 for 3600 seconds. 2026-10-14 04:30:25 INFO login failure rate normalized to 0.4 percent.",
        "reference": "198.51.100.42"
    },
    {
        "id": "extract-007",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What HTTP status code did the billing gateway return to the client?",
        "context": "2026-10-15 11:22:01 INFO invoice-service dispatched payment capture request req-9910 to stripe-proxy. 2026-10-15 11:22:04 WARN stripe-proxy TLS socket handshake stalled at 3000ms. 2026-10-15 11:22:08 ERROR stripe-proxy upstream connection closed prematurely; returned HTTP 504 to caller invoice-service. 2026-10-15 11:22:10 INFO invoice-service queued payment retry job in dead-letter queue dlq-invoices. 2026-10-15 11:25:00 INFO customer ledger maintained read consistency.",
        "reference": "HTTP 504"
    },
    {
        "id": "extract-008",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What was the replication lag duration reported for replica database db-replica-3?",
        "context": "2026-10-15 14:05:00 INFO db-orchestrator polled PostgreSQL streaming replication slots. 2026-10-15 14:05:30 WARN wal receiver process on db-replica-3 stalled behind master LSN 0/1400A230. 2026-10-15 14:06:12 ERROR db-replica-3 replication lag reached 1240 seconds exceeding the SLO threshold of 60 seconds. 2026-10-15 14:07:00 INFO load balancer removed db-replica-3 from read pool ro-db-pool. 2026-10-15 14:15:00 INFO network congestion resolved and replica caught up to within 1 second.",
        "reference": "1240 seconds"
    },
    {
        "id": "extract-009",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which certificate common name expired according to cert-manager logs?",
        "context": "2026-10-16 00:01:05 INFO cert-manager cron checked validity of 48 cluster certificates. 2026-10-16 00:01:10 ERROR x509 validation failure: certificate api.internal.payments.net expired at 2026-10-16T00:00:00Z. 2026-10-16 00:01:15 WARN microservices attempting mTLS connections to payment cluster rejected handshakes with SEC_ERROR_EXPIRED_CERTIFICATE. 2026-10-16 00:03:00 INFO security engineer triggered Vault PKI ACME issuer renewal. 2026-10-16 00:05:30 INFO updated secret cert-api-internal distributed to all namespaces.",
        "reference": "api.internal.payments.net"
    },
    {
        "id": "extract-010",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What is the name of the persistent volume claim that reached 100 percent capacity?",
        "context": "2026-10-16 08:44:19 INFO prometheus alert manager evaluated storage alerts. 2026-10-16 08:44:22 ERROR volume pvc-kafka-broker-02 reached 100 percent inode and byte capacity (500GiB / 500GiB). 2026-10-16 08:44:25 WARN Kafka broker-2 switched active log segments to read-only state and dropped out of ISR for topic telemetry-events. 2026-10-16 08:46:00 INFO storage administrator expanded AWS EBS volume to 1000GiB and executed resize2fs. 2026-10-16 08:52:00 INFO broker-2 resumed log ingestion.",
        "reference": "pvc-kafka-broker-02"
    },
    {
        "id": "extract-011",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What port number was the redis cache sentinel listening on?",
        "context": "2026-10-17 03:15:10 INFO redis-ha cluster initialized health check across 3 sentinel instances. 2026-10-17 03:15:12 INFO sentinel-1 active on 10.0.12.10:26379 monitoring master redis-master. 2026-10-17 03:15:15 WARN master 10.0.12.5:6379 failed ping with timeout after 5000ms. 2026-10-17 03:15:20 INFO sentinel quorum elected new master at 10.0.12.6:6379. 2026-10-17 03:16:00 INFO application clients reconnected to new primary.",
        "reference": "26379"
    },
    {
        "id": "extract-012",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which git commit hash was identified as introducing the memory leak?",
        "context": "2026-10-17 10:14:00 INFO git-bisect pipeline automated run completed for service user-profile. 2026-10-17 10:14:30 INFO commit 4a9f1b2 introduced unclosed RocksDB snapshot iterator causing RSS memory to increase by 50MB per hour. 2026-10-17 10:15:00 WARN staging deployment memory reached 92 percent threshold. 2026-10-17 10:16:00 INFO developer reverted commit 4a9f1b2 and initiated pull request pr-482 with explicit iterator close call in finally block.",
        "reference": "4a9f1b2"
    },
    {
        "id": "extract-013",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "How many thread pool workers were configured in the blocked thread pool?",
        "context": "2026-10-18 13:20:00 INFO tomcat container worker status checked. 2026-10-18 13:20:04 WARN thread pool Catalina-exec reached 200 of 200 active threads with 0 idle. 2026-10-18 13:20:10 ERROR incoming HTTP requests queued up to maximum backlog depth of 500; new connections rejected with ECONNREFUSED. 2026-10-18 13:22:00 INFO thread dump revealed 194 threads waiting on lock in LDAPAuthenticationProvider. 2026-10-18 13:25:00 INFO LDAP connection timeout configured from 0 to 3000ms.",
        "reference": "200"
    },
    {
        "id": "extract-014",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What is the name of the AWS S3 bucket that returned HTTP 403 Forbidden errors?",
        "context": "2026-10-18 18:02:11 INFO backup-agent started daily incremental snapshot backup. 2026-10-18 18:02:15 ERROR PutObject call to target bucket production-db-backups-us-east-1 returned HTTP 403 Access Denied. 2026-10-18 18:03:00 WARN backup process halted with status FAILED. 2026-10-18 18:05:00 INFO IAM policy inspection showed role backup-runner-role was missing s3:PutObjectTagging action. 2026-10-18 18:08:00 INFO IAM policy updated and backup retried successfully.",
        "reference": "production-db-backups-us-east-1"
    },
    {
        "id": "extract-015",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What was the peak CPU utilization percentage observed on host db-shard-08?",
        "context": "2026-10-19 07:45:00 INFO node-exporter recorded system metrics on analytics cluster. 2026-10-19 07:45:20 WARN db-shard-08 system load average spiked to 64.2 on a 32-core system. 2026-10-19 07:46:00 ERROR db-shard-08 CPU utilization registered 99.4 percent due to missing index on table daily_financial_ledger. 2026-10-19 07:48:00 INFO database administrator created index concurrently idx_ledger_account_created. 2026-10-19 07:51:00 INFO CPU utilization dropped to 14.2 percent.",
        "reference": "99.4 percent"
    },
    {
        "id": "extract-016",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which Kafka consumer group stalled during topic ingestion?",
        "context": "2026-10-19 12:10:00 INFO kafka-lag-exporter monitored consumer offset commits on cluster c4. 2026-10-19 12:10:15 WARN consumer group order-processing-group-v2 offset lag exceeded 250,000 records. 2026-10-19 12:10:30 ERROR consumer partition 4 assignment revoked following HeartbeatTimeoutException from worker host worker-12. 2026-10-19 12:12:00 INFO cluster coordinator initiated consumer group rebalance. 2026-10-19 12:14:00 INFO worker-12 restarted and lag cleared.",
        "reference": "order-processing-group-v2"
    },
    {
        "id": "extract-017",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What is the DNS domain that CoreDNS failed to resolve during the network blip?",
        "context": "2026-10-20 01:10:02 INFO CoreDNS pod coredns-67f89d received 4,500 queries per second. 2026-10-20 01:10:05 ERROR upstream resolver 169.254.169.253 timed out for domain auth.okta.enterprise.internal. 2026-10-20 01:10:08 WARN api-server authentication webhook received SERVFAIL for token review requests. 2026-10-20 01:11:00 INFO VPC DNS endpoint health check recovered. 2026-10-20 01:12:00 INFO CoreDNS cache repopulated with TTL 300.",
        "reference": "auth.okta.enterprise.internal"
    },
    {
        "id": "extract-018",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What was the disk I/O queue length recorded on the SAN storage array?",
        "context": "2026-10-20 06:12:10 INFO SAN storage array NetApp-Filer-01 latency alert triggered. 2026-10-20 06:12:14 ERROR read latency climbed to 420ms; disk I/O queue length reached 148 requests. 2026-10-20 06:12:20 WARN virtual machine hypervisor esxi-host-03 experienced datastore latency warnings. 2026-10-20 06:15:00 INFO storage engineer discovered runaway unthrottled pg_dump process running on vm-reports-01. 2026-10-20 06:16:00 INFO backup job throttled via ionice -c3 and queue length normalized to 2.",
        "reference": "148"
    },
    {
        "id": "extract-019",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "Which gRPC status code was returned by auth-service during the token verification storm?",
        "context": "2026-10-20 15:40:00 INFO gateway envoy-proxy routed incoming gRPC traffic to auth-service. 2026-10-20 15:40:10 WARN auth-service token validator exhausted Redis connection pool. 2026-10-20 15:40:15 ERROR auth-service returned gRPC status DEADLINE_EXCEEDED (code 4) for 2,400 consecutive VerifyToken RPC calls. 2026-10-20 15:42:00 INFO envoy circuit breaker tripped and ejected unhealthy upstream endpoints. 2026-10-20 15:44:00 INFO Redis connection timeout raised and endpoints recovered.",
        "reference": "DEADLINE_EXCEEDED"
    },
    {
        "id": "extract-020",
        "task": "extractive_qa",
        "system_instruction": "Answer using only the supplied context. Return the exact value requested. If it is not present, answer unknown.",
        "question": "What was the name of the failing Helm release rolled back by the platform team?",
        "context": "2026-10-21 11:00:00 INFO ArgoCD sync started for application release release-checkout-v3. 2026-10-21 11:00:30 ERROR deployment checkout-deployment failed readiness probe http-get on port 8080. 2026-10-21 11:01:00 WARN helm release release-checkout-v3 entered state FAILED_ROLLOUT. 2026-10-21 11:02:00 INFO automated rollback triggered; restored helm revision 42 of release-checkout-v3. 2026-10-21 11:03:30 INFO pods in namespace production became Ready 3/3.",
        "reference": "release-checkout-v3"
    },

    # =========================================================================
    # MULTI-HOP QA (20 cases: multi-001 to multi-020)
    # =========================================================================
    {
        "id": "multi-001",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the checkout errors, and what change resolved them?",
        "context": "2026-10-06 08:40 INFO checkout-api deployment v2.8 completed. 08:44 INFO checkout requests increased after a marketing campaign. 08:47 WARN database connection pool utilization reached 100 percent. 08:49 ERROR checkout-api returned intermittent HTTP 500 responses while waiting for database connections. 08:55 INFO catalog-api remained healthy and product pages loaded normally. 09:02 INFO the engineer compared the deployment configuration with the previous release. 09:08 INFO the new release had reduced the database pool maximum from 80 to 20. 09:16 INFO the team restored the pool maximum to 80 and restarted checkout-api. 09:23 INFO database wait time fell and checkout error rate returned to baseline. 09:30 INFO the team added a configuration review to the release checklist.",
        "reference": "The checkout errors were caused by the database connection pool being reduced from 80 to 20 in release v2.8, exhausting connections during increased traffic. Restoring the pool maximum to 80 and restarting checkout-api resolved the issue."
    },
    {
        "id": "multi-002",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why were reports delayed, and which upstream dependency caused the delay?",
        "context": "2026-10-07 02:00 INFO nightly reporting job started. 02:04 INFO report-builder requested customer events from event-store. 02:06 WARN event-store replication lag increased to 47 minutes. 02:10 INFO report-builder waited for the latest event watermark before generating daily totals. 02:18 ERROR reporting job exceeded its expected completion window. 02:22 INFO data engineer inspected the replication monitor and found a stopped replica consumer after a broker rebalance. 02:29 INFO the consumer was restarted and began processing the backlog. 02:44 INFO replication lag decreased to 12 minutes. 02:56 INFO event-store reached the latest watermark. 03:02 INFO report-builder completed the delayed reports. Billing database and email delivery metrics remained normal.",
        "reference": "Reports were delayed because report-builder waited for current customer events while event-store replication was 47 minutes behind. The upstream dependency was event-store; its replica consumer had stopped after a broker rebalance. Restarting the consumer cleared the backlog and allowed reports to finish."
    },
    {
        "id": "multi-003",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Which component triggered the login failures, and how did the team restore login service?",
        "context": "2026-10-08 16:10 INFO web frontend served login page successfully. 16:12 INFO identity-api received authentication requests. 16:13 ERROR identity-api reported TLS handshake failures to secrets-proxy. 16:16 WARN certificate validation failed because the secrets-proxy certificate had expired. 16:20 INFO engineers verified that user passwords and identity database records were unaffected. 16:24 INFO secrets-proxy was confirmed as the endpoint presenting the expired certificate. 16:31 INFO platform team renewed and deployed the certificate. 16:36 INFO identity-api completed successful TLS handshakes. 16:40 INFO login success rate returned to normal. 16:45 INFO monitoring confirmed no further certificate errors.",
        "reference": "The secrets-proxy component triggered login failures by presenting an expired TLS certificate, which caused identity-api handshakes to fail. The team renewed and deployed the certificate, after which identity-api handshakes and login success rates returned to normal."
    },
    {
        "id": "multi-004",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the image-processing backlog, and what action cleared it?",
        "context": "2026-10-09 12:00 INFO image-upload service accepted 1,200 files. 12:03 INFO processing queue depth began increasing. 12:07 WARN image-worker CPU utilization remained below 40 percent. 12:10 ERROR image-worker could not fetch tasks from task-broker because its consumer group was unauthorized. 12:14 INFO security audit showed that a service account rotation had removed the consume permission. 12:19 INFO upload storage remained healthy and new files continued to arrive. 12:25 INFO platform engineer restored consume permission for the image-worker service account. 12:29 INFO workers resumed fetching tasks from task-broker. 12:41 INFO queue depth began falling. 12:58 INFO all pending images completed processing. 13:05 INFO team added a permission check to the service-account rotation procedure.",
        "reference": "The image-processing backlog occurred because service-account rotation removed the image-worker's consume permission on task-broker, preventing workers from fetching tasks. Restoring that permission allowed workers to resume processing and clear the backlog."
    },
    {
        "id": "multi-005",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did order processing halt, and what infrastructure intervention brought it back online?",
        "context": "2026-10-21 04:00:10 INFO order-pipeline accepted 500 order events per second. 04:02:15 WARN disk write latency on primary disk array storage-node-01 jumped from 2ms to 850ms. 04:03:00 ERROR statefulset pod order-processor-0 failed liveness probe because write transactions to storage-node-01 timed out. 04:05:00 WARN kubernetes statefulset operator placed order-processor-0 into Terminating state but could not unmount the EBS volume due to an active kernel lock. 04:08:00 INFO platform on-call engineer identified the hung SCSI mount on underlying node host-k8s-worker-19. 04:12:00 INFO engineer cordoned host-k8s-worker-19, forcefully detached the EBS volume via AWS CLI, and terminated the unresponsive node. 04:15:30 INFO Kubernetes reattached volume to host-k8s-worker-22 and order-processor-0 transitioned to Running, clearing order backlog.",
        "reference": "Order processing halted because storage-node-01 disk latency surged to 850ms, causing order-processor-0 liveness timeouts and a hung EBS volume mount lock on host-k8s-worker-19. The team cordoned the node, forcefully detached the volume via AWS CLI, terminated the node, and let Kubernetes reschedule the pod on host-k8s-worker-22."
    },
    {
        "id": "multi-006",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "How did an upstream network policy update lead to billing charge duplicates, and how was it corrected?",
        "context": "2026-10-21 09:10:00 INFO security team applied network policy netpol-strict-egress to billing namespace. 09:12:15 WARN payment-service could connect to bank gateway but ingress ACK packets were blocked by netpol-strict-egress due to a missing port 443 ingress return rule. 09:13:30 ERROR payment-service treated unacknowledged TCP connections as network timeouts and executed immediate charge retries without an idempotency key. 09:15:00 WARN 142 customers were charged duplicate amounts on credit cards. 09:22:00 INFO network engineer diagnosed dropping of return packets in Calico CNI flow logs. 09:28:00 INFO netpol-strict-egress was patched to allow stateful return traffic, and payment-service was updated to inject idempotency keys on all outgoing requests.",
        "reference": "A strict network policy blocked return ingress ACK packets from the bank gateway, leading payment-service to misinterpret timeouts and issue duplicate charge retries without idempotency keys. Engineers fixed the issue by patching the network policy to allow stateful return traffic and updating payment-service to use idempotency keys."
    },
    {
        "id": "multi-007",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What chain of events led to the DNS resolution storm, and what two actions stopped it?",
        "context": "2026-10-22 11:00:00 INFO search-api was deployed with 150 pod replicas. 11:02:00 WARN search-api microservice was configured with ndots:5 in /etc/resolv.conf and lacked DNS connection pooling. 11:03:30 ERROR each search query triggered 5 sequential DNS lookups for internal service discovery, bombarding CoreDNS with 180,000 queries/second. 11:05:00 ERROR CoreDNS CPU hit 100 percent, dropping packet buffers and causing cluster-wide name resolution failures. 11:10:00 INFO platform team deployed NodeLocal DNSCache daemonset across the cluster to intercept local queries. 11:15:00 INFO engineers changed search-api ndots configuration from 5 to 2 and enabled connection keep-alive in client gRPC channels, dropping CoreDNS query volume back to 4,000 queries/second.",
        "reference": "Search-api pods with ndots:5 and no DNS connection pooling made 5 sequential DNS lookups per query, creating a 180,000 queries/sec storm that overwhelmed CoreDNS. The storm was stopped by deploying NodeLocal DNSCache across the cluster and reducing ndots from 5 to 2 with gRPC connection keep-alive enabled."
    },
    {
        "id": "multi-008",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did customer analytics dashboards show stale data, and which specific service fix restored live ingestion?",
        "context": "2026-10-22 17:30:00 INFO analytics-pipeline read events from topic clickstream-data. 17:35:00 WARN analytics-consumer reported schema registry HTTP 404 for schema ID 941. 17:36:00 ERROR frontend telemetry service deployed version v3.14 that introduced a new nested field in event payloads without registering the schema with Confluent Schema Registry. 17:40:00 WARN analytics-consumer discarded unregistered payloads into dead-letter storage, stopping real-time aggregation updates on customer dashboards. 17:52:00 INFO pipeline on-call contacted frontend team who acknowledged skipping the CI schema compatibility check. 18:05:00 INFO frontend team registered schema ID 941 in compatibility backward mode and re-enabled schema CI verification in pipeline gitlab-ci.",
        "reference": "Customer dashboards showed stale data because the frontend telemetry service deployed an unversioned schema with a nested field without registering it with Schema Registry, causing analytics-consumer to reject events with HTTP 404. Live ingestion was restored when the frontend team registered schema ID 941 in Schema Registry and reinstated the CI schema compatibility check."
    },
    {
        "id": "multi-009",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the search service outage, and how did the engineering team recover query performance?",
        "context": "2026-10-23 03:00:00 INFO nightly index optimization cron triggered on Elasticsearch cluster es-search-prod. 03:05:00 WARN heavy segment merging collided with an unexpected bulk re-indexing script executed by data science team. 03:08:00 ERROR JVM garbage collection pauses exceeded 45 seconds on 3 master-eligible nodes, causing split-brain cluster state. 03:10:00 ERROR search-api requests failed with 503 No Alive Nodes. 03:25:00 INFO on-call team killed the data science bulk ingestion script. 03:32:00 INFO engineers manually restarted the 3 master nodes sequentially and increased discovery.zen.minimum_master_nodes to prevent split-brain election. 03:45:00 INFO cluster state turned GREEN and search query latency returned to 22ms.",
        "reference": "The search outage occurred when segment merging coincided with an unthrottled bulk re-indexing script, causing 45-second JVM GC pauses and a split-brain cluster state on Elasticsearch master nodes. The team killed the re-indexing script, restarted the master nodes sequentially, and adjusted discovery.zen.minimum_master_nodes to stabilize the cluster."
    },
    {
        "id": "multi-010",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did Kafka message delivery stall, and what change to disk quotas restored broker replication?",
        "context": "2026-10-23 08:00:00 INFO Kafka cluster kafka-prod-us-west received 40MB/s telemetry data. 08:05:00 WARN broker-03 disk space utilization crossed 95 percent watermark. 08:07:00 ERROR log cleaner thread crashed on broker-03 due to an unhandled corrupt index file in partition metrics-events-14. 08:12:00 WARN broker-03 stopped compacting logs, allowing disk space to reach 100 percent full, which forced broker-03 to shutdown immediately. 08:18:00 ERROR min.insync.replicas constraint failed for topics with replication factor 3, blocking all producer writes. 08:30:00 INFO storage engineer purged expired temporary dump logs and deleted the corrupt index file. 08:35:00 INFO engineer restarted broker-03 and lowered retention.hours from 72 to 24 hours, stabilizing disk utilization at 62 percent.",
        "reference": "Kafka message delivery stalled because broker-03's log cleaner crashed on a corrupt index file, allowing the disk to fill to 100 percent and shutting down the broker, which violated min.insync.replicas constraints. Purging temporary logs, removing the corrupt index, and reducing retention.hours from 72 to 24 restored broker replication."
    },
    {
        "id": "multi-011",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the Redis cache failure, and how was high availability recovered?",
        "context": "2026-10-23 14:15:00 INFO redis-cluster-cache received 95,000 operations per second. 14:18:00 WARN key eviction policy was set to noeviction while memory approached maxmemory limit of 32GB. 14:20:00 ERROR redis-master rejected all SET operations with OOM command not allowed when used memory > maxmemory. 14:22:00 WARN web sessions were unable to be saved, redirecting users back to the login page repeatedly. 14:35:00 INFO SRE modified redis configuration dynamically via CONFIG SET maxmemory-policy allkeys-lru. 14:37:00 INFO Redis freed 6.4GB of expired and inactive session keys within 30 seconds. 14:40:00 INFO web session creation succeeded and normal operation resumed.",
        "reference": "The Redis cache failed because the memory policy was set to noeviction and memory reached its 32GB limit, causing Redis to reject write operations with OOM errors and breaking web sessions. Changing the eviction policy to allkeys-lru freed 6.4GB of inactive keys and restored normal caching."
    },
    {
        "id": "multi-012",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "How did a database migration error affect API requests, and what migration rollback was performed?",
        "context": "2026-10-24 01:00:00 INFO db-migration job migration-v42 executed ALTER TABLE users ADD COLUMN social_security_id VARCHAR NOT NULL. 01:02:00 ERROR the non-nullable column addition without a default value locked table users exclusively for table rewrite. 01:04:00 ERROR API server threads waiting on user records stacked up behind the ACCESS EXCLUSIVE lock; API response latency rose from 15ms to 12,000ms. 01:07:00 WARN health checks failed across 24 api-gateway pods, triggering automatic container evictions. 01:12:00 INFO database administrator identified the blocking migration query in pg_stat_activity and executed pg_terminate_backend on the migration session. 01:15:00 INFO migration was rolled back and re-applied using a multi-step nullable addition with concurrent index creation.",
        "reference": "A database migration attempted to add a NOT NULL column without a default value, acquiring an ACCESS EXCLUSIVE lock on table users that blocked all API server threads and triggered container health check failures. The DBA terminated the blocking migration session via pg_terminate_backend and re-architected the migration using nullable steps."
    },
    {
        "id": "multi-013",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did notification emails fail to send, and what third-party provider settings change resolved the problem?",
        "context": "2026-10-24 08:30:00 INFO email-dispatcher received 12,000 password reset requests. 08:32:00 WARN SendGrid SMTP relay returned 451 Authentication failed: IP address unallocated. 08:34:00 ERROR emails queued into memory until buffer memory reached 98 percent. 08:38:00 INFO investigations revealed that the corporate cloud provider had rotated the outgoing NAT Gateway Elastic IP during a maintenance window without updating the SendGrid IP allowlist. 08:45:00 INFO DevOps team obtained the new Elastic IP 52.14.88.109 and registered it in the SendGrid Security Whitelist portal. 08:50:00 INFO SendGrid accepted the relay connections and 11,800 queued emails were successfully delivered within 6 minutes.",
        "reference": "Notification emails failed because a cloud provider maintenance window rotated the NAT Gateway Elastic IP without updating SendGrid's IP allowlist, causing SendGrid to reject SMTP connections with 451 Authentication failed. Registering the new Elastic IP 52.14.88.109 in SendGrid's whitelist portal re-established authentication and cleared the email queue."
    },
    {
        "id": "multi-014",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the Cassandra write timeouts, and what compaction strategy change stabilized the cluster?",
        "context": "2026-10-24 16:00:00 INFO Cassandra cluster cassandra-events processed 45,000 writes/sec. 16:10:00 WARN coordinator node 10.200.4.12 reported WriteTimeoutException on keyspace user_sessions. 16:15:00 ERROR read queries scanned over 100,000 tombstones per query due to frequent session deletion. 16:22:00 ERROR JVM heap memory on 6 nodes exceeded 92 percent, triggering frequent 12-second stop-the-world pauses. 16:35:00 INFO database engineer executed nodetool upgradesstables and switched compaction strategy from SizeTieredCompactionStrategy to TimeWindowCompactionStrategy. 16:48:00 INFO tombstone cleanup completed and JVM heap consumption dropped back below 45 percent.",
        "reference": "Cassandra write timeouts were caused by excessive tombstones from frequent session deletions triggering massive read scans and 12-second JVM stop-the-world GC pauses. The cluster was stabilized by running nodetool upgradesstables and changing the compaction strategy to TimeWindowCompactionStrategy."
    },
    {
        "id": "multi-015",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did deployment pods get evicted continuously, and what Kubernetes scheduler change fixed the issue?",
        "context": "2026-10-25 02:00:00 INFO Kubernetes node autoscaler scaled cluster down from 20 nodes to 12 nodes during off-peak hours. 02:05:00 WARN remaining worker nodes reached 88 percent memory pressure. 02:08:00 ERROR kubelet on node k8s-node-07 evicted 8 pods from deployment ml-infer-service due to The node was low on resource: memory. 02:12:00 ERROR ml-infer-service pods lacked resource requests and limits, allowing other pods with Guaranteed QoS to starve them. 02:25:00 INFO cluster operator set explicit resource requests (memory: 2Gi, cpu: 1000m) and configured priorityClassName: high-priority for ml-infer-service. 02:35:00 INFO scheduler relocated pods across dedicated compute nodes and eviction cycles ceased.",
        "reference": "Pods were continuously evicted because off-peak cluster downscaling caused memory pressure on remaining nodes, and ml-infer-service lacked resource requests and limits, making it BestEffort and first in line for eviction. Defining explicit resource requests (2Gi memory, 1000m CPU) and a high-priority priorityClass stopped the eviction cycles."
    },
    {
        "id": "multi-016",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the cross-region replication breakdown, and what certificate rotation step repaired the tunnel?",
        "context": "2026-10-25 10:15:00 INFO IPsec VPN tunnel between us-east-1 and eu-central-1 logged phase-2 re-keying attempt. 10:16:30 ERROR StrongSwan daemon on gateway vpn-gw-01 rejected IKE SA proposal due to signature verification failure. 10:18:00 WARN cross-region Kafka MirrorMaker replication stalled, accumulating 4GB of backlog per minute. 10:24:00 INFO security team confirmed the intermediate CA certificate on vpn-gw-01 expired at 10:15:00. 10:32:00 INFO engineers installed new renewed X.509 CA certificate bundle on vpn-gw-01 and restarted ipsec service. 10:35:00 INFO IPsec tunnel established with AES-GCM-256 and MirrorMaker caught up within 18 minutes.",
        "reference": "Cross-region replication broke down because an intermediate CA certificate on VPN gateway vpn-gw-01 expired, causing StrongSwan to reject phase-2 IPsec re-keying and halting Kafka MirrorMaker traffic. Installing the renewed X.509 CA certificate bundle and restarting ipsec restored the tunnel and replication."
    },
    {
        "id": "multi-017",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did the RabbitMQ cluster partition, and what cluster auto-heal setting was applied?",
        "context": "2026-10-25 15:00:00 INFO RabbitMQ 3-node cluster processed 22,000 messages/sec. 15:03:00 WARN transient network split between availability zones us-east-1a and us-east-1b lasted 65 seconds. 15:05:00 ERROR RabbitMQ nodes rabbit@node1 and rabbit@node2 declared mutual network partition Mnesia split-brain. 15:07:00 ERROR queue mirrored queues became desynchronized and client publishers received NO_ROUTE. 15:20:00 INFO messaging team restarted node3 and updated rabbitmq.conf setting cluster_partition_handling = autoheal. 15:30:00 INFO cluster nodes automatically elected a winning partition, restarted the minority node, and resynchronized queues.",
        "reference": "A 65-second cross-AZ network split caused RabbitMQ nodes to enter an uncoordinated Mnesia split-brain partition, desynchronizing mirrored queues and rejecting publisher messages. Configuring cluster_partition_handling = autoheal in rabbitmq.conf allowed the cluster to automatically heal partitions by restarting minority nodes."
    },
    {
        "id": "multi-018",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What caused the customer checkout latency spike, and what database pool resizing resolved it?",
        "context": "2026-10-26 09:00:00 INFO flash sale launched for holiday promotion. 09:02:00 WARN order creation latency jumped from 45ms to 3,400ms. 09:04:00 ERROR checkout-service HikariCP connection pool exhausted: 30 of 30 connections active, 120 threads waiting with timeout 5000ms. 09:06:00 INFO PostgreSQL server CPU utilization was only 18 percent, indicating the database was idle while clients starved for connections. 09:12:00 INFO database team identified HikariCP maximumPoolSize was artificially capped at 30 while RDS instance could support 500 connections. 09:15:00 INFO engineer bumped maximumPoolSize to 120 in application config and performed rolling restart. 09:18:00 INFO thread wait time dropped to 0ms and checkout latency returned to 48ms.",
        "reference": "Checkout latency spiked because HikariCP connection pool was capped at 30 connections, causing 120 client threads to wait and time out even though the database was only at 18 percent CPU. Increasing maximumPoolSize from 30 to 120 and performing a rolling restart eliminated connection starvation and normalized latency."
    },
    {
        "id": "multi-019",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "Why did the CI/CD pipeline fail across all repositories, and what registry proxy update fixed it?",
        "context": "2026-10-26 14:00:00 INFO GitLab CI runner manager triggered 85 scheduled builds across developer repositories. 14:01:30 ERROR container build steps failed with error: toomanyrequests: You have reached your unauthenticated pull rate limit of 100 pulls per 6 hours. 14:03:00 WARN all 85 CI pipelines stalled in Failed status. 14:08:00 INFO DevOps identified that corporate NAT IP was shared across 400 developers and unauthenticated Docker Hub pulls exhausted the quota. 14:15:00 INFO DevOps team deployed an internal Harbor registry proxy with authenticated enterprise credentials and updated Docker daemon mirror configuration daemon.json on all CI runner nodes. 14:25:00 INFO build runners pulled base images from local Harbor cache without rate limits.",
        "reference": "CI/CD pipelines failed because 85 simultaneous builds made unauthenticated Docker Hub pulls from a shared corporate NAT IP, triggering Docker Hub's 100 pulls per 6 hours rate limit. Deploying an internal Harbor registry proxy with enterprise credentials and configuring it as the default daemon mirror on runner nodes resolved the issue."
    },
    {
        "id": "multi-020",
        "task": "multi_hop_qa",
        "system_instruction": "Answer only from the context. Combine the relevant events and state the causal sequence clearly. Do not invent missing facts.",
        "question": "What sequence of events triggered the cascading microservice blackout, and how was the circuit breaker reconfigured?",
        "context": "2026-10-26 20:00:00 INFO recommendation-service experienced localized cache invalidation storm. 20:01:30 WARN recommendation-service latency increased from 10ms to 4,200ms. 20:02:15 ERROR api-gateway had no timeout configured for recommendation-service calls, causing gateway worker threads to freeze waiting for responses. 20:03:00 ERROR api-gateway ran out of file descriptors and dropped health check probes from external load balancers. 20:04:00 WARN external load balancers marked all 12 api-gateway instances UNHEALTHY, blacking out the entire web application. 20:15:00 INFO platform team configured Envoy circuit breaker on api-gateway with a strict 250ms timeout and fall-back to empty recommendation list. 20:20:00 INFO api-gateway threads freed up, load balancers restored instances, and traffic resumed.",
        "reference": "A cache invalidation storm slowed recommendation-service to 4,200ms, and because api-gateway lacked a timeout, its worker threads froze, exhausted file descriptors, and failed external load balancer health checks, causing a total blackout. The team configured an Envoy circuit breaker with a 250ms timeout and fallback responses, freeing gateway threads and restoring traffic."
    },

    # =========================================================================
    # SUMMARIZATION (20 cases: summary-001 to summary-020)
    # =========================================================================
    {
        "id": "summary-001",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the inventory-service incident.",
        "context": "2026-10-10 09:00 INFO api-gateway accepted inventory requests. 09:02 INFO inventory-service queried the warehouse database. 09:04 WARN warehouse database response time rose above 3 seconds. 09:07 WARN inventory-service retried the query three times. 09:09 ERROR inventory-service returned HTTP 503 after the retries failed. 09:10 WARN api-gateway opened the circuit breaker for inventory requests. Customers could still browse product pages, but stock availability was temporarily unavailable at checkout. 09:18 INFO database team found an unoptimized query introduced in the latest inventory release. 09:31 INFO the query was rolled back to the previous version. 09:38 INFO database response time returned below 200 milliseconds. 09:42 INFO inventory-service recovered and the circuit breaker closed. No order records were lost. The team scheduled query-plan review before future releases.",
        "reference": "An unoptimized query in the latest inventory release slowed warehouse database responses, causing inventory-service retries to fail with HTTP 503 and the gateway to open its circuit breaker. Rolling back the query restored database performance and inventory-service availability. Product browsing continued, stock availability was temporarily affected, and no order records were lost."
    },
    {
        "id": "summary-002",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the delayed notification incident.",
        "context": "2026-10-11 10:00 INFO notification scheduler processed its normal workload. 10:05 WARN email-provider latency increased to 4 seconds. 10:08 INFO notification queue began accumulating messages. 10:15 WARN queue depth reached 900 messages and delivery times exceeded five minutes. 10:19 INFO SMS notifications continued to be delivered normally. 10:24 INFO provider status page reported elevated email API latency in the region. 10:37 INFO provider API latency returned to normal. 10:40 INFO notification workers increased queue drain capacity from 50 to 100 messages per minute. 10:52 INFO queue depth returned below 100 messages. 11:03 INFO all delayed email notifications were delivered. No notifications were permanently dropped. The team added provider latency monitoring and a queue-age alert.",
        "reference": "Elevated latency at the external email provider caused the notification queue to grow to 900 messages and delayed email delivery by more than five minutes, while SMS remained unaffected. After provider latency recovered, workers increased queue drain capacity and delivered all pending emails. No notifications were permanently dropped, and additional monitoring was planned."
    },
    {
        "id": "summary-003",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the database failover incident.",
        "context": "2026-10-12 03:14 INFO primary-orders-db reported elevated disk latency. 03:18 WARN replication delay to standby-orders-db reached 90 seconds. 03:21 ERROR primary-orders-db stopped accepting writes after its storage volume became read-only. 03:24 INFO database orchestration initiated failover to standby-orders-db. 03:27 WARN order-api returned temporary errors while reconnecting. 03:32 INFO standby-orders-db was promoted to primary after consistency checks completed. 03:36 INFO order-api re-established connections and write requests succeeded. 03:44 INFO reconciliation found 12 requests that had to be retried; no confirmed orders were lost. 04:00 INFO storage team began replacing the failed primary volume. Read-only analytics queries were unaffected. The incident review requested a lower failover threshold and more frequent replication checks.",
        "reference": "The primary orders database stopped accepting writes after its storage volume became read-only, and replication lag had reached 90 seconds. Orchestration failed over to the standby database; after consistency checks and reconnection, order-api recovered. Twelve requests required retries, but no confirmed orders were lost."
    },
    {
        "id": "summary-004",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the API rate-limit incident.",
        "context": "2026-10-13 13:00 INFO partner-sync job began importing product updates. 13:04 INFO partner API request volume increased to 300 requests per minute. 13:06 WARN partner API rate limit was 120 requests per minute. 13:08 ERROR partner API returned HTTP 429 for excess requests. 13:12 INFO sync worker retried requests immediately, increasing the number of rejected calls. 13:20 INFO engineers identified that exponential backoff was disabled in the worker configuration. 13:27 INFO exponential backoff with jitter was enabled and concurrency was reduced to 40 requests per minute. 13:34 INFO partner API accepted requests normally. 13:48 INFO product sync completed with 18 updates delayed and then successfully retried. No product records were lost. The team added a rate-limit integration test.",
        "reference": "The partner-sync job exceeded the partner API's 120-requests-per-minute limit, producing HTTP 429 errors. Immediate retries worsened the problem because exponential backoff was disabled. Enabling backoff with jitter and reducing concurrency restored successful requests; 18 delayed updates were later completed and no product records were lost."
    },
    {
        "id": "summary-005",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Redis cluster split-brain incident.",
        "context": "2026-10-27 01:15:00 INFO redis-cluster initiated automated slot rebalancing. 01:17:00 WARN network partition separated availability zone A from zones B and C for 4 minutes. 01:18:30 ERROR nodes in zone A elected local master while zone B retained original master, causing split-brain write divergence across slots 0-5460. 01:21:00 ERROR 340 customer session tokens written to zone A were unrecognized by zone B nodes, causing sporadic session terminations. 01:30:00 INFO network partition resolved. 01:35:00 INFO database administrators demoted zone A node to replica and executed resync from authoritative zone B master. 01:45:00 INFO all slots rejoined consensus; 12 invalidated sessions were cleanly re-authenticated without data corruption.",
        "reference": "A network partition isolating availability zone A led to an unauthorized local master election and split-brain write divergence in Redis slots 0-5460, intermittently invalidating 340 customer sessions. Upon network recovery, administrators demoted the rogue node and forced a resynchronization from the authoritative master. All hash slots regained consensus, and affected users were cleanly re-authenticated without data corruption."
    },
    {
        "id": "summary-006",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Kafka partition leader imbalance incident.",
        "context": "2026-10-27 07:30:00 INFO cluster maintenance scheduled rolling restart of Kafka broker nodes 1 through 6. 07:45:00 WARN broker-1 failed to release leader partition locks on topic orders-v1 due to a stuck disk write thread. 07:50:00 ERROR broker-2 and broker-3 assumed leadership for 90 percent of all topic partitions, creating a severe CPU and I/O hotspot. 07:55:00 ERROR producer request latency surged to 8,500ms and message delivery timeouts triggered across 14 upstream microservices. 08:12:00 INFO SRE force-killed the hung I/O process on broker-1 and executed kafka-preferred-replica-election.sh across all topic partitions. 08:22:00 INFO partition leadership balanced evenly across the 6 brokers, and producer latency dropped back to 14ms without message loss.",
        "reference": "A rolling restart stalled when broker-1 failed to release partition locks, concentrating 90 percent of topic leadership onto brokers 2 and 3 and causing severe producer timeouts. SREs terminated the stuck process on broker-1 and ran a preferred replica election script to redistribute partitions. Partition leadership normalized across all six brokers, restoring producer latency to 14ms with zero data loss."
    },
    {
        "id": "summary-007",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Elasticsearch unassigned shards incident.",
        "context": "2026-10-27 13:00:00 INFO node es-data-04 terminated unexpectedly after underlying AWS EC2 hardware degradation. 13:02:00 WARN 12 primary shards for index audit-logs-2026 became UNASSIGNED. 13:04:00 ERROR cluster health degraded from GREEN to RED, blocking compliance audit queries and delaying security log indexing. 13:10:00 INFO autoscaler provisioned replacement EC2 instance es-data-04r. 13:15:00 ERROR automated shard allocation failed with error: allocation forbidden by disk watermark limit on peer nodes. 13:25:00 INFO storage engineers increased cluster disk watermark threshold from 85 to 90 percent and triggered cluster.routing.allocation.enable = all. 13:42:00 INFO all 12 primary shards recovered from replica mirrors and cluster health returned to GREEN.",
        "reference": "An EC2 hardware crash took down node es-data-04, leaving 12 primary shards unassigned and turning cluster health RED because disk watermarks blocked re-allocation. Engineers provisioned a replacement node, raised disk watermarks from 85 to 90 percent, and re-enabled shard routing. All shards recovered successfully from mirrors, returning cluster health to GREEN with all logs intact."
    },
    {
        "id": "summary-008",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the PostgreSQL transaction ID wraparound incident.",
        "context": "2026-10-28 02:00:00 INFO PostgreSQL monitoring daemon check_postgres alerted on database customer-db. 02:05:00 WARN database age(datfrozenxid) reached 1,980,000,000, leaving only 20 million transactions before emergency forced shutdown. 02:10:00 ERROR autovacuum workers could not freeze old tuples due to long-running analytical queries locking tables for over 18 hours. 02:15:00 WARN database administrator notified on-call of impending database shutdown risk. 02:22:00 INFO administrator terminated the analytical queries using pg_cancel_backend and invoked VACUUM FREEZE ANALYZE on high-churn tables. 02:45:00 INFO transaction ID age decreased below 200,000,000, averting catastrophic database shutdown without user impact.",
        "reference": "Long-running analytical queries blocked autovacuum from freezing tuples, pushing PostgreSQL transaction ID age within 20 million transactions of an emergency shutdown. The DBA terminated the offending queries and ran an aggressive manual vacuum freeze on high-churn tables. Transaction ID age normalized below 200 million, preventing a catastrophic database outage without data loss."
    },
    {
        "id": "summary-009",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Kubernetes ingress certificate expiration incident.",
        "context": "2026-10-28 09:12:00 INFO ingress-nginx controller processed 32,000 external HTTPS requests/sec. 09:14:00 ERROR browsers presented users with security warning NET::ERR_CERT_DATE_INVALID for domain checkout.store.com. 09:15:30 WARN e-commerce checkout traffic dropped by 92 percent as customer transactions aborted. 09:18:00 INFO security engineers identified that cert-manager webhook pod had crashed 3 days prior, silently preventing automated Let's Encrypt renewal. 09:25:00 INFO engineers restarted cert-manager webhook and manually requested immediate HTTP01 challenge certificate issuance. 09:31:00 INFO valid 90-day TLS certificate was injected into ingress secret and reloaded by ingress-nginx, restoring customer checkout flow.",
        "reference": "An unnoticed cert-manager webhook pod crash prevented automated TLS certificate renewal, causing browsers to reject checkout.store.com with SSL errors and dropping checkout traffic by 92 percent. Engineers restarted the webhook and triggered an immediate HTTP01 challenge renewal. Ingress controllers reloaded the new certificate, resolving all security warnings and restoring normal transactions."
    },
    {
        "id": "summary-010",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Docker registry storage saturation incident.",
        "context": "2026-10-28 16:30:00 INFO automated CI/CD runners initiated 120 container image builds. 16:34:00 ERROR Docker pushes to internal registry harbor.corp.net failed with HTTP 500 Insufficient Storage. 16:36:00 WARN artifact filesystem /var/lib/registry reached 100 percent capacity (2.0TB / 2.0TB) due to disabled untagged image garbage collection. 16:40:00 ERROR production hotfix deployments were blocked across all engineering teams. 16:50:00 INFO platform team executed Harbor garbage collection job with dryRun=false, purging 680GB of orphaned layers. 17:05:00 INFO image push operations resumed successfully and automated weekly registry pruning was scheduled.",
        "reference": "The internal container registry filled its 2.0TB storage volume to 100 percent because image layer garbage collection was disabled, blocking hotfix deployments and container builds across the company. The platform team executed a manual garbage collection that purged 680GB of orphaned layers. Container pushes resumed immediately, and weekly automated pruning was enabled to prevent recurrence."
    },
    {
        "id": "summary-011",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the RabbitMQ memory alarm incident.",
        "context": "2026-10-29 03:00:00 INFO payment-events queue processed 8,000 messages/sec. 03:05:00 WARN RabbitMQ node rabbit@host-1 memory utilization crossed the vm_memory_high_watermark (0.40). 03:06:00 ERROR memory alarm triggered: broker blocked all publishing connections to prevent OOM crash. 03:08:00 ERROR upstream payment services queued requests locally and began failing with 504 Gateway Timeout. 03:15:00 INFO inspection revealed a stalled analytics consumer had left 1.2 million unacknowledged messages in queue. 03:22:00 INFO engineers killed the stalled consumer, allowing RabbitMQ to page messages to disk and release RAM. 03:28:00 INFO memory alarm cleared, publishers unblocked, and pending payments processed normally.",
        "reference": "A stalled consumer left 1.2 million unacknowledged messages in RabbitMQ, triggering the high memory watermark alarm and blocking all incoming publisher connections. Upstream payment services experienced 504 timeouts while publishing was halted. Terminating the stuck consumer allowed messages to page to disk, clearing the memory alarm and unblocking payment processing."
    },
    {
        "id": "summary-012",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the BGP route leak incident.",
        "context": "2026-10-29 11:15:00 INFO transit gateway bgp-router-01 established BGP session with regional ISP provider. 11:17:00 ERROR misconfigured route-map on ISP peer leaked corporate internal IP ranges (10.0.0.0/8) into public Internet routing tables. 11:20:00 WARN asymmetric routing caused 65 percent of ingress packet loss across European customer traffic. 11:23:00 ERROR remote offices lost secure VPN connectivity to central cloud infrastructure. 11:35:00 INFO network operations contacted transit provider NOC and issued BGP community no-export filter. 11:48:00 INFO ISP withdrew the leaked prefix announcements, and global routing convergence restored full network connectivity.",
        "reference": "A misconfigured ISP route-map leaked private 10.0.0.0/8 IP ranges into public BGP routing tables, causing severe asymmetric routing and 65 percent packet loss for European traffic and remote VPNs. Network operations coordinated with the transit provider to apply a no-export filter and withdraw the invalid prefixes. Global routing converged within 30 minutes, restoring full connectivity."
    },
    {
        "id": "summary-013",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the microservice cascading thread exhaustion incident.",
        "context": "2026-10-29 18:00:00 INFO order-service and payment-service operated under normal evening peak load. 18:02:00 WARN third-party fraud verification API latency spiked from 120ms to 9,000ms. 18:04:00 ERROR payment-service exhausted its 250 Tomcat worker threads waiting for fraud API responses. 18:06:00 ERROR order-service threads calling payment-service also backed up, exhausting all 300 threads in order-service. 18:09:00 WARN customer checkout buttons hung indefinitely on web and mobile apps. 18:18:00 INFO team enabled Resilience4j circuit breaker on fraud-service with a 1,000ms timeout and 50 percent failure rate threshold. 18:25:00 INFO circuit breaker opened, isolating the slow fraud API, freeing upstream thread pools, and restoring checkout.",
        "reference": "A latency spike in an external fraud API caused thread exhaustion in payment-service, which cascaded upstream and froze all worker threads in order-service. Customer checkout hung across web and mobile platforms. Enabling a circuit breaker with a 1,000ms timeout isolated the slow external dependency, immediately freeing thread pools and restoring checkout functionality."
    },
    {
        "id": "summary-014",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the AWS IAM role misconfiguration incident.",
        "context": "2026-10-30 04:00:00 INFO Terraform infrastructure-as-code automated pipeline ran scheduled security compliance drift correction. 04:02:00 ERROR automated policy template deleted s3:GetObject permission from EC2 instance profile role-worker-node. 04:05:00 ERROR media-transcoding worker pods failed to download uploaded customer videos, logging AccessDenied. 04:08:00 WARN video processing queue accumulated 4,500 unprocessed user video uploads over 40 minutes. 04:30:00 INFO cloud security engineer identified the deleted IAM statement in CloudTrail event history. 04:35:00 INFO engineer restored the s3:GetObject permission policy via emergency Terraform commit. 04:42:00 INFO worker pods re-assumed credentials and processed the media backlog within 25 minutes.",
        "reference": "An automated Terraform drift correction mistakenly stripped s3:GetObject permissions from the worker node IAM profile, preventing media-transcoding pods from downloading videos and stranding 4,500 uploads. Security engineers traced the deletion via CloudTrail and restored the policy through an emergency commit. Pods re-assumed the corrected role and successfully cleared the processing backlog."
    },
    {
        "id": "summary-015",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Cassandra tombstone saturation incident.",
        "context": "2026-10-30 10:10:00 INFO notification-tracker service updated status of push messages. 10:14:00 WARN query read latency on table push_status rose from 4ms to 650ms. 10:16:00 ERROR Cassandra logged ReadFailureException on node 10.0.4.15: Scanned over 100,001 tombstones, query aborted. 10:20:00 ERROR mobile push delivery confirmation endpoints failed with HTTP 500 for 18 percent of users. 10:32:00 INFO engineers identified that push status records were being soft-deleted immediately after insertion without TTL. 10:40:00 INFO team patched query to use partition key lookups, ran nodetool compact, and set table gc_grace_seconds to 86400. 10:55:00 INFO tombstone count dropped below 500 per slice and read latencies returned to 3ms.",
        "reference": "Immediate soft-deletions without TTL saturated Cassandra table push_status with over 100,000 tombstones per query, triggering read failure exceptions and HTTP 500 errors on push delivery confirmations. Engineers updated queries to use partition key lookups, lowered gc_grace_seconds, and executed manual compactions. Tombstones were cleaned up and query latency dropped back to 3ms."
    },
    {
        "id": "summary-016",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Kubernetes CNI IP exhaustion incident.",
        "context": "2026-10-30 16:00:00 INFO marketing email campaign launched, triggering Kubernetes Horizontal Pod Autoscaler. 16:04:00 WARN HPA requested scaling api-gateway from 30 to 120 pod replicas. 16:06:00 ERROR pods entered Pending status with reason: FailedCreatePodSandBox: no free IP addresses available in pod CIDR 10.244.4.0/24. 16:08:00 WARN incoming traffic exceeded capacity of existing pods, increasing HTTP 502 Bad Gateway responses to 14 percent. 16:15:00 INFO network engineer realized the AWS VPC CNI was assigned an undersized /24 subnet for the secondary node pool. 16:22:00 INFO engineer attached a new secondary IPv4 CIDR 10.244.64.0/18 to the VPC and re-allocated ENI IP prefixes. 16:30:00 INFO 90 pending pods acquired IP addresses, transitioned to Running, and error rates returned to zero.",
        "reference": "A traffic surge triggered pod autoscaling that exhausted available IP addresses in an undersized /24 node CIDR subnet, stranding 90 pods in Pending status and causing 14 percent HTTP 502 errors. Network engineers expanded cluster address space by attaching a /18 CIDR block to the VPC and reconfiguring the CNI. The pending pods immediately acquired IPs and scaled up, eliminating gateway errors."
    },
    {
        "id": "summary-017",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the ClickHouse merge tree disk full incident.",
        "context": "2026-10-31 01:00:00 INFO analytics engine executed hourly data ingestion into ClickHouse table logs_raw. 01:05:00 WARN background part mutation failed on node ch-data-02. 01:08:00 ERROR disk volume /var/lib/clickhouse reached 100 percent utilization (4.0TB / 4.0TB). 01:10:00 ERROR ClickHouse server placed table logs_raw into READ_ONLY mode and rejected incoming streaming events. 01:15:00 WARN real-time telemetry streaming buffer accumulated 80GB in Kafka topics. 01:25:00 INFO database team detached old historical partitions older than 90 days and dropped uncompressed archive tables. 01:38:00 INFO 820GB of disk space was recovered; server resumed write operations and caught up with Kafka backlog.",
        "reference": "Unthrottled hourly ingestion filled ClickHouse storage to 100 percent, halting background part mutations and forcing table logs_raw into read-only mode, which backed up 80GB of telemetry in Kafka. Database administrators detached partitions older than 90 days and dropped unused archive tables, freeing 820GB of disk space. ClickHouse resumed writes and cleared the ingested Kafka queue without data loss."
    },
    {
        "id": "summary-018",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the OAuth token validation service outage incident.",
        "context": "2026-10-31 08:00:00 INFO oauth-authorizer validated user access tokens against identity provider. 08:03:00 WARN public JSON Web Key Set (JWKS) cache expired in oauth-authorizer memory. 08:04:00 ERROR identity provider endpoint https://idp.auth.corp/.well-known/jwks.json returned HTTP 503 during scheduled failover. 08:06:00 ERROR oauth-authorizer could not verify cryptographic token signatures and rejected all 45,000 incoming user requests with HTTP 401 Unauthorized. 08:12:00 INFO SRE enabled stale-while-revalidate caching policy in oauth-authorizer and manually injected cached public keys into Redis. 08:18:00 INFO token validation succeeded using cached cryptographic keys, and user authentication returned to 100 percent success rate.",
        "reference": "When the in-memory JWKS cache expired while the identity provider was undergoing failover, oauth-authorizer could not verify cryptographic signatures and rejected all 45,000 user requests with HTTP 401. SREs mitigated the outage by enabling stale-while-revalidate caching and injecting cached public keys into Redis. Token verification succeeded immediately, and authentication recovered completely."
    },
    {
        "id": "summary-019",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the Memcached connection leak incident.",
        "context": "2026-10-31 14:00:00 INFO session-service deployed v1.9 across 40 container replicas. 14:05:00 WARN memcached server memcached-cluster-01 reported active connections reached 10,000 of 10,240 max limit. 14:08:00 ERROR new memcached connection attempts timed out with Connection reset by peer. 14:10:00 ERROR session retrieval fell back to PostgreSQL primary database, driving database CPU from 12 percent to 98 percent. 14:14:00 WARN website page load latency degraded from 80ms to 4,800ms. 14:25:00 INFO code review revealed v1.9 omitted client.close() in an error handling branch, leaking connections on retries. 14:32:00 INFO team rolled back session-service to v1.8 and restarted Memcached instances. 14:40:00 INFO connections dropped to 350, database CPU fell to 14 percent, and response times normalized.",
        "reference": "A connection leak in session-service v1.9 exhausted Memcached's 10,240 connection limit, forcing session lookups onto PostgreSQL and driving database CPU to 98 percent with 4.8-second page loads. Rolling back to v1.8 and restarting Memcached closed leaked sockets and restored cache hits. Database CPU plummeted back to 14 percent and page latencies returned to normal."
    },
    {
        "id": "summary-020",
        "task": "summarization",
        "system_instruction": "Summarize the incident in two or three sentences using only the supplied context. Preserve the cause, impact, resolution, and any important outcome.",
        "question": "Summarize the AWS Direct Connect fiber cut failover incident.",
        "context": "2026-10-31 22:10:00 INFO physical fiber cut occurred on metropolitan telco backbone carrying AWS Direct Connect 10Gbps link dx-circuit-primary. 22:10:15 ERROR BGP session on dx-circuit-primary dropped with BGP-ERR-PEER-DEATH. 22:11:00 WARN automated failover to standby IPsec VPN tunnel commenced. 22:12:30 WARN IPsec tunnel throughput was capped at 1.25Gbps, causing 8.7Gbps of egress data transfer to queue up on edge routers. 22:15:00 ERROR high-throughput database synchronization between on-premises datacenters and AWS cloud stalled. 22:25:00 INFO network engineering enabled secondary Direct Connect path dx-circuit-secondary via alternate redundant peering location Equinix Ashburn. 22:35:00 INFO 10Gbps Direct Connect capacity restored, buffer queues cleared, and replication resumed.",
        "reference": "A physical fiber cut severed the primary 10Gbps AWS Direct Connect link, forcing traffic onto a 1.25Gbps standby VPN tunnel that became severely saturated and stalled hybrid database synchronization. Network engineers manually activated a secondary redundant Direct Connect circuit in Ashburn. Full 10Gbps bandwidth was restored, clearing edge router queues and resuming database replication."
    }
]

out_path = Path("data/benchmark.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    for c in cases:
        f.write(json.dumps(c) + "\n")


print(f"Successfully wrote {len(cases)} benchmark cases to {out_path}.")
tasks = {}
tokens = []
for c in cases:
    tasks[c["task"]] = tasks.get(c["task"], 0) + 1
    tokens.append(count_tokens(c["context"]))

print("Task breakdown:")
for t, cnt in tasks.items():
    print(f"  {t}: {cnt} cases")

print(f"Context tokens: min={min(tokens)}, max={max(tokens)}, mean={sum(tokens)/len(tokens):.1f}")
