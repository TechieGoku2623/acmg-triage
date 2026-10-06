# llm_cost results

n excerpts = 12. Local render+tokenize = 6.81 ms total. API RTT = unmeasured.

Default literature model: gemini-2.0-flash ($0.000528/variant). Escalate to a larger tier only when the small-model cache miss fails structured-output validation.

| model | mean input tok/prompt | input tok/variant (3 nodes) | USD/variant | USD/10k variants |
| --- | --- | --- | --- | --- |
| gpt-4o-mini | 160.2 | 480.8 | 0.000792 | 7.92 |
| gpt-4o | 160.2 | 480.8 | 0.013202 | 132.02 |
| claude-haiku-4-5 | 160.2 | 480.8 | 0.006481 | 64.81 |
| claude-sonnet-4-5 | 160.2 | 480.8 | 0.019442 | 194.42 |
| gemini-2.0-flash | 160.2 | 480.8 | 0.000528 | 5.28 |
