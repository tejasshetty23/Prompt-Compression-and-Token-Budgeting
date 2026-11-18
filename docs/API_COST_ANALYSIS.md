# API Cost Savings Analysis

## 1. Purpose

The project guidelines require a comparison of API cost savings at the 2x, 3x, and 5x prompt-compression targets. The current benchmark uses local Ollama inference, for which the configured API cost is zero. Therefore, local benchmark cost fields cannot demonstrate commercial API savings.

This document defines a reproducible *pricing-model estimate*. It must not be presented as measured provider billing.

## 2. Required inputs

For each benchmark case and compression target, record:

- Original input-token count (`T_original`)
- Compressed input-token count (`T_compressed`)
- Output-token count (`T_output`)
- Provider input-token price per 1,000,000 tokens (`P_in`)
- Provider output-token price per 1,000,000 tokens (`P_out`)

Use the same provider, model, region, pricing tier, and date for all compared configurations. Record the source and retrieval date of the pricing schedule in the final report. Do not use a price copied from an undated source.

## 3. Cost equations

For a single request:

`Cost_original = (T_original / 1,000,000 × P_in) + (T_output_original / 1,000,000 × P_out)`

`Cost_compressed = (T_compressed / 1,000,000 × P_in) + (T_output_compressed / 1,000,000 × P_out)`

`Savings = Cost_original - Cost_compressed`

`Savings_percent = 100 × (Cost_original - Cost_compressed) / Cost_original`

If the same output is generated in both conditions, output-token cost cancels out. If output lengths differ, include both output costs rather than assuming they are equal.

For a dataset, sum request costs before calculating the overall percentage:

`Dataset_savings_percent = 100 × (Σ Cost_original - Σ Cost_compressed) / Σ Cost_original`

## 4. Results table to complete

Populate this table from actual token counts and a dated provider price schedule. Do not leave illustrative values in a submitted results table.

| Target | Original input tokens | Compressed input tokens | Original cost | Compressed cost | Savings (%) |
|---|---:|---:|---:|---:|---:|
| 2x | TBD | TBD | TBD | TBD | TBD |
| 3x | TBD | TBD | TBD | TBD | TBD |
| 5x | TBD | TBD | TBD | TBD | TBD |

## 5. Interpretation and limitations

- This is a modelled cost comparison unless requests are actually sent to the priced API and provider usage/billing records are collected.
- Compression itself has compute cost. If compression runs locally, report its runtime separately; if it uses a paid service, include that charge.
- Token savings do not automatically equal the same percentage reduction in total bill when output tokens, cached tokens, minimum charges, or other fees apply.
- The repository's current local Ollama benchmark has zero configured API cost. Do not describe that as a measured commercial API saving.

## 6. Evidence to attach

1. Provider pricing source and date checked.
2. Export of original and compressed token counts.
3. Calculation script or spreadsheet.
4. Per-ratio summary and assumptions.
5. If available, provider usage records for a small validation run.

## 7. Status

**Status: analysis specification; empirical commercial API savings remain to be measured.**
