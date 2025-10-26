def LangGrAgentMemFn():
    from dotenv import load_dotenv
    load_dotenv()
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    agent = create_react_agent(
        model="groq:llama-3.3-70b-versatile", 
        tools=[], 
        checkpointer=checkpointer
    )

    config = {"configurable": {"thread_id":"1"}} # Thread id is like session or conversation id

    prompt= "Who is dhoni?"
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]}, config=config # Use same thread_id to maintain memory/context
    ) 
    print(response["messages"][-1].content)

    print("---\n")
     # Run the agents
    prompt= "When was he born?"
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]}, config=config # Use same thread_id to maintain memory/context of previous interaction
    )   
    print(response["messages"][-1].content)