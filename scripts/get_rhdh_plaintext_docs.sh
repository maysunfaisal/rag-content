#!/bin/bash
set -eou pipefail

RHDH_VERSION=$1

trap "rm -rf red-hat-developers-documentation-rhdh" EXIT

rm -rf rhdh-product-docs-plaintext/${RHDH_VERSION}

git clone --single-branch --branch release-${RHDH_VERSION} https://github.com/redhat-developer/red-hat-developers-documentation-rhdh

pdm run scripts/asciidoctor-text/rhdh_convert_it_all.py \
    -r red-hat-developers-documentation-rhdh \
    -o rhdh-product-docs-plaintext/${RHDH_VERSION} \
    -t https://raw.githubusercontent.com/maysunfaisal/rag-content/refs/heads/poc-2/scripts/asciidoctor-text/rhdh_topic_map.yaml \
    -a https://raw.githubusercontent.com/maysunfaisal/rag-content/refs/heads/poc-2/scripts/asciidoctor-text/rhdh_attributes.yaml

# for f in $(cat config/exclude.conf); do
#     rm ocp-product-docs-plaintext/${RHDH_VERSION}/$f
# done
