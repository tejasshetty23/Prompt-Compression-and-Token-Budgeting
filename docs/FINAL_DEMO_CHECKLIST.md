# Final Demonstration Checklist

## 1. Demonstration objective

Demonstrate the prompt-compression middleware and its evaluation workflow. The current repository README documents a FastAPI `/compress` endpoint. A separate Gradio/Streamlit interface is not established by the README; do not claim one exists unless it is implemented and tested.

## 2. Suggested live demo sequence

1. Start Ollama and confirm the selected local model is available.
2. Activate the Python virtual environment and install project dependencies.
3. Run the test suite.
4. Start the FastAPI service.
5. Submit a representative question and technical-log context to `/compress`.
6. Show the original prompt, compressed prompt, requested ratio, actual token counts, and token budget outcome if returned by the endpoint.
7. Repeat with 2x, 3x, and 5x targets.
8. Run or show the benchmark results and task-level metrics.
9. Explain the compression-quality-latency trade-off, including the reported end-to-end latency increase at 5x.
10. Explain that commercial API savings are estimated only after provider pricing and token counts are supplied; local Ollama cost is not commercial API billing.

## 3. Evidence to capture

- Successful test-suite output.
- API startup output.
- Successful `/compress` request and response.
- Example input and compressed output.
- Benchmark command and output CSV.
- Accuracy and latency figures.
- Any errors or limitations encountered.

## 4. Optional UI enhancement

If a UI is required by the course review, add a small Streamlit or Gradio front end that calls the existing API. Suggested controls:

- Upload a supported file or paste context.
- Enter a question.
- Select target compression ratio.
- Set token budget.
- Display original and compressed token counts.
- Display compressed context and model response.
- Display measured latency and task metric where available.

Do not mark the UI requirement complete until it is implemented and tested.

## 5. Status

**Status: demo plan; complete the checklist during the actual demonstration and retain screenshots/logs as evidence.**
