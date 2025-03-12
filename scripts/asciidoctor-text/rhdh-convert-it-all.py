#!/usr/bin/env python3

"""Utility script to convert OCP docs from adoc to plain text."""

import argparse
import os
import subprocess
import sys
import shutil
import requests
import yaml

from git import Repo


# def node_in_distro(node: dict, distro: str) -> bool:
#     """Check if a node is in a distro."""
#     return node.get("Distros", "") == "" or distro in node.get("Distros", "").split(",")


def process_node(node: dict, dir: str = "", file_list: list = []) -> list:
    """Process YAML node from the topic map."""
    currentdir = dir
    if "Topics" in node:
        currentdir = os.path.join(currentdir, node["Dir"])
        for subnode in node["Topics"]:
            file_list = process_node(
                subnode, dir=currentdir, file_list=file_list
            )
    else:
        file_list.append(os.path.join(currentdir, node["File"]))
    return file_list


def convert_to_txt(repo: str, output_dir: str, topic_map_url: str, attributes_url: str) -> None:
    """Process YAML node from the topic map."""

    repo_dir = "red-hat-developers-documentation-rhdh"
    topic_map = "rhdh_topic_map.yaml"
    attributes = "rhdh_attributes.yaml"

    try:
        shutil.rmtree(repo_dir)
        Repo.clone_from(repo, repo_dir, branch="main")
    except Exception:
        print("error deleting " + repo_dir + " and git cloning repository " + repo)


    # urllib.request.urlretrieve(topic_map_url, topic_map)
    # urllib.request.urlretrieve(attributes_url, attributes)
    response = requests.get(topic_map_url)
    if response.status_code == 200:
        with open(topic_map, "wb") as file:
            file.write(response.content)
    else:
        print("Failed to download file from " + topic_map_url)

    response = requests.get(attributes_url)
    if response.status_code == 200:
        with open(attributes, "wb") as file:
            file.write(response.content)
    else:
        print("Failed to download file from " + attributes_url)

    attribute_list: list = []
    if attributes is not None:
        # attributes = os.path.normpath(os.path.join(os.getcwd(), attributes))
        with open(attributes, "r") as fin:
            attributes = yaml.safe_load(fin)
        for key, value in attributes.items():
            attribute_list = [*attribute_list, "-a", key + "=%s" % value]

    # topic_map = os.path.normpath(os.path.join(os.getcwd(), topic_map))
    with open(topic_map, "r") as fin:
        topic_map = yaml.safe_load_all(fin)
        mega_file_list: list = []
        for map in topic_map:
            file_list: list = []
            file_list = process_node(map, file_list=file_list)
            mega_file_list = mega_file_list + file_list

    output_dir = os.path.normpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    repo_dir = os.path.normpath(repo_dir)
    script_dir = os.path.dirname(os.path.realpath(__file__))

    for filename in mega_file_list:
        output_file = os.path.join(output_dir, filename + ".txt")
        os.makedirs(os.path.dirname(os.path.realpath(output_file)), exist_ok=True)
        input_file = os.path.join(repo_dir, filename + ".adoc")
        converter_file = os.path.join(script_dir, "text-converter.rb")
        print("Processing: " + input_file)
        command = ["asciidoctor"]
        command = command + attribute_list
        command = [
            *command,
            "-r",
            converter_file,
            "-b",
            "text",
            "-o",
            output_file,
            "--trace",
            "--quiet",
            input_file,
        ]
        result = subprocess.run(command, check=False)  # noqa: S603
        if result.returncode != 0:
            print(result)
            print(result.stdout)

    print(mega_file_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This command converts the openshift-docs assemblies to plain text.",
        usage="convert-it-all [options]",
    )

    # print(sysconfig.get_paths()["purelib"])

    parser.add_argument(
        "--repo",
        "-r",
        required=True,
        help="repo to fetch",
    )
    parser.add_argument("--topic-map", "-t", required=True, help="The topic map file")
    parser.add_argument(
        "--output-dir", "-o", required=True, help="The output directory for text"
    )
    parser.add_argument(
        "--attributes", "-a", help="An optional file containing attributes"
    )

    args = parser.parse_args(sys.argv[1:])
    convert_to_txt(args.repo, args.output_dir, args.topic_map, args.attributes)
