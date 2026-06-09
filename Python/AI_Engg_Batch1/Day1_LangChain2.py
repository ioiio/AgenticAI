def LangChFn():
    from dotenv import load_dotenv
    #from langchain.chat_models import init_chat_model
    from langchain.agents import create_agent

    load_dotenv()

    agent = create_agent(
        model="groq:llama-3.3-70b-versatile",
        tools=[]
    )

    # Run the agents
    response = agent.invoke(
        {"messages": [{"role": "user", 
        "content": "where is Aparna Cyber Life?"}]}
        #"content": "where is Aparna Cyber Life? What's the key highlights?"}]}
    )
    print(response["messages"][-1].content)