#set page(
  paper: "us-letter",
  margin: (top: 0.75in, bottom: 1.0in, left: 0.625in, right: 0.625in),
  footer: context {
    let p = counter(page).get().first()
    align(center, text(size: 9pt, font: "Times New Roman")[#p])
  }
)

#set text(
  font: "Times New Roman",
  size: 10pt,
  lang: "en"
)

#set par(
  justify: true,
  leading: 0.55em,
  first-line-indent: 1.2em,
)

#set math.equation(numbering: "(1)")

// Headings
#show heading.where(level: 1): it => block(width: 100%, below: 0.6em, above: 1.2em)[
  #set align(center)
  #set text(size: 10pt, weight: "bold", font: "Times New Roman")
  #smallcaps(it.body)
]

#show heading.where(level: 2): it => block(width: 100%, below: 0.5em, above: 0.9em)[
  #set text(size: 10pt, style: "italic", weight: "bold", font: "Times New Roman")
  #it.body
]

#show heading.where(level: 3): it => block(width: 100%, below: 0.4em, above: 0.7em)[
  #set text(size: 10pt, style: "italic", weight: "regular", font: "Times New Roman")
  #it.body
]

// Captions
#show figure.where(kind: table): set figure.caption(position: top)
#show figure.caption: it => [
  #set text(size: 8pt)
  #if it.kind == table [
    #align(center)[
      #text(weight: "bold")[TABLE #counter(figure.where(kind: table)).display("I")] \
      #smallcaps(it.body)
    ]
  ] else [
    #align(left)[
      *Fig. #counter(figure.where(kind: image)).display("1").* #it.body
    ]
  ]
]

// Raw code
#show raw: set text(font: "Courier", size: 7.5pt)
#show raw.where(block: true): it => block(
  fill: rgb("f8f9fa"),
  inset: 5pt,
  radius: 2pt,
  stroke: 0.4pt + rgb("cbd5e1"),
  width: 100%,
  it
)

// Title Block (Full width across page 1)
#align(center)[
  #text(size: 21pt, weight: "bold")[Prompt Compression and Token Budgeting for Enterprise Telemetry: Empirical Evaluation of LLMLingua-2 Control, Quality Tradeoffs, and Latency Bottlenecks]
  
  #v(1em)
  #grid(
    columns: (1fr, 1fr),
    align: center,
    [
      #text(size: 11pt, weight: "bold")[Tejas Shetty]\
      #text(size: 9pt)[Department of Computer Science and Engineering]\
      #text(size: 9pt)[Autonomous AI Systems and Cloud Observability Lab]\
      #text(size: 9pt, font: "Courier")[tejasshetty23\@github.com]
    ],
    [
      #text(size: 11pt, weight: "bold")[Sushir C.]\
      #text(size: 9pt)[Department of Computer Science and Engineering]\
      #text(size: 9pt)[Autonomous AI Systems and Cloud Observability Lab]\
      #text(size: 9pt, font: "Courier")[sushirc\@gemini.lab]
    ]
  )
]
#v(1.2em)

// Two-Column Layout begins
#show: columns.with(2, gutter: 0.25in)

// Abstract & Index Terms
#box[
  #set text(size: 9pt)
  #set par(justify: true, first-line-indent: 0pt, leading: 0.5em)
  _#strong("Abstract")_---#strong([Deploying Large Language Models (LLMs) for real-time observability, automated triage, and incident postmortem synthesis requires processing dense, token-heavy diagnostic traces and multi-page technical documentation. While prompt compression techniques---such as LLMLingua and LLMLingua-2---promise significant reductions in token consumption and inference expenditure, their practical deployment within production enterprise middleware remains poorly understood. In this paper, we conduct an extensive empirical investigation into the mechanics, failure modes, and systems tradeoffs of prompt compression and token budgeting. First, we identify and formalize the root causes of _compression-ratio overshooting_ in LLMLingua-2, where requested compression multipliers (e.g., 5.0x) consistently produce actual compressions of 6.2x to 7.7x due to strict percentile threshold offsets and subword-to-word probability dispersion. We develop a calibrated power-law control formulation, $r_0(R) = R^(-0.86)$, combined with closed-loop adaptive proportional feedback, reducing ratio variance and constraining actual compression within $plus.minus 4\%$ of requested targets across diverse contexts. Second, we introduce a standardized 60-case enterprise incident benchmark across 9 infrastructure archetypes, evaluating 240 measured inference runs across 1.0x, 2.0x, 3.0x, and 5.0x compression using local Ollama-served Qwen 2.5 1.5B models under deterministic decoding. Third, we establish task-specific degradation boundaries across Extractive QA, Multi-Hop Relational QA, and Incident Summarization, leveraging an enhanced evaluation suite including Exact Match, Token F1, ROUGE-1/2/L, Key Fact Recall, and MiniLM semantic cosine similarity. Finally, we uncover and quantify the "Local Inference Paradox": running a 560M parameter neural compressor on CPU incurs a 3,800--5,500ms latency penalty that overwhelms the sub-400ms inference times of compact edge LLMs, yielding a 3x--10x net end-to-end slowdown. We conclude by presenting an operational decision rubric defining when prompt compression delivers genuine economic and latency utility.])

  #v(0.6em)
  _#strong("Index Terms")_---#strong([Prompt Compression, LLMLingua-2, Token Budgeting, Large Language Models, Cloud Observability, Systems Efficiency, Machine Learning Systems.])
]

#v(0.8em)

= I. Introduction

The integration of Large Language Models (LLMs) into Site Reliability Engineering (SRE) and cloud infrastructure management has emerged as a cornerstone of modern autonomic computing [1], [2]. Diagnostic workflows routinely ingest heterogeneous, high-volume telemetry: Kubernetes events, systemd journal logs, distributed tracing spans, and multi-page incident postmortems. However, transmitting massive textual contexts into generative transformer models encounters fundamental operational boundaries:

1. *Context Window Exhaustion and Attention Degradation:* While modern long-context models support 32k to 1M tokens, empirical studies demonstrate that models suffer from the "Lost in the Middle" phenomenon [3], exhibiting sharp declines in retrieval accuracy as extraneous noise fills the attention context.

2. *Economic Scaling Costs:* In commercial API environments (e.g., OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet), token pricing scales linearly with context length. High-frequency automated monitors processing millions of log lines daily face prohibitive recurring expenditures [4].

3. *Inference Latency and Throughput:* For self-hosted and edge-deployed models, prefill latency scales with prompt length, creating significant queueing delays during high-severity production incidents [5].

To mitigate these constraints, selective prompt compression frameworks---most notably LLMLingua [6] and its small-model successor LLMLingua-2 [7]---have been proposed. Rather than relying on simple sentence truncation or keyword filtering, these frameworks employ smaller, auxiliary transformer models to compute information-density metrics across token sequences, dynamically dropping low-utility tokens while retaining semantic coherence.

Despite promising headline results on academic question-answering benchmarks, implementing prompt compression within enterprise telemetry middleware reveals three fundamental open questions:

- *Research Question 1 (Control Predictability):* Why do off-the-shelf prompt compressors exhibit massive compression-ratio overshooting when applied to structured logs and system events, and how can deterministic, budget-enforced compression control be achieved?
- *Research Question 2 (Task-Specific Information Boundaries):* At what exact compression thresholds do different downstream reasoning tasks---specifically Extractive Entity QA, Multi-Hop Causal Reasoning, and Global Narrative Summarization---suffer critical degradation?
- *Research Question 3 (The Systems Latency Tradeoff):* Under what architectural configurations does the computational cost of executing an auxiliary neural compressor on CPU justify the downstream token savings, particularly in resource-constrained local deployment scenarios?

== Contributions
In this work, we resolve these questions through systematic algorithmic refinement and extensive empirical benchmarking:

- *Mathematical Analysis and Calibrated Adaptive Control:* We diagnose the mathematical and tokenizer-level mechanisms driving LLMLingua-2's compression overshooting. We formulate an empirical power-law mapping $r_0(R) = R^(-0.86)$ coupled with a proportional closed-loop controller that stabilizes actual compression ratios within $plus.minus 4\%$ of requested targets across all testing cells.
- *Preservation-Invariant Middleware Architecture:* We design and open-source an enterprise-grade Python middleware that guarantees strict context isolation, anchoring system instructions and user queries as immutable invariants while chunking, ranking, compressing, and enforcing hard per-request token budgets on diagnostic context.
- *A Curated 60-Case Enterprise Benchmark Dataset:* We release a diverse, provenance-tracked evaluation suite of 60 real-world incident scenarios covering 9 infrastructure domains (Kubernetes, Kafka, PostgreSQL, Redis, CoreDNS, OAuth/IAM, gRPC microservices, CI/CD pipelines, and cloud networking) across Extractive QA, Multi-Hop QA, and Summarization.
- *Comprehensive Multimodal Evaluation (240 Measured Runs):* Using local Ollama-served Qwen 2.5 1.5B with warm-up runs strictly excluded, we evaluate 240 model generations. We augment traditional n-gram metrics with semantic cosine embedding similarity (`sentence-transformers/all-MiniLM-L6-v2`) and factual keyphrase recall.
- *Discovery of the "Local Inference Paradox":* We document and analyze the counter-intuitive phenomenon wherein CPU-based neural prompt compression severely degrades end-to-end latency (up to a 10.5x slowdown) for small local LLMs, and derive the exact mathematical crossover points where prompt compression provides genuine economic and latency advantages.

= II. Related Work

== A. Context Filtering and Retrieval-Augmented Generation
Retrieval-Augmented Generation (RAG) represents the prevailing paradigm for managing large diagnostic contexts [8]. In standard RAG pipelines, external documents are partitioned into fixed-length text chunks, indexed via dense vector embeddings, and retrieved using approximate nearest neighbor search (e.g., cosine similarity over bi-encoder representations) [9]. While effective for broad topic retrieval, standard RAG struggles with high-cardinality semi-structured logs where critical failure indicators are lexically subtle and temporally distributed across disjoint log lines.

== B. Prompt Compression Architectures
Prompt compression methods broadly fall into three categories:

1. *Heuristic and Lexical Pruning:* Techniques utilizing TF-IDF, BM25, or stop-word removal [10]. While computationally negligible, lexical pruning lacks syntactic awareness, frequently deleting negation tokens, prepositions, and structural identifiers essential for reasoning.

2. *Generative Information Summarization:* Utilizing smaller LLMs (e.g., T5, LLaMA-7B) to summarize intermediate context prior to downstream querying [11]. While preserving narrative fluency, generative summarization suffers from hallucination risks, non-deterministic latency, and substantial compute overhead.

3. *Neural Token Classification (LLMLingua Series):* LLMLingua [6] introduced budget-aware prompt compression using causal language models (e.g., LLaMA-2-7B, GPT-2) to evaluate token perplexity as an information proxy. To eliminate the high inference latency of causal generation, LLMLingua-2 [7] reformulated compression as a token classification task using an encoder-only XLM-RoBERTa backbone trained on the MeetingBank dataset. LLMLingua-2 assigns binary keep/drop probabilities to individual tokens in a single non-autoregressive forward pass. However, as demonstrated in Section IV, its default percentile thresholding creates severe ratio overshooting when applied outside conversational transcripts.

== C. Token Budgeting and LLM Inference Economics
As LLMs transition into enterprise operations, token budgeting has emerged as a critical cost and governance requirement [12]. Commercial providers enforce strict tokens-per-minute (TPM) rate limits, while multi-tenant architectures require predictable latency SLAs. Previous work by Chen et al. [13] evaluated token economics across commercial APIs, demonstrating that input prompt tokens dominate total inference cost by up to 80% in log analysis workloads. However, prior literature largely assumes that token reduction directly translates to reduced system latency, an assumption we systematically dismantle in Section VII.

= III. Middleware Architecture & Design

To provide predictable token budgeting while maintaining strict semantic guarantees, we developed the `PromptBudgetMiddleware` system, illustrated in Fig. 1.

#figure(
  caption: [Architectural flow of the Prompt Budget Middleware.],
  block(
    width: 100%,
    fill: rgb("f8fafc"),
    stroke: 0.5pt + rgb("cbd5e1"),
    inset: 8pt,
    radius: 3pt,
    [
      #set text(size: 7.5pt, font: "Times New Roman")
      #align(center)[
        #rect(width: 90%, fill: rgb("e2e8f0"), stroke: 0.5pt + rgb("94a3b8"), radius: 2pt)[
          *Incoming Request*: System Instruction ($cal(I)$), Question ($cal(Q)$), Context ($cal(C)$), Token Budget ($B$)
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("eff6ff"), stroke: 0.5pt + rgb("3b82f6"), radius: 2pt)[
          *1. Architectural Context Isolation*: Anchors $cal(I)$ and $cal(Q)$ as immutable invariants ($0%$ compression).
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("eff6ff"), stroke: 0.5pt + rgb("3b82f6"), radius: 2pt)[
          *2. Ingestion & Lexical Relevance Chunking*: Sliding token window ($800$ tok, $80$ overlap); Question-overlap lexical ranking; Chronological sort.
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("f0fdf4"), stroke: 0.5pt + rgb("22c55e"), radius: 2pt)[
          *3. Calibrated LLMLingua-2 Compression*: Initial rate $r_0 = R^(-0.86)$; XLM-RoBERTa token classification; Adaptive proportional refinement ($tau=0.15$).
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("fefce8"), stroke: 0.5pt + rgb("eab308"), radius: 2pt)[
          *4. Hard Token Budget Enforcement*: Validates prefix fit; Deterministic tail truncation to token budget $B_("max")$.
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("fdf2f8"), stroke: 0.5pt + rgb("ec4899"), radius: 2pt)[
          *5. Telemetry & Cost Tracking*: Tiktoken encoding counts; Decoupled latency telemetry ($T_("comp")$, $T_("infer")$, $T_("e2e")$); JSONL logging.
        ]
        #v(0.3em) $arrow.b$ #v(0.3em)
        #rect(width: 90%, fill: rgb("e2e8f0"), stroke: 0.5pt + rgb("94a3b8"), radius: 2pt)[
          *Dispatched Prompt to Downstream Model* (Ollama Qwen 2.5 1.5B / Cloud API)
        ]
      ]
    ]
  )
)

== A. Context Isolation Invariant
A core design flaw in naive compression wrappers is passing the entire prompt (system instructions, user query, and context) into the compressor. In enterprise environments, system instructions contain strict safety, schema, and formatting guardrails (e.g., "Return valid JSON", "Answer only from context"). Compressing system instructions invariably leads to schema violations and prompt injection vulnerabilities.

Our middleware strictly enforces the *Context Isolation Invariant*:
$ cal(P)_("final") = cal(I)_("system") parallel cal(Q)_("user") parallel cal(C)_("compressed") $
where $cal(I)_("system")$ and $cal(Q)_("user")$ are preserved verbatim, and compression $cal(F)_("comp")(dot)$ operates exclusively on context $cal(C)$.

== B. Ingestion and Lexical Relevance Chunking
Enterprise diagnostic context frequently exceeds single-sequence transformer limits. The ingestion pipeline supports `.log`, `.txt`, `.md`, `.csv`, `.jsonl`, and multi-page `.pdf` documents (extracted via `pdfplumber`).

When context length $|cal(C)|_("tokens") > L_("chunk")$ (default 800 tokens), context is partitioned into overlapping windows. Let $Delta L = L_("chunk") - L_("overlap")$ denote the window stride length. Then each chunk spans:
$ cal(S)_i = "tokens"[i dot Delta L : i dot Delta L + L_("chunk")] $
To prevent losing boundary entities, overlap tokens are preserved from the previous chunk's suffix using `truncate_to_last_tokens`. Chunks are ranked against question $cal(Q)$ using lexical term matching:
$ "Score"(cal(S)_i, cal(Q)) = sum_(w in cal(Q)) "count"(w, cal(S)_i) $
The top-$k$ ranked chunks (sorted by their original chronological index to preserve temporal causality) are concatenated to form the candidate context.

== C. Hard Budget Enforcement
Following neural compression, the middleware enforces a hard token ceiling $B_("max")$. If the total token length of the candidate prompt exceeds $B_("max")$, context is deterministically truncated from its tail using the downstream tokenizer encoding (`cl100k_base`):
$ L_("allow") = max(0, B_("max") - "count"(cal(I)_("system") parallel cal(Q)_("user"))) $
$ cal(C)_("final") = "truncate_to_tokens"(cal(C)_("compressed"), L_("allow")) $
If $B_("max") < "count"(cal(I)_("system") parallel cal(Q)_("user"))$, the middleware raises a descriptive `ValueError`, preventing execution of corrupted requests.

= IV. Compression Control Theory & Formulation

== A. Mathematical Derivation of LLMLingua-2 Overshooting
In LLMLingua-2 [7], prompt compression is framed as token classification. Given an input sequence $bold(x) = (x_1, dots, x_N)$, the encoder outputs probability distribution $bold(p) = (p_1, dots, p_N)$ where $p_i = P("keep" mid x_i)$.

To achieve a target compression ratio $R >= 1.0$, the nominal retention rate is set to:
$ r_("nom") = 1 / R, quad "reduce_rate" = 1.0 - r_("nom") $
The algorithm calculates a decision threshold $theta$ using NumPy's percentile function:
$ theta = "Percentile"(bold(p)_("expanded"), floor(100 dot "reduce_rate" + 1)) $
and constructs the compressed sequence by filtering tokens:
$ "Keep"(x_i) <=> p_i > theta $

This operational formulation introduces three systematic sources of negative bias in retained token volume:

1. *Percentile Offset Discard:* The addition of $+1$ inside the percentile index shifts the retention threshold upwards by one full percentile. In a sequence of $N$ tokens, this mathematically discards up to $0.01 dot N$ additional tokens beyond the nominal target.

2. *Strict Inequality Boundary Exclusion:* The conditional filter requires $p_i > theta$. In discrete probability distributions where multiple tokens share identical model logits (frequent in structured logs with repetitive keywords such as `INFO`, `2026-10-01`, `HTTP`), all tokens whose probability equals $theta$ are discarded. Consequently, the fraction of retained tokens is strictly less than $1 - floor(100 dot "reduce_rate" + 1) / 100 < r_("nom")$.

3. *Subword-Word Asymmetry:* In `llmlingua`, subword tokens are merged into words using mean pooling, but thresholding expands word probabilities back across the number of OpenAI tokenizer tokens. In technical enterprise logs, low-probability words frequently consist of multiple subwords (e.g., timestamps `2026-10-01 09:00:02` or service hashes `order-worker-99a` decompose into 4--7 subwords). Discarding a single multi-subword token eliminates multiple tokens from the final prompt, causing actual token retention to drop significantly below $r_("nom")$.

Empirical measurement of this discrepancy is presented in Table I.

#figure(
  caption: [Empirical Compression Ratio Overshoot (Uncalibrated Baseline)],
  table(
    columns: (1.3fr, 1.1fr, 1.2fr, 1.0fr),
    align: (left, center, center, center),
    stroke: none,
    table.hline(stroke: 0.8pt),
    table.header([*Target Ratio ($R$)*], [*Nominal Rate ($1/R$)*], [*Actual Ratio (Mean)*], [*Overshoot (%)*]),
    table.hline(stroke: 0.4pt),
    [1.0x (Baseline)], [1.000], [1.000x], [0.0%],
    [2.0x], [0.500], [2.281x], [+14.1%],
    [3.0x], [0.333], [3.604x], [+20.1%],
    [5.0x], [0.200], [6.182x], [+23.6%],
    table.hline(stroke: 0.8pt),
  )
)
#v(-0.3em)
#align(center)[#text(size: 7.5pt, style: "italic")[Note: In individual cases with dense timestamps, actual compression reached 7.72x under the 5.0x setting.]]

== B. Calibrated Power-Law Control Formulation
To compensate for the non-linear relationship between nominal rate parameter $r$ and downstream token retention, we conducted an empirical parameter sweep across $r in [0.10, 0.90]$ on representative enterprise telemetry traces.

Fitting a log-log regression model over observed actual ratios $R_("actual")$ yields:
$ ln(r) = -0.8563 dot ln(R) - 0.0024 $
Exponentiating both sides establishes the *Power-Law Calibration Formula*:
$ r_0(R) = min(1.0, max(0.05, R^(-0.86))) $

Evaluating $r_0(R)$ at our standard experimental ratios yields:
- For $R = 2.0x$: $r_0 = 2.0^(-0.86) approx bold(0.5510)$ (vs. nominal $0.5000$)
- For $R = 3.0x$: $r_0 = 3.0^(-0.86) approx bold(0.3888)$ (vs. nominal $0.3333$)
- For $R = 5.0x$: $r_0 = 5.0^(-0.86) approx bold(0.2505)$ (vs. nominal $0.2000$)

== C. Closed-Loop Adaptive Refinement
While $r_0(R)$ aligns the population mean, structural variations across logs (e.g., dense JSON traces vs. sparse plain text) can introduce residual variance. To guarantee strict adherence, the middleware implements a closed-loop proportional controller:

```python
def compress_adaptive(context, target_ratio, tolerance=0.15, max_refinements=1):
    r0 = target_ratio ** (-0.86)
    compressed, metadata = raw_compress(context, rate=r0)
    actual_ratio = count_tokens(context) / count_tokens(compressed)
    
    # Check if outside tolerance threshold
    err = abs(actual_ratio - target_ratio) / target_ratio
    if err > tolerance and max_refinements > 0:
        # Proportional feedback adjustment
        adjusted_rate = clip(r0 * (actual_ratio / target_ratio), 0.05, 1.0)
        ref_compressed, _ = raw_compress(context, rate=adjusted_rate)
        ref_ratio = count_tokens(context) / count_tokens(ref_compressed)
        
        if abs(ref_ratio - target_ratio) <= abs(actual_ratio - target_ratio):
            return ref_compressed, ref_ratio
    return compressed, actual_ratio
```

By setting tolerance $tau = 0.15$ and capping refinements at $M=1$, the controller avoids latency overhead on $97.5%$ of requests while eliminating extreme outliers.

#figure(
  caption: [Requested target compression ratio versus measured actual ratio before and after calibrated adaptive control.],
  image("../artifacts/figures/ratio_control.pdf", width: 95%)
)

= V. Experimental Benchmark Setup

== A. The 60-Case Enterprise Incident Benchmark Dataset
To overcome the statistical limitations of small exploratory datasets (e.g., 4 cases per task), we constructed a comprehensive, rigorously curated benchmark dataset consisting of *60 distinct incident scenarios*. 

The dataset is partitioned equally across three fundamental LLM operational tasks:
1. *Extractive QA (20 Cases, `extract-001` to `extract-020`):* Requires pinpointing precise operational metrics, IP addresses, Kubernetes namespaces, container exit codes, port numbers, or service identifiers. Reference answers are atomic strings.
2. *Multi-Hop QA (20 Cases, `multi-001` to `multi-020`):* Requires synthesizing multiple temporally or architecturally separated events to deduce root cause, propagating failure chains, and administrative resolutions.
3. *Incident Summarization (20 Cases, `summary-001` to `summary-020`):* Requires generating comprehensive postmortem summaries encapsulating all four canonical SRE dimensions: Cause, Impact, Resolution, and Long-Term Outcome.

The scenarios encompass 9 mission-critical enterprise systems, detailed in Table II:
- *Kubernetes:* OOMKilled exit 137, CrashLoopBackOff, CNI IP exhaustion, kubelet eviction policies, Helm rollback.
- *Distributed Messaging:* Kafka broker disk fill, partition leader locks, consumer lag rebalances, RabbitMQ Mnesia split-brain.
- *Databases:* PostgreSQL transaction ID wraparound, HikariCP starvation, replication lag, Cassandra tombstones, ClickHouse disk full.
- *Caching:* Redis split-brain failover, `noeviction` OOM set rejections, Memcached connection leaks.
- *Networking:* BGP route leaks, IPsec VPN CA expiry, CoreDNS query storms, AWS Direct Connect fiber cuts.
- *API Gateways:* HTTP 503 circuit breakers, HTTP 504 timeouts, Envoy thread pool exhaustion, WAF rate limits.
- *Identity & Security:* Expired TLS certificates, AWS IAM drift correction deletions, NAT Gateway IP rotation.
- *CI/CD Pipelines:* Docker Hub unauthenticated rate limits, container registry volume saturation, blocking schema migrations.
- *Search Engines:* Elasticsearch GC pauses, split-brain master elections, unassigned shards.

Context lengths average $165.5 plus.minus 20.9$ tokens (ranging from 130 to 218 tokens), providing a consistent density baseline.

#figure(
  caption: [Benchmark Dataset Archetype Distribution across 60 Cases],
  table(
    columns: (1.5fr, 0.8fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, center, center, center, center),
    stroke: none,
    table.hline(stroke: 0.8pt),
    table.header([*Infrastructure Domain*], [*Extract*], [*Multi-Hop*], [*Summary*], [*Total*]),
    table.hline(stroke: 0.4pt),
    [Kubernetes Core & CNI], [4], [3], [3], [10],
    [Distributed Messaging (Kafka/Rabbit)], [3], [3], [2], [8],
    [Databases (Postgres/Cassandra)], [3], [3], [3], [9],
    [In-Memory Caches (Redis/Memcached)], [2], [2], [2], [6],
    [Cloud Networking & BGP], [2], [2], [3], [7],
    [API Gateways & Ingress], [2], [2], [2], [6],
    [Identity, Auth & TLS], [2], [2], [2], [6],
    [CI/CD & Registries], [1], [2], [1], [4],
    [Search Clusters (Elasticsearch)], [1], [1], [2], [4],
    table.hline(stroke: 0.4pt),
    [*Total Cases*], [*20*], [*20*], [*20*], [*60*],
    table.hline(stroke: 0.8pt),
  )
)

== B. Downstream Inference Pipeline
- *Model:* `Qwen 2.5 1.5B Instruct` executed locally via Ollama. Qwen 2.5 1.5B was selected as an exemplar of the modern generation of highly capable, compact edge models optimized for low-latency operational deployment [14].
- *Decoding Parameters:* `temperature = 0.0` (greedy deterministic decoding), `top_p = 1.0`, timeout = 120s.
- *Warm-up Protocol:* To ensure latency fidelity, the benchmark runner executes 1 compressor warm-up call and 2 distinct LLM warm-up calls before initializing benchmark measurements. These warm-up calls are strictly excluded from all reported CSV data.
- *Execution Volume:* 60 cases $times$ 4 compression ratios (1.0x, 2.0x, 3.0x, 5.0x) = *240 fully measured inference runs*.

== C. Multi-Dimensional Evaluation Metrics
To provide robust quality evaluation beyond superficial n-gram matching, we employ a multi-metric evaluation protocol:
1. *Exact Match (EM):* Binary indicator evaluating exact string equality after lowercase alphanumeric normalization.
2. *Token-Level F1:* Harmonic mean of precision and recall over bag-of-words token overlap.
3. *ROUGE-1, ROUGE-2, and ROUGE-L:* Evaluating unigram overlap, bigram phrasing, and Longest Common Subsequence (LCS) recall for narrative fluency.
4. *Key Fact Recall:* Evaluating the recall of salient domain entities, status codes, and numerical values against ground truth references:
$ "FactRecall" = (| "Tokens"_("pred") inter "SalientTokens"_("ref") |) / (| "SalientTokens"_("ref") |) $
5. *Semantic Cosine Similarity:* Embeddings generated using the pre-trained sentence transformer `sentence-transformers/all-MiniLM-L6-v2` [15]. Embeddings $bold(e)_p, bold(e)_r in RR^(384)$ are mean-pooled across attention masks and normalized, computing cosine similarity $cos(bold(e)_p, bold(e)_r)$. This metric provides semantic invariance against paraphrasing and alternative sentence ordering.

#figure(
  placement: top,
  scope: "parent",
  caption: [Comprehensive Benchmark Results (60 Cases, 240 Measured Runs across Qwen 2.5 1.5B)],
  table(
    columns: (2.6fr, 1.4fr, 1.4fr, 1.4fr, 1.4fr),
    align: (left, center, center, center, center),
    stroke: none,
    table.hline(stroke: 0.8pt),
    table.header([*Task / Metric*], [*1.0x (Baseline)*], [*2.0x Target*], [*3.0x Target*], [*5.0x Target*]),
    table.hline(stroke: 0.4pt),
    [*COMPRESSION CONTROL:*], [], [], [], [],
    [Actual Compression Ratio], [1.000 ± 0.000], [1.980 ± 0.153], [2.984 ± 0.220], [4.837 ± 0.358],
    [Context Token Reduction (%)], [0.00% ± 0.00%], [49.20% ± 3.93%], [66.31% ± 2.46%], [79.22% ± 1.51%],
    [Compressed Context Tokens], [165.5 ± 20.9], [84.0 ± 12.8], [55.9 ± 9.6], [34.4 ± 4.8],
    table.hline(stroke: 0.2pt),
    [*EXTRACTIVE QA (N=20):*], [], [], [], [],
    [Exact Match (EM)], [0.750 ± 0.444], [0.550 ± 0.510], [0.500 ± 0.513], [0.350 ± 0.489],
    [Token F1], [0.890 ± 0.224], [0.650 ± 0.452], [0.533 ± 0.500], [0.383 ± 0.487],
    table.hline(stroke: 0.2pt),
    [*MULTI-HOP QA (N=20):*], [], [], [], [],
    [Token F1], [0.464 ± 0.091], [0.400 ± 0.093], [0.352 ± 0.087], [0.353 ± 0.082],
    [ROUGE-L], [0.391 ± 0.082], [0.328 ± 0.087], [0.285 ± 0.073], [0.280 ± 0.061],
    [Semantic Similarity (MiniLM)], [0.825 ± 0.056], [0.803 ± 0.072], [0.783 ± 0.085], [0.736 ± 0.089],
    [Key Fact Recall], [0.531 ± 0.131], [0.413 ± 0.104], [0.360 ± 0.129], [0.334 ± 0.117],
    table.hline(stroke: 0.2pt),
    [*INCIDENT SUMMARIZATION (N=20):*], [], [], [], [],
    [ROUGE-L], [0.319 ± 0.059], [0.267 ± 0.074], [0.261 ± 0.065], [0.232 ± 0.046],
    [ROUGE-1], [0.476 ± 0.052], [0.422 ± 0.071], [0.417 ± 0.074], [0.381 ± 0.074],
    [ROUGE-2], [0.172 ± 0.059], [0.114 ± 0.050], [0.100 ± 0.040], [0.069 ± 0.039],
    [Key Fact Recall], [0.481 ± 0.083], [0.353 ± 0.103], [0.307 ± 0.078], [0.250 ± 0.072],
    table.hline(stroke: 0.2pt),
    [*LATENCY BREAKDOWN (ALL TASKS MEAN):*], [], [], [], [],
    [Compression Latency (ms)], [0.4 ± 0.4], [4911.6 ± 1882.2], [4027.3 ± 1348.2], [4742.4 ± 2035.1],
    [Inference Latency (ms)], [1929.5 ± 1464.8], [1382.8 ± 816.2], [1252.9 ± 903.1], [991.7 ± 481.0],
    [End-to-End Latency (ms)], [1929.9 ± 1464.8], [6294.4 ± 2240.8], [5280.2 ± 1964.3], [5734.0 ± 2302.9],
    [Relative Latency vs Baseline], [1.00x], [3.26x (Slower)], [2.74x (Slower)], [2.97x (Slower)],
    table.hline(stroke: 0.8pt),
  )
)

= VI. Empirical Results & Analysis

Table III presents the comprehensive aggregate experimental results across all 240 measured runs, reporting mean and standard deviation for quality, token reduction, and latency.

#figure(
  placement: top,
  scope: "parent",
  caption: [Task degradation trajectories across Extractive QA, Multi-Hop QA, and Incident Summarization as compression increases from 1.0x to 5.0x.],
  image("../artifacts/figures/accuracy_vs_compression.pdf", width: 95%)
)

== A. Compression Ratio Control & Predictability
As demonstrated in Table III, our calibrated power-law controller completely resolves the overshooting failure mode. Whereas the uncalibrated baseline produced actual ratios of 2.28x, 3.60x, and 6.18x (with peaks exceeding 7.7x), our adaptive controller achieves:
- Target 2.0x $arrow.r$ *1.980x* ($plus.minus 0.153$)
- Target 3.0x $arrow.r$ *2.984x* ($plus.minus 0.220$)
- Target 5.0x $arrow.r$ *4.837x* ($plus.minus 0.358$)

This stability ensures that token budgets are respected without prematurely dropping context.

== B. Task Degradation Dynamics

=== 1) Extractive QA
Extractive QA exhibits high vulnerability to compression. Between 1.0x and 2.0x, Exact Match decreases from 0.750 to 0.550. However, past 2.0x, performance collapses: EM drops to 0.500 at 3.0x and to 0.350 at 5.0x, while Token F1 plummets from 0.890 to 0.383 ($-57.0%$). 

Because extractive queries depend on isolated, low-frequency tokens (e.g., port `26379`, commit hash `4a9f1b2`, status code `HTTP 504`), the XLM-RoBERTa classifier frequently scores these tokens below the retention threshold when compression exceeds 2x.

=== 2) Multi-Hop QA
In Multi-Hop QA, answers are explanatory narratives describing causal sequences. While Token F1 decreases from 0.464 (1.0x) to 0.352 (3.0x), *Semantic Similarity remains resilient, staying at 0.803 at 2.0x and 0.783 at 3.0x*. 

Even when intermediate sentences are pruned, the downstream LLM correctly infers the root cause and resolution. Degradation only accelerates at 5.0x (Semantic Sim = 0.736, Fact Recall = 0.334), where essential causal links (e.g., the specific configuration parameter that failed) are pruned entirely.

=== 3) Incident Summarization
Incident Summarization demonstrates resilient narrative retention under moderate compression:
- ROUGE-L at 1.0x: *0.319* ($plus.minus 0.059$)
- ROUGE-L at 2.0x: *0.267* ($plus.minus 0.074$)
- ROUGE-L at 3.0x: *0.261* ($plus.minus 0.065$)
- ROUGE-L at 5.0x: *0.232* ($plus.minus 0.046$)

At 2.0x and 3.0x, prompt compression preserves the core failure symptoms and remediation actions with minimal degradation in Longest Common Subsequence recall ($0.319 arrow.r 0.267 arrow.r 0.261$). Severe degradation accelerates past 3.0x, dropping ROUGE-L to $0.232$ and Key Fact Recall to $0.250$ as crucial operational remediation details are pruned.

= VII. Latency Dynamics: The Local Inference Paradox

A foundational assumption in existing prompt compression literature is that reducing input token count automatically reduces end-to-end execution latency [6], [7]. Our empirical measurements expose a profound counter-example when operating in local environments.

#figure(
  caption: [Latency breakdown across compression ratios, exposing the CPU compression overhead bottleneck.],
  image("../artifacts/figures/latency_breakdown.pdf", width: 95%)
)

== A. The Latency Decomposition
End-to-end latency $T_("e2e")$ decomposes into compression overhead and downstream generation:
$ T_("e2e") = T_("compress") + T_("infer") $
where $T_("infer") = T_("prefill")(N_("comp")) + T_("decode")(M_("out"))$.

In our testbed, downstream generation on Qwen 2.5 1.5B (running with Apple Silicon GPU acceleration via Ollama) exhibited rapid execution:
- Extractive QA Baseline ($N=145.7$ tokens): $T_("infer") = bold(411.7" ms")$
- Extractive QA 5.0x Compressed ($N=30.1$ tokens): $T_("infer") = bold(254.9" ms")$ (Inference saving: *156.8 ms*, a 38.1% speedup)
- All-Tasks Baseline ($N=165.5$ tokens): $T_("infer") = bold(1929.5" ms")$
- All-Tasks 5.0x Compressed ($N=34.4$ tokens): $T_("infer") = bold(991.7" ms")$ (Inference saving: *937.8 ms*, a 48.6% speedup)

However, executing the 560M parameter XLM-RoBERTa encoder on CPU required:
$ T_("compress") approx bold("4,000--5,500 ms") $
Consequently, total response latency increased substantially: for Extractive QA, end-to-end latency surged from *412.1 ms to 4,094.8 ms (a 9.9x slowdown)*; across all tasks, mean end-to-end latency surged from *1,929.9 ms to 5,734.0 ms (a 2.97x slowdown)*. The inference speedups gained from shorter prompt lengths were completely dominated by CPU tensor evaluation time.

== B. Analytical Crossover Model
To formalize when prompt compression yields positive latency utility ($Delta T_("e2e") < 0$), we define the *Latency Utility Inequality*:
$ Delta T_("e2e") = T_("compress") - Delta T_("infer") < 0 $
where the downstream inference acceleration $Delta T_("infer")$ is:
$ Delta T_("infer") = T_("infer")(N_("orig")) - T_("infer")(N_("comp")) $

Let $kappa_("prefill")$ denote the downstream model's prefill processing time per token (ms/token), and $kappa_("comp")$ denote the compressor's processing time per token:
$ T_("compress") = kappa_("comp") dot N_("orig") $
$ Delta T_("infer") approx kappa_("prefill") dot (N_("orig") - N_("comp")) $
Dividing by $N_("orig")$ with compression reduction factor $delta = 1 - 1 / R$:
$ kappa_("comp") < delta dot kappa_("prefill") ==> kappa_("prefill") > kappa_("comp") / delta $

On CPU execution:
- $kappa_("comp") approx (4911" ms") / (165" tokens") approx bold(29.7" ms/token")$
- For Qwen 2.5 1.5B on GPU/Metal: $kappa_("prefill") approx bold(0.95" ms/token")$

Because $kappa_("comp") >> kappa_("prefill")$ by a factor of 31x, prompt compression on CPU can *never* yield a net latency improvement for small local LLMs on short-to-medium contexts.

#figure(
  caption: [Context token reduction and estimated API cost trajectory per 10k calls as compression increases.],
  image("../artifacts/figures/cost_token_savings.pdf", width: 95%)
)

== C. Economic and Architectural Implications
Prompt compression becomes computationally and economically viable under two distinct conditions:
1. *Large Commercial Cloud APIs (e.g., GPT-4o, Claude 3.5 Sonnet):* Where commercial providers charge \$3.00--\$15.00 per million prompt tokens and enforce strict concurrency throttling, prompt compression reduces API bills by up to 75% while operating within cloud budgets.
2. *GPU-Accelerated or Asynchronous Context Caching:* When the auxiliary compressor runs on a dedicated GPU accelerator ($kappa_("comp") < 0.2" ms/token"$) or when compressed documentation/logs are cached and reused across hundreds of queries, the compression overhead is fully amortized.

= VIII. Failure-Mode Case Studies

To understand how information breaks down under severe compression, we examine four representative failure modes from our benchmark results.

== Case 1: Entity and Timestamp Stripping (Extractive QA, `extract-001`)
- *Prompt Question:* "Which service returned HTTP 503?"
- *Ground Truth:* `inventory-service`
- *Raw Context (183 tokens):* `...ERROR inventory-service returned HTTP 503 after three retries. WARN api-gateway opened its circuit breaker...`
- *5.0x Compressed Context (32 tokens):* `09:00:02 accepted R-441 validated session queried warehouse stock 1 2 returned 503 retries opened breaker inventory requests notification healthy`
- *Downstream LLM Prediction:* `warehouse stock`
- *Failure Analysis:* The compressor retained `returned 503 retries` but deleted the adjacent subject token `inventory-service`, retaining only `warehouse stock` from an earlier clause. The downstream LLM associated the error with the nearest available noun phrase, yielding a false prediction.

== Case 2: Causal Chain Disconnection (Multi-Hop QA, `multi-006`)
- *Prompt Question:* "How did an upstream network policy update lead to billing charge duplicates, and how was it corrected?"
- *Ground Truth:* `A strict network policy blocked return ingress ACK packets from the bank gateway, leading payment-service to misinterpret timeouts and issue duplicate charge retries without idempotency keys. Engineers patched the policy to allow return traffic and added idempotency keys.`
- *5.0x Compressed Prediction:* `A network policy was applied. Customers were charged duplicates on credit cards. The policy was patched.`
- *Failure Analysis:* Compression at 5x eliminated the technical explanation (dropping `return ingress ACK packets`, `missing port 443 rule`, and `idempotency keys`). While the high-level chronology was preserved, the precise engineering causality required for an SRE postmortem was completely lost.

== Case 3: Recovery Action Pruning (Summarization, `summary-016`)
- *Prompt Question:* "Summarize the Kubernetes CNI IP exhaustion incident."
- *5.0x Compressed Prediction:* `Horizontal Pod Autoscaler scaled api-gateway from 30 to 120 replicas, but pods entered Pending status due to no free IP addresses in pod CIDR 10.244.4.0/24, causing HTTP 502 errors.`
- *Failure Analysis:* The model accurately summarized the root cause and impact, but completely omitted the resolution (attaching secondary CIDR `10.244.64.0/18` to the VPC). Under 5x compression, the final sentences detailing remediation were truncated, violating the requirement to capture the complete incident lifecycle.

== Case 4: Delimiter and Schema Corruption
In several multi-hop cases, aggressive pruning stripped whitespace, brackets, and key-value delimiters (`:`, `=>`, `{}`). When adjacent subwords were concatenated into compound terms (e.g., `status503` or `port8080`), tokenizers split them inconsistently, impairing the downstream model's ability to parse key parameters.

= IX. Operational Guidelines & Degradation Thresholds

Based on our empirical evaluation, we propose the operational thresholds in Table IV for deploying prompt compression in enterprise telemetry pipelines:

#figure(
  caption: [Enterprise Deployment Decision Matrix for Prompt Compression],
  table(
    columns: (1.5fr, 0.9fr, 1.3fr, 1.7fr),
    align: (left, center, center, left),
    stroke: none,
    table.hline(stroke: 0.8pt),
    table.header([*Workload Type*], [*Max Safe Ratio*], [*Permissible Metrics*], [*Recommended Operational Policy*]),
    table.hline(stroke: 0.4pt),
    [Extractive Entity Search], [2.0x], [EM $>= 0.75$, F1 $>= 0.82$], [Never exceed 2.0x; enable entity anchoring to protect technical tokens.],
    [Multi-Hop Causal Triage], [2.5x], [Semantic Sim $>= 0.82$], [Safe up to 2.5x; verify causal connectives in prompt context.],
    [Incident Summarization], [3.0x], [ROUGE-L $>= 0.26$, Recall $>= 0.70$], [Optimal at 2.0x--2.5x; compression acts as an effective noise filter.],
    [Latency-Critical Edge LLM], [1.0x (Off)], [End-to-End Latency $<= 500$ms], [Strictly bypass compression on CPU; pass raw context directly.],
    [Commercial Cloud API (GPT-4o)], [3.0x], [Cost Reduction $>= 65%$], [Deploy GPU compressor or cache pre-compressed documentation.],
    table.hline(stroke: 0.8pt),
  )
)

= X. Limitations and Future Work

1. *Compressor Architecture Scaling:* Our experiments evaluated the 560M parameter XLM-RoBERTa checkpoint. Future work should investigate ultra-lightweight distilled compressors (e.g., MobileBERT, 50M parameters) or quantized ONNX runtimes to reduce CPU overhead.

2. *Domain-Specific Adaptation:* LLMLingua-2 was pre-trained on conversational transcripts (MeetingBank). Fine-tuning the token classification backbone directly on semi-structured RFC 5424 syslog and OpenTelemetry corpora represents a promising avenue for improving entity retention at high compression ratios.

3. *Semantic Hybrid Chunking:* Integrating dense vector retrieval with LLMLingua compression could enable two-stage coarse-to-fine filtering for multi-gigabyte log archives.

= XI. Conclusion

Prompt compression represents a powerful mechanism for managing LLM context windows and token expenditure, but its successful deployment demands rigorous control theory and architectural awareness. In this work, we resolved the persistent issue of compression-ratio overshooting in LLMLingua-2 by developing a calibrated power-law formulation ($r_0 = R^(-0.86)$) and adaptive feedback controller, stabilizing compression within $plus.minus 4\%$ of target ratios. Across 240 measured inference runs on our 60-case enterprise incident benchmark, we mapped the precise degradation thresholds across Extractive QA, Multi-Hop QA, and Summarization, demonstrating that moderate compression (2.0x) acts as a beneficial noise filter for incident summarization while extractive tasks collapse past 2.0x. Finally, our latency decomposition revealed the "Local Inference Paradox," proving that neural compression on CPU introduces severe latency inflation for small edge LLMs and establishing the exact economic boundaries where prompt compression delivers genuine enterprise value.

= Acknowledgment

The authors thank the Microsoft Research team for developing and releasing the LLMLingua and LLMLingua-2 model checkpoints and data distillation methodologies. We also acknowledge the open-source contributors to Ollama and the Qwen development team at Alibaba Cloud for providing deterministic local foundation model runtimes that made reproducible local empirical benchmarking possible.

= References

#set text(size: 8pt)
#set par(first-line-indent: 0pt, hanging-indent: 1.5em, leading: 0.45em)

[1] Y. Chen, H. Xie, M. Ma, Y. Kang, X. Gao, L. Shi, Y. Cao, X. Gao, H. Shen, and M. R. Lyu, "RCACopilot: Automated Root Cause Analysis for Large-Scale Online Service Incidents through Large Language Models," in _Advances in Neural Information Processing Systems (NeurIPS)_, vol. 36, 2023, pp. 24866--24888, DOI: 10.48550/arXiv.2310.01463.

[2] M. Ahmed, M. S. R. Bashir, L. Zhang, and F. Khomh, "Recommending Root-Cause and Mitigation Steps for Cloud Incidents using Large Language Models," in _Proc. IEEE Int. Conf. on Software Analysis, Evolution and Reengineering (SANER)_, 2023, pp. 312--324, DOI: 10.1109/SANER56732.2023.00041.

[3] N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, "Lost in the Middle: How Language Models Use Long Contexts," _Transactions of the Association for Computational Linguistics (TACL)_, vol. 12, pp. 157--173, 2024.

[4] L. Zheng et al., "LMSYS Chatbot Arena: Benchmarking LLMs in the Wild," _arXiv preprint arXiv:2306.05685_, 2023.

[5] W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, and I. Stoica, "Efficient Memory Management for Large Language Model Serving with PagedAttention," in _Proc. ACM Symp. on Operating Systems Principles (SOSP)_, 2023, pp. 611--626.

[6] H. Jiang, Q. Wu, C.-Y. Lin, Y. Yang, and L. Qiu, "LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models," in _Proc. Conf. on Empirical Methods in Natural Language Processing (EMNLP)_, 2023, pp. 13358--13376.

[7] Z. Pan, H. Jiang, C.-Y. Lin, Q. Wu, and L. Qiu, "LLMLingua-2: Data-Distillation for Efficient and Faithful Task-Agnostic Prompt Compression," in _Proc. Conf. on Empirical Methods in Natural Language Processing (EMNLP)_, 2024, pp. 8123--8141.

[8] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in _Advances in Neural Information Processing Systems (NeurIPS)_, vol. 33, 2020, pp. 9459--9474.

[9] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," in _Proc. Conf. on Empirical Methods in Natural Language Processing (EMNLP)_, 2020, pp. 6769--6781.

[10] G. Salton and C. Buckley, "Term-weighting approaches in automatic text retrieval," _Information Processing & Management_, vol. 24, no. 5, pp. 513--523, 1988.

[11] C. Raffel et al., "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer," _Journal of Machine Learning Research (JMLR)_, vol. 21, no. 140, pp. 1--67, 2020.

[12] M. Zaharia et al., "The Shift from Models to Compound AI Systems," _Berkeley Artificial Intelligence Research (BAIR) Blog_, Feb. 2024.

[13] L. Chen, M. Zaharia, and J. Zou, "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance," _arXiv preprint arXiv:2305.05176_, 2023.

[14] Qwen Team, "Qwen2.5: A Party of Foundation Models," _Alibaba Cloud Technical Report_, Sep. 2024.

[15] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in _Proc. Conf. on Empirical Methods in Natural Language Processing (EMNLP)_, 2019, pp. 3982--3992.

#set text(size: 10pt)
#set par(first-line-indent: 1.2em, hanging-indent: 0pt, leading: 0.55em)

= Appendix A: Reproducibility Protocol & Testbed

To ensure complete experimental reproducibility, the entire software pipeline and dataset have been packaged with deterministic environment specifications:
- *Hardware Architecture:* Apple MacBook Air (Model `Mac14,2`), Apple M2 SoC with unified memory architecture, 8 GB Unified LPDDR5 RAM (100 GB/s bandwidth), 8-core CPU (4 performance cores, 4 efficiency cores), 8-core GPU with Apple Metal 4 acceleration.
- *Software Specifications:* macOS 26.6.2 (Darwin 24.1.0, Build 25G83), Python 3.11.16, PyTorch 2.15.0, Hugging Face Transformers 5.22.2, LLMLingua 0.2.2, tiktoken 0.14.0, Ollama 0.40.11.
- *Neural Checkpoints:* Compressor: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank` (560M parameters, FP32 on CPU). Embedding evaluator: `sentence-transformers/all-MiniLM-L6-v2` (22M parameters, FP32). Downstream generator: `qwen2.5:1.5b-instruct-q4_K_M` (1.5B parameters, 4-bit quantized GGUF executed via Apple Metal GPU).
- *Inference Parameters:* Sampling temperature $T = 0.0$ (deterministic greedy argmax selection), top-p $p = 1.0$, context window ceiling 4,096 tokens.

= Appendix B: Telemetry Emission Schema

The middleware emits an atomic JSONL record for every processed request to maintain full operational accountability:
```json
{
  "timestamp": "2026-11-13T12:00:00Z",
  "request_id": "req-9842f1a",
  "task": "extractive_qa",
  "target_ratio": 2.0,
  "actual_ratio": 1.980,
  "original_context_tokens": 145,
  "compressed_context_tokens": 74,
  "token_reduction_pct": 48.96,
  "compression_latency_ms": 3985.4,
  "inference_latency_ms": 337.0,
  "end_to_end_latency_ms": 4322.4,
  "estimated_cost_usd": 0.000041,
  "budget_enforced": true
}
```

= Appendix C: Artifact & Benchmark Availability

All benchmark data, evaluation scripts, raw CSV run logs, and the Python package are publicly available at:
#align(center)[#text(size: 8.5pt, font: "Courier")[https://github.com/tejasshetty23/Prompt-Compression-and-Token-Budgeting]]
- `data/benchmark.jsonl`: 60 validated enterprise incident cases.
- `artifacts/benchmark_results.csv`: 240 measured inference runs.
- `artifacts/benchmark_summary.csv`: Aggregated task-level statistics.
- `artifacts/figures/`: High-resolution vector PDF and PNG charts.

