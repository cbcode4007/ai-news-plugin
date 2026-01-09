## AI News Plugin

A small command-line program that delivers accurate news information from Global News upon request, tailored to the exact contents of the question. It is mainly meant to be used as part of the AI Operator framework, which will call it to defer any news-related queries.

It takes the following parameters (besides the always necessary script name):
- User query string ("Are there any tech headlines today?", etc.)
- Optionally, Log mode string ("info", the default, or "debug", for whether detailed debug lines are recorded in the log or just basic info)
