# Prototype of Granite and MCP integration with Red Hat Developer Hub

Python script demonstrating use of the [Model Context Protocol](https://modelcontextprotocol.io) (MCP), providing both client and server capabilities for integrating with [Red Hat Developer Hub](https://developers.redhat.com/rhdh/overview) and the [IBM Granite-3.0-8b-Instruct model](https://huggingface.co/ibm-granite/granite-3.0-8b-instruct).

## Overview

## Installation and Setup

The recommended Python version is v3.12 for maximum compatibility between Pytorch and MCP.  [Pyenv](https://github.com/pyenv/pyenv) is an easy way to manage your Python versions and switch between versions as needed.

After switching to the recommended version of Python, upgrade pip:
```
pip install --upgrade pip
```

Use the provided requirements.txt file to install the required libraries:
```
pip install -r requirements.txt
```

Run the granite-example script to download and test the Granite model:
```
python granite-example-1.py
```