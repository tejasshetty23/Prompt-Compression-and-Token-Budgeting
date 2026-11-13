# Benchmark Methodology and Experimental Design

## 1. Executive Summary
This document specifies the scientific methodology, system architecture, and evaluation protocols for benchmarking prompt compression and token budgeting using LLMLingua-2 on enterprise telemetry and operational documentation.

The objective is to establish predictable compression-ratio control, measure task-specific quality degradation, dissect latency bottlenecks in local versus cloud inference, and determine empirical degradation thresholds for enterprise deployment.

---

## 2. Experimental Design
The benchmark evaluates four compression targets:
* **1.0x (Baseline)**: Uncompressed raw context.
* **2.0x Target**: 50% nominal token reduction.
* **3.0x Target**: 66.7% nominal token reduction.
* **5.0x Target**: 80% nominal token reduction.

### Controlled Invariants
To isolate the effect of prompt compression from experimental confounds, the following variables are strictly controlled across all runs:
1. **Downstream Generative Model**: Fixed to `Qwen 2.5 1.5B` served locally via Ollama (`http://localhost:11434/v1`).
2. **Decoding Parameters**: Deterministic greedy decoding (`temperature = 0.0`).
3. **Compressor Model**: `microsoft/llmlingua-2-xlm-roberta-large-meetingbank` (560M parameters, XLM-RoBERTa encoder-only classifier).
4. **Context Isolation**: System instructions and user questions are anchored as fixed invariants; compression is applied strictly to document and log context.
5. **Warm-Up Protocol**: An unmeasured compressor and downstream model warm-up call precedes all benchmark runs, eliminating JIT/model-loading initialization artifacts from latency measurements.
6. **Token-Window Chunking**: Fixed chunk size of 800 tokens with 80-token overlap, ranked lexically by question term overlap before compression.

---

## 3. Compression-Ratio Control Theory

### 3.1 Root Cause of LLMLingua-2 Ratio Overshoot
In default LLMLingua-2 configurations, requesting a compression ratio $R$ via nominal retention rate $r_{\text{nom}} = \frac{1}{R}$ causes severe over-compression (e.g., requested 5.0x produces 6.2x to 7.7x actual compression).

Mathematical and empirical analysis reveals four primary root causes:
1. **Strict Percentile Thresholding**: LLMLingua-2 computes the retention threshold as:
   $$\text{threshold} = \text{percentile}(\text{token\_probs}, \lfloor 100 \times (1 - r) + 1 \rfloor)$$
   Tokens are retained only if $\text{prob} > \text{threshold}$ (strict inequality). The $+1$ offset shifts the cutoff upwards by one full percentile, discarding up to 1% additional tokens by design. When probability ties exist at the threshold, strict inequality discards all tied tokens, causing further retention loss.
2. **Subword-to-Word Expansion Disconnect**: LLMLingua-2 merges subwords into words using mean pooling, but computes the percentile over expanded subword tokens. Technical log artifacts (timestamps, UUIDs, stack frames) contain multiple subwords with low retention probabilities; dropping these multi-token words removes disproportionately more tokens than the percentile calculation assumes.
3. **Delimiter Concatenation**: Reconstructing retained strings merges adjacent subwords, reducing total token count in downstream BPE/tiktoken tokenizers.
4. **Non-Linear Rate-to-Ratio Response**: The relationship between nominal retention rate and actual token reduction is non-linear across enterprise log syntax.

### 3.2 Calibrated Power-Law Controller
To achieve predictable compression, we derived an empirical calibration curve mapping target ratio $R$ to effective retention rate $r_0(R)$:
$$r_0(R) = R^{-0.86}$$

Empirical validation shows that this power-law calibration accurately aligns actual compression:
* Target 2.0x: $r_0(2.0) = 0.551 \implies \text{actual ratio } \approx 1.95\text{x}$
* Target 3.0x: $r_0(3.0) = 0.389 \implies \text{actual ratio } \approx 3.13\text{x}$
* Target 5.0x: $r_0(5.0) = 0.251 \implies \text{actual ratio } \approx 4.76\text{x}$

### 3.3 Closed-Loop Proportional Feedback
For outlier contexts where initial compression deviates from target ratio $R_{\text{target}}$ by more than tolerance $\tau = 0.15$:
$$r_1 = \text{clip}\left(r_0 \times \frac{R_{\text{actual}}}{R_{\text{target}}}, 0.05, 1.0\right)$$
A single refinement pass brings the ratio within tolerance while bounding computational overhead.

---

## 4. Evaluation Tasks and Metrics

### 4.1 Extractive QA
* **Metric 1: Exact Match (EM)**: Normalized binary indicator of exact string equivalence between prediction and ground truth.
* **Metric 2: Token-Level F1**: Harmonic mean of precision and recall over alphanumeric tokens.

### 4.2 Multi-Hop QA
* **Metric 1: Token-Level F1**: Evaluates overlap with multi-clause reference answers.
* **Metric 2: ROUGE-L**: Measures longest common subsequence overlap, assessing sentence fluency and relational ordering.
* **Metric 3: Semantic Cosine Similarity**: Evaluates sentence embeddings using `sentence-transformers/all-MiniLM-L6-v2`:
  $$\text{Sim}(p, r) = \frac{\mathbf{e}_p \cdot \mathbf{e}_r}{\|\mathbf{e}_p\|_2 \|\mathbf{e}_r\|_2}$$
  Provides semantic invariance against paraphrasing and alternative syntactic orderings.
* **Metric 4: Key Fact Recall**: Measures the proportion of salient entities, actions, and numerical parameters from the reference that appear in the prediction.

### 4.3 Summarization
* **Metric 1: ROUGE-L**: Structural longest common subsequence overlap.
* **Metric 2: ROUGE-1 / ROUGE-2**: Unigram and bigram overlap with reference incident summaries.
* **Metric 3: Key Fact Recall**: Quantitative assessment of cause, impact, resolution, and outcome retention.

### 4.4 System & Efficiency Metrics
* **Original Context Tokens ($N_{\text{orig}}$)**: Token count of raw context (tiktoken `cl100k_base`).
* **Compressed Context Tokens ($N_{\text{comp}}$)**: Token count of retained context.
* **Actual Compression Ratio**: $\frac{N_{\text{orig}}}{\max(1, N_{\text{comp}})}$.
* **Token Reduction Percentage**: $\left(1 - \frac{N_{\text{comp}}}{N_{\text{orig}}}\right) \times 100\%$.
* **Compression Latency ($T_{\text{comp}}$)**: Wall-clock time spent in RoBERTa forward pass, token scoring, and filtering.
* **Inference Latency ($T_{\text{infer}}$)**: Wall-clock time spent in Ollama downstream model generation.
* **End-to-End Latency ($T_{\text{e2e}}$)**: Total wall-clock time ($T_{\text{comp}} + T_{\text{infer}}$).
* **Estimated Cloud Cost**: Projected input and output costs under commercial model pricing.

---

## 5. Degradation Thresholds and Safe Ratio Criteria
A target compression ratio $R$ is certified as **Safe** for task $\mathcal{T}$ if and only if:
$$\frac{M_{\mathcal{T}}(1.0\text{x}) - M_{\mathcal{T}}(R)}{M_{\mathcal{T}}(1.0\text{x})} \le \epsilon_{\mathcal{T}}$$
where $M_{\mathcal{T}}$ is the task's primary metric and $\epsilon_{\mathcal{T}}$ is the maximum allowable degradation tolerance:
* Extractive QA ($\epsilon = 0.15$ on Exact Match / F1).
* Multi-Hop QA ($\epsilon = 0.15$ on Semantic Similarity / F1).
* Incident Summarization ($\epsilon = 0.15$ on ROUGE-L).
