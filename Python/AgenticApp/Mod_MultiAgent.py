def MultiAgentFn():
    from dotenv import load_dotenv
    load_dotenv()
    import asyncio
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent
    import os
    from langchain_google_genai import ChatGoogleGenerativeAI

    async def run_agent():
        client = MultiServerMCPClient(     
            {
                "tavily-remote": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-remote",
                        "https://mcp.tavily.com/mcp/?tavilyApiKey=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"
                    ],
                    "transport": "stdio"
                },
            }  
        )
        
        tools = await client.get_tools()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0 # Recommended for agents to ensure deterministic decisions
        )
        #agent = create_react_agent("groq:llama-3.3-70b-versatile", tools)
        agent = create_react_agent(llm, tools)       
        prompt="Who is Prakash Tripathi, he lives in Hyderabad, his blog is techyprakash.com"
        # The agent expects a list of messages, so we wrap the prompt in a HumanMessage.
        from langchain_core.messages import HumanMessage
        response = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        print(response["messages"][-1].content)

    asyncio.run(run_agent())



