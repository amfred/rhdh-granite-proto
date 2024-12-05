# Prototype of Granite and MCP integration with Red Hat Developer Hub

Python script demonstrating use of the [Model Context Protocol](https://modelcontextprotocol.io) (MCP), providing both client and server capabilities for integrating with [Red Hat Developer Hub](https://developers.redhat.com/rhdh/overview) and the [IBM Granite-3.0-8b-Instruct model](https://huggingface.co/ibm-granite/granite-3.0-8b-instruct).

## Overview

## Installation and Setup

The recommended Python version is v3.12 for maximum compatibility between Pytorch and MCP.  [Pyenv](https://github.com/pyenv/pyenv) is an easy way to manage your Python versions and switch between versions as needed.

After switching to the recommended version of Python, upgrade pip:
```
pip install --upgrade pip
```

Use the provided requirements.txt file to install the required libraries, including Pytorch and MCP:
```
pip install -r requirements.txt
```

Start up Granite in the local ollama server:
```
ollama pull granite3-dense:8b
ollama serve
```

Run the granite-example script to download and test the Granite model:
```
python granite-from-ollama.py
```

Run the test client with a local server:
```
export RHDH_API_KEY = <Bearer token for Developer Hub's catalog APIs. Read only is sufficient.>
export RHDH_API_URL = <URL for the MCP server hosting the catalog API, example http://0.0.0.0:8000 for localhost>
export GRANITE_API_KEY = <API key for the model inference server hosting granite3-dense:8b also known as granite-3.0-8b-instruct >
export GRANITE_API_URL = <URL for an Open AI API compatible server hosting the granite3-dense:8b model, example https://ibm-granite-3.0-8b-instruct-vllm.apps.your-openshift-ai-cluster.com>

python rhdh_catalog_client.py
```

Run the server in SSE mode:
```
python rhdh_catalog_server.py --port 8000 --transport sse

INFO:server:Starting up rhdh-api server using transport: sse
INFO:server:Starting up sse server on port: 8000
INFO:     Started server process [16234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Useful curl commands for testing the models directly using the Open AI API:

This works for a VLLM server hosting ibm-granite-8b-code-instruct:
```
curl -X POST \
  "$GRANITE_API_URL/v1/chat/completions" \                
  -H "Authorization: Bearer $GRANITE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ibm-granite-8b-code-instruct",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is the plot of the movie Inception?"
      }
    ]
  }' \
  -k
```

This works for an Ollama server hosting granite3-dense:8b also known as granite-3.0-8b-instruct:
```
  curl -X POST \      
  "$GRANITE_API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $GRANITE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "granite3-dense:8b",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is the plot of the movie Inception?"
      }
    ]
  }' \
  -k

```