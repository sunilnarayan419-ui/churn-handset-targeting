#!/usr/bin/env bash
# Build the manuscript: variables -> Manubot (citations, templates) -> pandoc (HTML + DOCX).
# Requires: pip install -e ".[docs]" and pandoc >= 2.11 on PATH.
set -o errexit -o pipefail

python scripts/export_manuscript_variables.py
python scripts/check_manuscript.py

rm -rf output && mkdir -p output ci/cache
manubot process \
  --content-directory=content \
  --output-directory=output \
  --cache-directory=ci/cache \
  --template-variables-path=results=build/variables.json \
  --skip-citations \
  --log-level=INFO

# Manubot writes output/manuscript.md; the Pandoc filter resolves citations and writes references.
cp -r content/images output/images
pandoc output/manuscript.md \
  --from=markdown+smart --to=html5 --standalone --embed-resources --resource-path=output \
  --filter=pandoc-manubot-cite --citeproc \
  --mathml --toc --number-sections \
  --metadata-file=content/metadata.yaml --css=build/manuscript.css \
  --output=output/index.html
pandoc output/manuscript.md \
  --from=markdown+smart --to=docx --resource-path=output \
  --filter=pandoc-manubot-cite --citeproc \
  --metadata-file=content/metadata.yaml --output=output/manuscript.docx
echo "built output/index.html and output/manuscript.docx"
