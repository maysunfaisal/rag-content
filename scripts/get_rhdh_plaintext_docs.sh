#!/bin/bash
set -eou pipefail

RHDH_VERSION=$1

trap "rm -rf red-hat-developers-documentation-rhdh" EXIT

rm -rf rhdh-product-docs-plaintext/${RHDH_VERSION}

git clone --single-branch --branch release-${RHDH_VERSION} https://github.com/redhat-developer/red-hat-developers-documentation-rhdh

python3 scripts/asciidoctor-text/convert-it-all.py -i red-hat-developers-documentation-rhdh \
    -o rhdh-product-docs-plaintext/${RHDH_VERSION} -a scripts/asciidoctor-text/rhdh-attributes.yaml \
    -t scripts/asciidoctor-text/topic_map.yaml

# for f in $(cat config/exclude.conf); do
#     rm ocp-product-docs-plaintext/${RHDH_VERSION}/$f
# done
