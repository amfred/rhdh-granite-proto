import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("client")

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python", # Executable
    args=["mcp_website_fetcher_server.py"], # Optional command line arguments
    env=None # Optional environment variables
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

            # Call a tool
            result = await session.call_tool("fetch", arguments={"url": "https://example.com"})
            logger.info(f"First few characters from fetching URL: \n{result.content[0].text[:66]}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
