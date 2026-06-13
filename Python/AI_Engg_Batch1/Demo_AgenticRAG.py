def AgenticRAG():
    import asyncio
    from mcp.server.fastmcp import FastMCP
    from pydantic import BaseModel, Field

    # ==============================================================================
    # 1. THE LIVE CONTEXT MCP SERVER (The Source of Live Context)
    # ==============================================================================
    # FastMCP automatically generates schemas from python docstrings & type hints.
    mcp = FastMCP("LiveContextServer")

    # In-memory mock database representing changing live data (impossible to embed statically)
    MOCK_LIVE_INVENTORIES = {
        "neon-hoodie": {"stock": 14, "location": "Warehouse A", "price": 45.00, "status": "In Stock"},
        "mcp-stickers": {"stock": 0, "location": "Warehouse B", "price": 2.50, "status": "Backordered (Ships in 2 weeks)"},
        "cyber-glasses": {"stock": 8, "location": "Warehouse A", "price": 89.99, "status": "In Stock"},
    }

    @mcp.tool()
    async def get_realtime_inventory(product_id: str) -> str:
        """
        Fetches the precise, real-time stock levels, warehouse location, and status of a product.
        Use this when user asks about item availability.
        """
        prod = MOCK_LIVE_INVENTORIES.get(product_id.lower())
        if not prod:
            return f"Error: Product ID '{product_id}' not found in live inventory."
        
        return (
            f"Product ID: {product_id}\n"
            f"Live Stock Level: {prod['stock']} units\n"
            f"Location: {prod['location']}\n"
            f"Price: ${prod['price']}\n"
            f"Current Status: {prod['status']}"
        )

    @mcp.tool()
    async def search_live_helpdesk_tickets(query: str) -> str:
        """
        Scans live, unresolved customer helpdesk tickets.
        Use this to retrieve real-time customer context before answering inquiries.
        """
        # Mimics dynamic API searching
        return (
            f"--- Live Helpdesk Search Results for '{query}' ---\n"
            "Ticket #48201 (Open)\n"
            "User: user_402@example.com\n"
            "Title: Delayed delivery for 'neon-hoodie'\n"
            "Notes: Customer paid for express shipping but tracking states delayed in transit."
        )


    # ==============================================================================
    # 2. RUNNING THE SYSTEM & THE AGENT CLIENT (How they connect)
    # ==============================================================================
    # This mock agent client demonstrates how an LLM dynamically calls the MCP tools on stage.
    async def run_live_agent_demo(user_prompt: str):
        print("=" * 80)
        print(f"User Query: '{user_prompt}'")
        print("=" * 80)
        
        # In a real setup, the agent parses the tool definitions provided by the MCP Server.
        # Let's inspect the tools exposed by the MCP server live:
        tools_list = mcp.list_tools()
        print("\n[Client Discovery] MCP Server detected. Available Tools:")
        for tool in tools_list:
            print(f"  - Tool Name: {tool.name}")
            print(f"    Description: {tool.description.strip()}")
        
        # Mock LLM reasoning loop:
        print("\n[Agent Decisioning] Analyzing prompt to select optimal tool...")
        
        # Simulating LLM routing logic
        if "hoodie" in user_prompt or "stock" in user_prompt:
            selected_tool = "get_realtime_inventory"
            tool_args = {"product_id": "neon-hoodie"}
        elif "ticket" in user_prompt or "support" in user_prompt:
            selected_tool = "search_live_helpdesk_tickets"
            tool_args = {"query": "neon-hoodie"}
        else:
            print("[Agent Decisioning] No specialized real-time tool needed. Answering via general knowledge.")
            return
        
        print(f"[Agent Decisioning] Selected Live Tool: '{selected_tool}' with args: {tool_args}")
        
        # Execute the selected MCP tool dynamically
        print("\n[MCP Execution] Calling tool inside the server session...")
        if selected_tool == "get_realtime_inventory":
            result = await get_realtime_inventory(**tool_args)
        else:
            result = await search_live_helpdesk_tickets(**tool_args)
            
        print(f"\n[MCP Context Result]:\n{result}")
        
        # Finally, simulate passing this context back into the generation model
        print("\n" + "-" * 40)
        print("[Agent Synthesis] Final Answer generated using Live Context:")
        print(f"\"Hey there! I've checked our live warehouse database. The neon-hoodie currently has {MOCK_LIVE_INVENTORIES['neon-hoodie']['stock']} units available at {MOCK_LIVE_INVENTORIES['neon-hoodie']['location']}. However, I did spot your open Ticket #48201 regarding a shipping delay. Let me expedite that for you immediately!\"")
        print("-" * 40)