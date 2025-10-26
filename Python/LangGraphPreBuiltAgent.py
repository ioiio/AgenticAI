def LangGrPreBAgentFn():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    from langgraph.prebuilt import create_react_agent

    def addFile(filename: str) -> None:
        """Create a new file in current directory"""
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                pass
            print(f"File '{filename}' created.")
        else:
            print(f"File '{filename}' already exists.")
        
    def addFolder(directory_name: str):
        """Create a new Directory in current directory"""
        if not os.path.exists(directory_name):
            os.mkdir(directory_name)
            print(f"Directory '{directory_name}' created.")
        else:
            print(f"Directory '{directory_name}' already exists.")

    agent = create_react_agent(
        model="groq:llama-3.3-70b-versatile", 
        tools=[addFile, addFolder], 
        prompt="You are a helpful assistant" 
    )

    # # Save graph in image
    # try:
    #     img = agent.get_graph().draw_mermaid_png()
    #     with open("graph3.png", "wb") as f:
    #         f.write(img)
    # except Exception:
    #     pass

    # Run the agents
    # prompt= "create a new file with name test.txt in the current location"
    prompt= "create a new directory with name Test in the current location and inside that create a file named example.txt"
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]}
    ) 
    print(response["messages"][-1].content)
    
    # prompt= "Who is dhoni?"
    # response = agent.invoke(
    #     {"messages": [{"role": "user", "content": prompt}]}
    # ) 
    # print(response["messages"][-1].content)

    # print("---\n")
    #  # Run the agents
    # prompt= "Who did he born?"
    # response = agent.invoke(
    #     {"messages": [{"role": "user", "content": prompt}]}
    # )   
    # print(response["messages"][-1].content)