def main():
        # Call langgraph pre-built agent (tools, memory and structured output)
        import LangGraphAgent_Memory
        LangGraphAgent_Memory.LangGrAgentMemFn()

        # # Call langgraph pre-built agent (tools, memory and structured output)
        # import LangGraphPreBuiltAgent
        # LangGraphPreBuiltAgent.LangGrPreBAgentFn()

        # # Call langgraph module function
        # import LangGraphMod
        # LangGraphMod.LangGrFn()

        # # Call langchain module function
        # import LangChainMod
        # LangChainMod.LangChFn()

if __name__ == "__main__":
    main()