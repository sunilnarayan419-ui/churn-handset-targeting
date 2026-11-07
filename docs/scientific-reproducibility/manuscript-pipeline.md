# Manuscript pipeline (Manubot)

The repository contains a Manubot manuscript whose numbers are generated, not typed. This infrastructure is
preserved unchanged by the documentation work.

```{mermaid}
flowchart LR
    RAW["data/raw/*.csv<br/>local only"] --> ER["scripts/export_results.py<br/>uses the churn_targeting package"]
    ER --> RJ["reports/results.json"]
    NB["reports/notebook_results.json<br/>model comparison"] --> EV
    RJ --> EV["scripts/export_manuscript_variables.py"]
    EV --> BV["build/variables.json<br/>formatted strings"]
    BV --> CK["scripts/check_manuscript.py<br/>StrictUndefined render of content/*.md"]
    CK --> MB["manubot process<br/>content/ + variables"]
    MB --> MD["output/manuscript.md"]
    MD --> PD["pandoc<br/>HTML + DOCX, citations, MathML"]
    PD --> OUT["output/index.html<br/>output/manuscript.docx"]
    OUT --> GH["GitHub Pages<br/>docs.yml on main"]
```

## Steps

| Step | Command | Notes |
|---|---|---|
| Recompute results | `python scripts/export_results.py --data-dir data/raw --out reports/results.json` | Needs raw data and scipy; about 1-2 minutes |
| Format variables | `python scripts/export_manuscript_variables.py` | Writes `build/variables.json` (generated, git-ignored) |
| Check variables | `python scripts/check_manuscript.py` | Fails on any undefined template variable |
| Build | `bash build/build.sh` | Needs the `docs` extra and pandoc ≥ 2.11; writes `output/` |

The workflow `.github/workflows/docs.yml` (named `manuscript`) installs pandoc and `.[docs]`, runs the build,
uploads the artefact and publishes to GitHub Pages on `main`. It is independent of this Sphinx site.

`tests/test_artifacts.py` checks that `reports/results.json` and `reports/notebook_results.json` agree.
Manuscript sources: `content/00.front-matter.md` ... `90.back-matter.md`, `metadata.yaml`,
`manual-references.json`, `citation-tags.tsv`, `images/`.
