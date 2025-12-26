def OllamaFn():
    from dotenv import load_dotenv
    load_dotenv()
    import asyncio
    from langgraph.prebuilt import create_react_agent

    async def run_agent():
        agent = create_react_agent("ollama:llama3.2:latest", {})
        response = await agent.ainvoke({"messages": "Who is Osho"})
        print(response["messages"][-1].content)

    asyncio.run(run_agent())