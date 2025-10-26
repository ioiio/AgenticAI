def main():
        # Call langgraph pre-built agent with structured output
        import LangGraphAgent_StrOutput
        LangGraphAgent_StrOutput.LangGrAgentStrOpFn()

        # # Call langgraph pre-built agent with memory
        # import LangGraphAgent_Memory
        # LangGraphAgent_Memory.LangGrAgentMemFn()

        # # Call langgraph pre-built agent with tools
        # import LangGraphPreBuiltAgent
        # LangGraphPreBuiltAgent.LangGrPreBAgentFn()

        # # Call langgraph module tools function
        # import LangGraphMod
        # LangGraphMod.LangGrFn()

        # # Call langchain module function
        # import LangChainMod
        # LangChainMod.LangChFn()

if __name__ == "__main__":
    main()