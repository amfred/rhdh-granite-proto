import anyio
import click
import httpx
import logging
import json
import mcp.types as types
from mcp.server import Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("granite3-model-server")

CHAT_URI = "/v1/chat/completions"

server = Server("granite3-model")

# Utility method to convert a PromptMessage into a json array in this format:
#{
#    "model": "ibm-granite-8b-code-instruct",
#    "messages": [
#      {
#        "role": "system",
#        "content": "You are a helpful assistant."
#      },
#      {
#        "role": "user",
#        "content": "What is the plot of the movie Inception?"
#      }
#    ]
#  }'
def create_request_data(model: str, prompt: list[types.PromptMessage]) -> dict:

    request_data = {
        "model": model,
        "messages" : [
          {
            "role": "system",
            "content": "You are a helpful assistant."
          },
        ]
    }

    logger.info("Converting messages into request data, starting with this request data: \n"
                +json.dumps(request_data))
    
    logger.info("The prompt to convert is: \n")

    for message in prompt["messages"]:
        logger.info("The current message is: ".join(map(str, message)))
        if message.role == "user":
            request_data["messages"].append({"role": "user", "content": message.content.text})
    
    logger.info("Finalrequest data: \n"
                +json.dumps(request_data))

    return request_data

# Utility method to chat with the model
async def chat_with_granite3_model(
    path: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    
    url = arguments["url"]
    prompt = arguments["prompt"]
    apiKey = arguments["apiKey"]

    logger.info(f"Preparing to chat_with_granite3_model with messages length {len(prompt.messages)} and Items:\n")
    for item in prompt.messages:
        logger.info(item)
    
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)",
        "Authorization": f"Bearer {apiKey}",
        "Content-Type": "application/json" 
    }

    fullPath = url + path
    logger.info(f"The fullPath is: {fullPath}")
    json = create_request_data("granite3-dense:8b", prompt)
    logger.info("The request data is: ".join(map(str, json)))
    async with httpx.AsyncClient(follow_redirects=True, headers=headers, verify=False) as client:
        response = await client.post(url=fullPath, data=json)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]

# Utility method to create the messages for the prompt
def create_messages(
    topic: str, context: str | None = None
) -> list[types.PromptMessage]:
    messages = []

    # Add context if provided
    if context:
        messages.append(
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text", text=f"Here is some relevant context: {context}"
                ),
            )
        )
    # Add the actual chat message
    messages.append(
        types.PromptMessage(
            role="user", 
            content=types.TextContent(type="text", text=topic)
        )
    )
    logger.info("Returning messages: ".join(map(str, messages)))
    return messages

# Add prompt capabilities
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="chat-prompt",
            description="A simple prompt with optional context and chat message",
            arguments=[
                types.PromptArgument(
                    name="context",
                    description="Additional context to consider",
                    required=False,
                ),
                types.PromptArgument(
                    name="topic",
                    description="The chat message to send to the model",
                    required=True
                )
            ]
        ),
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str,
    arguments: dict[str, str] | None
) -> types.GetPromptResult:
    if name != "chat-prompt":
        raise ValueError(f"Unknown prompt: {name}")

    if arguments is None:
        arguments = {}

    return types.GetPromptResult(
        messages=create_messages(
            context=arguments.get("context"), topic=arguments.get("topic")
        ),
        description="A simple prompt with optional context and chat message"
    )

# Add tool capabilities
@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
    # All of the tools require the url
    if "url" not in arguments:
        raise ValueError("Missing required argument 'url'")
    elif (arguments["url"] == None or arguments["url"] == ""):
        raise ValueError("Required argument 'url' must not be blank")
       
    # The tools also require the apiKey
    if "apiKey" not in arguments:
        raise ValueError("Missing required argument 'apiKey'")
    elif (arguments["apiKey"] == None or arguments["apiKey"] == ""):
        raise ValueError("Required argument 'apiKey' must not be blank")
    
    elif name == "chat":
        path = CHAT_URI
        # The chat tool requires a prompt

        if "prompt" not in arguments:
            raise ValueError("Missing required argument 'prompt'")
        
        logger.info("Calling the chat_with_granite3_model utility method")
        return await chat_with_granite3_model(path, arguments)
    else:
        raise ValueError(f'Unknown tool: {name}')

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="chat",
            description="Sends a chat request to the model",
            inputSchema={
                "type": "object",
                "required": ["url","apiKey"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch",
                    },
                    "apiKey": {
                        "type": "string",
                        "description": "API key to use in the Authorization: Bearer header",
                    },
                    "model": {
                        "type": "string",
                        "description": "The name of the model, for example granite3-dense:8b",
                    }
                },
            },
        )
    ]
         
@click.group()
def cli():
    pass

@cli.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    logger.info(f"Starting up granite3-model server using transport: {transport}")

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        logger.info(f"Starting up sse server on port: {port}")

        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        async def handle_messages(request):
            await sse.handle_post_message(request.scope, request.receive, request._send)

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server
        logger.info("Starting up stdio server")

        async def arun():
            async with stdio_server() as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
