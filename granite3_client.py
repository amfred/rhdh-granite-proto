import logging
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("###granite3-client")

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python", # Executable
    args=["granite3_model_server.py"], # Optional command line arguments
    env=None
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # The example server only supports tools:
        
            # List available prompts
            promptsList = await session.list_prompts()
            logger.info("List of prompts: \n")
            logger.info("".join(map(str, promptsList.prompts)))

            # Get a prompt
            prompt = await session.get_prompt("chat-prompt", 
                {
                "context": "The sky is red at sunset.",
                "topic": "It's sunset time. What color is the sky?"
                })
            logger.info(f"Prompt from get_prompt with messages length {len(prompt.messages)} and description {prompt.description} and Items:\n")
            for item in prompt.messages:
                logger.info(item)

            # List available tools
            toolsList = await session.list_tools()
            logger.info("List of tools: \n".join(map(str, toolsList.tools)))

            if "GRANITE_API_URL" not in os.environ:
                raise ValueError("Missing required environment variable 'GRANITE_API_URL'")
            elif "GRANITE_API_KEY" not in os.environ:
                raise ValueError("Missing required environment variable 'GRANITE_API_KEY'")
            
            url = os.environ.get('GRANITE_API_URL')
            apiKey = os.environ.get('GRANITE_API_KEY')

            # Call the chat tool
            result = await session.call_tool("chat", arguments={
                "url": os.environ.get('GRANITE_API_URL', None),
                "apiKey": os.environ.get('GRANITE_API_KEY', None),
                "model": "granite3-dense:8b",
                "prompt": prompt
                })
            logger.info(f"Response from Granite API: \n{result.content[0].text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
