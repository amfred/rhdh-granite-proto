import anyio
import click
import httpx
import logging
import mcp.types as types
from mcp.server import Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rhdh-catalog-server")

BASE_URI            = "/api/catalog"
LOCATION_URI        = "/locations"
ENTITIES_URI        = "/entities"
COMPONENT_URI       = "/entities/by-name/component/%s/%s"
RESOURCE_URI        = "/entities/by-name/resource/%s/%s"
API_URI             = "/entities/by-name/api/default/ollama-service-api"
QUERY_URI           = "/entities/by-query"
ENTITY_FACETS_URI   = "/entity-facets"
DEFAULT_NS          = "default"

# This is a method whose purpose is to make sure HTTP in general is working
async def fetch_website(
    url: str,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]

# This is a utility method to call Backstage Software Catalog APIs
async def get_from_backstage_catalog(
    url: str, path: str, apiKey: str
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)",
        "Authorization": f"Bearer {apiKey}"
    }
    fullPath = url + path
    #logger.info(f"The fullPath is: {fullPath}")
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        response = await client.get(fullPath)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]
    
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
    app = Server("rhdh-api")
    logger.info(f"Starting up rhdh-api server using transport: {transport}")

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # All of the tools require the url
        if "url" not in arguments:
            raise ValueError("Missing required argument 'url'")
        elif (arguments["url"] == None or arguments["url"] == ""):
            raise ValueError("Required argument 'url' must not be blank")

        if name == "fetch":
            return await fetch_website(arguments["url"])
        
        # The remaining tools also require the apiKey
        if "apiKey" not in arguments:
            raise ValueError("Missing required argument 'apiKey'")
        elif (arguments["apiKey"] == None or arguments["apiKey"] == ""):
            raise ValueError("Required argument 'apiKey' must not be blank")

        elif name == "get_tags":
            path = BASE_URI + ENTITY_FACETS_URI + "?facet=metadata.tags&filter=kind%3Dresource"
            return await get_from_backstage_catalog(arguments["url"], path, arguments["apiKey"])
        elif name == "get_apis":
            path = BASE_URI + QUERY_URI + "?filter=kind=api&fields=kind,metadata.namespace,metadata.name,metadata.title,metadata.description,metadata.tags,metadata.links";
            return await get_from_backstage_catalog(arguments["url"], path, arguments["apiKey"])
        elif name == "get_inference_servers":
            path = BASE_URI + QUERY_URI + "?filter=kind=component,spec.type=model-server&fields=kind,metadata.namespace,metadata.name,metadata.title,metadata.description,metadata.tags,metadata.links";
            return await get_from_backstage_catalog(arguments["url"], path, arguments["apiKey"])
        else:
            raise ValueError(f'Unknown tool: {name}')

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="fetch",
                description="Fetches a webpage and returns its content",
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_tags",
                description="Gets metadata about the tags in Developer Hub: the name of each tag (value), and the number of times each tag is used (count).",
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
                        }
                    },
                },
            ),
            types.Tool(
                name="get_apis",
                description="Gets a list of APIs registered in Developer Hub",
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
                        }
                    },
                },
            ),
            types.Tool(
                name="get_inference_servers",
                description="Gets a list of model inference servers registered in Developer Hub",
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
                        }
                    },
                },
            )
        ]

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
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
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
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
