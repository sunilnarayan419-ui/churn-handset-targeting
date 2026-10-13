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
  --log-level=INFO

# Manubot writes output/manuscript.md and output/references.json (citations become hashed ids).
cp -r content/images output/images
pandoc output/manuscript.md \
  --from=markdown+smart --to=html5 --standalone --embed-resources --resource-path=output \
  --citeproc --bibliography=output/references.json \
  --mathml --toc --number-sections \
  --metadata-file=content/metadata.yaml --css=build/manuscript.css \
  --output=output/index.html
pandoc output/manuscript.md \
  --from=markdown+smart --to=docx --resource-path=output \
  --citeproc --bibliography=output/references.json \
  --metadata-file=content/metadata.yaml --output=output/manuscript.docx
echo "built output/index.html and output/manuscript.docx"
