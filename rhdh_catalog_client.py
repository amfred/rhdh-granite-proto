import logging
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# If this was a purely MCP test client I wouldn't need these
import ollama
import timeit
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rhdh-catalog-client")

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python", # Executable
    args=["rhdh_catalog_server.py"], # Optional command line arguments
    env=None
)

# Utility method because even when I ask the Granite model to ONLY return a URL, it usually
# returns an explanation with the URL.
def extract_url(string):
    url_pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    match = re.search(url_pattern, string)
    if match:
        return match.group(0)
    else:
        return None

# Utility method to call the local granite model
async def call_granite_on_ollama(prompt) -> str:
    start = timeit.default_timer()
    response = ollama.chat(model='granite3-dense:8b', messages=[
    {
        'role': 'user',
        'content': prompt,
    }])
    inferenceTime = timeit.default_timer() - start
    responseStr = response['message']['content']
    logger.info(f"The inference service response is: \n{responseStr}")
    logger.info(f"The inference execution time is: {inferenceTime}")
    return responseStr

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # The example server only supports tools:
        
            # List available prompts
            # prompts = await session.list_prompts()
            # logger.info("Prompts: ", prompts)

            # Get a prompt
            # prompt = await session.get_prompt("example-prompt", arguments={"arg1": "value"})
            # logger.info("Prompt: ", prompt)

            # List available resources
            #resources = await session.list_resources()
            #logger.info("Resources: ", resources)

            # List available tools
            toolsList = await session.list_tools()
            logger.info("List of tools: \n".join(map(str, toolsList.tools)))

            # Read a resource
            #resource = await session.read_resource("file://some/path")
            #logger.info("Resource: ", resource)

            # Call the fetch tool
            result = await session.call_tool("fetch", arguments={"url": "https://example.com"})
            logger.info(f"First few characters from website: \n{result.content[0].text[:66]}")

            if "RHDH_API_URL" not in os.environ:
                raise ValueError("Missing required environment variable 'RHDH_API_URL'")
            elif "RHDH_API_KEY" not in os.environ:
                raise ValueError("Missing required environment variable 'RHDH_API_KEY'")
            
            url = os.environ.get('RHDH_API_URL')
            apiKey = os.environ.get('RHDH_API_KEY')

            # Call the Developer Hub APIs in various ways
            # Represent each of these as a separate tool
            result = await session.call_tool("get_tags", arguments={
                "url": url,
                "apiKey": apiKey,
                })
            logger.info(f"Tag list from RHDH API: \n{result.content[0].text}")

            result = await session.call_tool("get_apis", arguments={
                "url": os.environ.get('RHDH_API_URL', None),
                "apiKey": os.environ.get('RHDH_API_KEY', None),
                })
            logger.info(f"API list from RHDH API: \n{result.content[0].text}")

            result = await session.call_tool("get_inference_servers", arguments={
                "url": os.environ.get('RHDH_API_URL', None),
                "apiKey": os.environ.get('RHDH_API_KEY', None),
                })
            logger.info(f"Inference server list from RHDH API: \n{result.content[0].text}")

            # This section isn't using MCP yet; it's just demonstrating that a model
            # can help to parse the data that comes back from Developer Hub.
            # Ask the Granite model to do something with the catalog results

            signupResponse = await call_granite_on_ollama('Given the following context, where should I go to sign up for the 3scale-based developer-model-service? Respond with ONLY the URL:\n'+result.content[0].text)
            logger.info(f"The service sign-up response is: \n{signupResponse}")

            ollamaResponse = await call_granite_on_ollama('Given the following context, what is the ollama inference server URL? Respond with ONLY the URL:\n'+result.content[0].text)
            logger.info(f"The inference service response is: \n{ollamaResponse}")

            vllmResponse = await call_granite_on_ollama('Given the following context, what is the VLLM inference server URL? Respond with ONLY the URL:\n'+result.content[0].text)
            logger.info(f"The inference service response is: \n{vllmResponse}")

            logger.info(f"The service sign-up URL is: {extract_url(signupResponse)}")
            logger.info(f"The ollama inference service URL is: {extract_url(ollamaResponse)}")
            logger.info(f"The VLLM inference service URL is: {extract_url(vllmResponse)}")
            


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
