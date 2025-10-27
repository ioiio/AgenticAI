def LangGrMCPFn():
    from dotenv import load_dotenv
    load_dotenv()
    import asyncio
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent
    import os

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    async def run_agent():
        client = MultiServerMCPClient(
            {
                "github": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-github"
                    ],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
                    },
                    "transport": "stdio"
                }
            }
        )
        tools = await client.get_tools()
        agent = create_react_agent("groq:llama-3.3-70b-versatile", tools)
        #prompt="What are the files present in repository prakash-manit/AgenticAI?"
        prompt="create a new file named BinarySearch.py in repository prakash-manit/Python and add binary search algorithm code in it."
        response = await agent.ainvoke({"messages": prompt})
        print(response["messages"][-1].content)

    asyncio.run(run_agent())



