# Dataset Scope and External Validation

## 1. Dataset currently described in the repository

The repository README describes a curated synthetic benchmark containing 60 cases:

| Task | Number of cases |
|---|---:|
| Extractive QA | 20 |
| Multi-hop QA | 20 |
| Incident summarization | 20 |
| **Total** | **60** |

The cases cover nine infrastructure archetypes: Kubernetes, Kafka, PostgreSQL, Redis, CoreDNS, OAuth/IAM, gRPC microservices, CI/CD, and BGP/Cloud networking.

## 2. Ingestion capability versus evaluation evidence

The implementation describes ingestion utilities for `.log`, `.pdf`, `.txt`, `.md`, `.csv`, and `.jsonl` files, with PDF extraction through `pdfplumber`.

File-format support demonstrates that the software can accept these formats. It does not, by itself, demonstrate that the benchmark was run on real enterprise logs or multi-page PDFs.

The current README explicitly characterises the benchmark dataset as synthetic and curated, not production telemetry.

## 3. Recommended validation extension

If time and permissions allow, add a small, anonymised validation set drawn from public technical incident reports, public sample logs, or appropriately authorised non-sensitive documents.

For each added source, record:

- Source name and public URL or provenance.
- Access date and licence/permission where relevant.
- Whether identifying or confidential information was removed.
- Document type and approximate length.
- Task/question and reference answer creation procedure.
- Inclusion/exclusion criteria.

Do not upload confidential company logs, personal data, credentials, IP addresses that should remain private, or other restricted information.

## 4. If external data cannot be added

Keep the current dataset and state the limitation transparently:

"This study evaluates a curated synthetic benchmark designed around nine enterprise infrastructure archetypes. Although the middleware supports multiple document and log formats, the present evaluation does not establish performance on production enterprise telemetry. External validation is left as future work."

## 5. Status

**Status: documentation of current scope and limitation; no real-world dataset is claimed by this document.**
