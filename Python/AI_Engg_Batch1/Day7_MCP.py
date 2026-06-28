def MCP_Fn():   
    import os
    import json
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from groq import Groq

    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()

    # 1. Initialize Clients & FastAPIs
    app = FastAPI(title="Simplified MCP Gateway")

    # Ensure you run: export GROQ_API_KEY="your-key"
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # Mock Enterprise Data Silo
    # This is a mock database. In a real company, this would be Jira, Salesforce, or a SQL database.
    # Right now, it’s just a isolated Python dictionary holding customer support tickets that the AI cannot see by default.
    TICKET_DB = {
        "TICK-101": {"status": "Open", "priority": "High", "issue": "Database timeout in production region east."},
        "TICK-102": {"status": "Closed", "priority": "Low", "issue": "Typo on the landing page footer."},
        "TICK-103": {"status": "In Progress", "priority": "Medium", "issue": "API endpoint /v2/users returning 500 error."},
    }

    # Define the incoming payload schema
    class QueryRequest(BaseModel):
        prompt: str

    # 2. Define our MCP Tool Schema (OpenAI/Groq Format), Teaching the AI what it can do
    # This is the schema that tells the LLM what tools are available and how to call them.
    MCP_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_ticket_details",
                "description": "Exposes internal database state for a specific ticket ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string", "description": "The unique ticket reference ID (e.g., TICK-101)"}
                    },
                    "required": ["ticket_id"]
                }
            }
        }
    ]

    # 3. The Local Tool Execution Layer (The "Server" code)
    def execute_mcp_tool(name: str, arguments: dict) -> str:
        if name == "get_ticket_details":
            ticket_id = arguments.get("ticket_id")
            ticket = TICKET_DB.get(ticket_id, {"error": f"Ticket {ticket_id} not found"})
            return json.dumps(ticket)
        raise ValueError(f"Tool {name} not supported.")


    # 4. The Production Endpoint
    @app.post("/chat")
    async def chat_pipeline(request: QueryRequest):
        # Initialize message history
        messages = [
            {"role": "system", "content": "You are a production support engineer with access to system tools."},
            {"role": "user", "content": request.prompt}
        ]

        try:
            # Step 1: Query Groq to see if a tool/data access is needed
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=MCP_TOOLS,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Step 2: If the model asks for data, fetch it and call Groq again
            if tool_calls:
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Fetch data directly from our native Python execution layer
                    mcp_data_context = execute_mcp_tool(function_name, function_args)
                    
                    # Append tool results back into context history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": mcp_data_context
                    })
                
                # Step 3: Get final synthesized answer from Groq using the new data
                final_response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                return {"response": final_response.choices[0].message.content, "tool_used": True}
            
            return {"response": response_message.content, "tool_used": False}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)