from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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
            # print("Prompts: ", prompts)

            # Get a prompt
            # prompt = await session.get_prompt("example-prompt", arguments={"arg1": "value"})
            # print("Prompt: ", prompt)

            # List available resources
            #resources = await session.list_resources()
            #print("Resources: ", resources)

            # List available tools
            tools = await session.list_tools()
            print("Tools: ", tools)

            # Read a resource
            #resource = await session.read_resource("file://some/path")
            #print("Resource: ", resource)

            # Call a tool
            result = await session.call_tool("fetch", arguments={"url": "https://example.com"})
            print("Tool result: ", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
