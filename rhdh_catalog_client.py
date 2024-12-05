import logging
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rhdh-catalog-client")

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python", # Executable
    args=["rhdh_catalog_server.py"], # Optional command line arguments
    env=None
)

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

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
