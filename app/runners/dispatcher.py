import asyncio

from app.dispatcher.bootstrap import create_dispatcher
from app.dispatcher.models.tool_request import ToolRequest


async def main():

    dispatcher = create_dispatcher()

    request = ToolRequest(
        tool="mock",
        payload={
            "message": "hello jarbas"
        }
    )

    response = await dispatcher.dispatch(request)

    print(response)


if __name__ == "__main__":
    asyncio.run(main())