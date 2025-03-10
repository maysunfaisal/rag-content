#!/usr/bin/env python3
"""Utility script to generate embeddings."""

import os
import sys
import time
import yaml

from pathlib import Path

# from llama_index.readers.file.flat.base import FlatReader

# Add the common_embedding.py to the Python path
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scripts_dir)

from common_embeddings import (
    FileMetadataProcessor,
    filter_out_invalid_nodes,
    get_common_arg_parser,
    get_settings,
    print_unreachable_docs_warning,
    process_documents,
    save_index,
    save_metadata,
)


RHDH_DOCS_ROOT_URL = "https://docs.redhat.com/en/documentation/red_hat_developer_hub/"
RHDH_DOCS_VERSION = "1.4"


def process_node(node: dict, dir: str = "", file_url_list: dict = {}) -> dict:
    """Process YAML node from the topic map."""
    currentdir = dir
    if "Topics" in node:
        currentdir = os.path.join(currentdir, node["Dir"])
        for subnode in node["Topics"]:
            file_url_list = process_node(
                subnode, dir=currentdir, file_url_list=file_url_list
            )
    else:
        dir_basename = os.path.basename(currentdir)
        file_url_list[dir_basename] = node["WebpageID"]
    return file_url_list

class RHDHDocsMetadata(FileMetadataProcessor):
    """Generates metadata from plaintext documentation."""

    def __init__(self, root_dir: str, rhdh_docs_version: str, topic_map: str):
        super().__init__()
        self.root_dir = root_dir
        self.rhdh_docs_version = rhdh_docs_version
        self.topic_map = topic_map
        self.file_url_list: dict = {}

        with open(topic_map, "r") as fin:
            topic_map = yaml.safe_load_all(fin)
            for map in topic_map:
                self.file_url_list = process_node(map, file_url_list=self.file_url_list)

    def url_function(self, file_path: str):

        dir_basename = os.path.basename(os.path.dirname(file_path))

        return (
            RHDH_DOCS_ROOT_URL
            + self.rhdh_docs_version
            + "/html-single/"
            + self.file_url_list[dir_basename]
            + "/index"
        )


if __name__ == "__main__":

    start_time = time.time()
    parser = get_common_arg_parser()
    parser.add_argument(
        "-v", "--rhdh-version", help="RHDH version", default=RHDH_DOCS_VERSION
    )
    parser.add_argument("--topic-map", "-t", required=True, help="The topic map file")
    args = parser.parse_args()
    print(f"Arguments used: {args}")

    topic_map = os.path.normpath(os.path.join(os.getcwd(), args.topic_map))

    # OLS-823: sanitize directory
    PERSIST_FOLDER = os.path.normpath("/" + args.output).lstrip("/")
    if PERSIST_FOLDER == "":
        PERSIST_FOLDER = "."

    EMBEDDINGS_ROOT_DIR = os.path.abspath(args.folder)
    if EMBEDDINGS_ROOT_DIR.endswith("/"):
        EMBEDDINGS_ROOT_DIR = EMBEDDINGS_ROOT_DIR[:-1]

    os.environ["HF_HOME"] = args.model_dir
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    settings, embedding_dimension, storage_context = get_settings(
        args.chunk, args.overlap, args.model_dir
    )

    metadata_processor = RHDHDocsMetadata(EMBEDDINGS_ROOT_DIR, args.rhdh_version, topic_map)

    # Load documents
    documents = process_documents(
        args.folder,
        metadata_func=metadata_processor.file_metadata_func,
        num_workers=args.workers,
    )

    unreachables = metadata_processor.n_unreachable_urls()
    # Create chunks/nodes
    nodes = settings.text_splitter.get_nodes_from_documents(documents)

    # Filter out invalid nodes
    good_nodes = filter_out_invalid_nodes(nodes)

    # Create & save Index
    save_index(good_nodes, storage_context, args.index, PERSIST_FOLDER)

    # Save metadata
    save_metadata(start_time, args, embedding_dimension, documents, PERSIST_FOLDER)

    if unreachables > 0:
        print_unreachable_docs_warning(unreachables)
