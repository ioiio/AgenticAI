def LangGrPreBAgentFn():
    from dotenv import load_dotenv
    load_dotenv()

    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model="groq:llama-3.3-70b-versatile", 
        tools=[], 
        prompt="You are a helpful assistant" 
    )

    # Save graph in image
    try:
        img = agent.get_graph().draw_mermaid_png()
        with open("graph2.png", "wb") as f:
            f.write(img)
    except Exception:
        pass

    # Run the agents
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "what are large language models"}]}
    )
    print(response)