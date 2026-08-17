# Disclaimer

Multi-Agent Research Assistant is provided **as-is**, free of charge, for anyone to run, study, modify, and build on. Please read this before you use it.

## You run this on your own machine, with your own keys

This is a local-first tool. When you run it, you provide your own API keys (OpenAI-compatible, Agnes AI, and/or a local Ollama server) and everything executes on your own machine. Nobody else's infrastructure is involved, and the maintainer has no visibility into how you use it.

## You are responsible for your data

Everything the app processes — research queries, uploaded PDFs, search results, and generated reports — is **100% your responsibility**:

- **What you enter.** Don't submit content you don't have the right to process, or content that's confidential, regulated, or sensitive, unless you understand and accept the consequences of sending it to whichever provider (OpenAI-compatible API, Agnes AI, or your local Ollama) you've configured.
- **Where it goes.** Anything routed through a hosted reasoning provider (OpenAI-compatible or Agnes AI) leaves your machine and is subject to that provider's own terms, privacy policy, and data-retention practices. Review those before sending anything sensitive. Local Ollama calls and DuckDuckGo/arXiv searches do not require API keys, but web search queries themselves still leave your machine.
- **What's stored locally.** Every research run (query, plan, sources, and final report) is saved to a local JSON file (`data/history.json`) on your own disk, in plaintext, with no encryption. It is never uploaded anywhere by this project. Delete it any time you want to clear your history.
- **Compliance.** If you're subject to GDPR, HIPAA, an employer's data policy, or any other regulatory or contractual obligation, it's on you to ensure your use of this tool — and the providers you point it at — complies with those obligations.

## No warranty

This software is provided under the MIT License **"AS IS", WITHOUT WARRANTY OF ANY KIND**, express or implied. The author is not liable for any damages, data loss, unexpected API charges from a provider you configured, or other outcomes arising from your use of this project. See [LICENSE](LICENSE) for the full legal text.

## Accuracy of research output

This tool uses LLMs to plan research, summarize sources, and write reports. LLMs can be wrong, and web search results can be outdated, biased, or inaccurate. The credibility scoring in `tools/credibility.py` is a deterministic heuristic (domain reputation, recency, lexical overlap) — it is not a guarantee of accuracy, and citations are only as reliable as the sources retrieved. Always verify anything important before relying on it.

## No financial relationship

This project does not want or accept donations, sponsorships, or any form of financial support. See [README.md](README.md#support-the-project) for details. Using this software creates no financial relationship between you and the author.

If any of this is unclear, please open an issue — see [SUPPORT.md](SUPPORT.md).
