# Capability Map: Netflix Recommender Portfolio

| Module id | Responsibility | Depends on |
|---|---|---|
| `reproducible-story` | Explain the project, document reproducible local use, and prepare an interview-ready case study | — |
| `evaluation-quality` | Make recommender evaluation defensible, interpretable, and reproducible | `reproducible-story` |
| `hosted-demo` | Publish a reliable interactive demo and document how it is deployed | `reproducible-story` |

Build order: `reproducible-story` → `evaluation-quality` and `hosted-demo` (independent of each other).
