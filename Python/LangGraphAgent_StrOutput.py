def LangGrAgentStrOpFn():
    from dotenv import load_dotenv
    load_dotenv()
    from langgraph.prebuilt import create_react_agent
    from pydantic import BaseModel

    class MailResponse(BaseModel):
        # subject: str
        # body: str
        flights  : str
        hotels  : str
        placestovisit : str 

    agent = create_react_agent(
        model="groq:llama-3.3-70b-versatile", 
        tools=[], 
        response_format=MailResponse
    )

    # Run the agents
    # prompt= "write a mail applying leave for travel"
    prompt= "write a 5 days travel itinerary for Bali with veg food options starting from Hyderabad"
    response = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]}
    )
    print(response["messages"][-1].content)
    # print(response)
    print("------------------------------")
    print(response["structured_response"])
    print("------------------------------")
    print(response["structured_response"].flights)
    print("------------------------------")
    print(response["structured_response"].hotels)
    print("------------------------------")
    print(response["structured_response"].placestovisit)



