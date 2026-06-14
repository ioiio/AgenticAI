def LCEL_Pipeline():
    import os
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

    # 1. Initialize the Groq LLM
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()

    # Ensure your GROQ_API_KEY environment variable is set before running
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )

    # 2. Define the Prompt Templates
    translation_prompt = ChatPromptTemplate.from_template(
        "Translate the following text into {target_language}.\n"
        "Provide only the translation without any conversational filler.\n\n"
        "Text:\n{text}"
    )

    # This prompt expects the text to ALREADY be in the target language
    summary_prompt = ChatPromptTemplate.from_template(
        "Identify and summarize the core key points from the following text. "
        "Provide the summary as a concise bulleted list in the same language as the text.\n\n"
        "Text:\n{text}"
    )

    formatting_prompt = ChatPromptTemplate.from_template(
        "# Content Processing Pipeline Report\n\n"
        "## Original Text Reference (Snippet)\n"
        "> {original_snippet}...\n\n"
        "## Translation ({target_language})\n"
        "{translated_text}\n\n"
        "## Key Summarized Points (in {target_language})\n"
        "{summary_text}"
    )

    # 3. Build the Sequential LCEL Chain
    # .assign() safely appends new data keys to the stream without losing original keys
    pipeline_chain = (
        # Step 3a: Extract a small snippet of the original English text for the report header
        RunnablePassthrough.assign(original_snippet=lambda x: x["text"][:100])
        
        # Step 3b: Run translation and add 'translated_text' to the stream
        .assign(translated_text=translation_prompt | llm | StrOutputParser())
        
        # Step 3c: Extract 'translated_text', pass it to the summarizer, and add 'summary_text' to the stream
        .assign(
            summary_text=(
                lambda x: {"text": x["translated_text"]}
            ) 
            | summary_prompt 
            | llm 
            | StrOutputParser()
        )
        
        # Step 3d: Feed the full dictionary into the formatting template and output the final string
        | formatting_prompt 
        | llm 
        | StrOutputParser()
    )

    # 4. Execute the Pipeline
   
    # Long-form English sample text
    sample_text = (
        "Artificial Intelligence is transforming industries at an unprecedented pace. "
        "Healthcare systems are utilizing machine learning models to detect anomalies in medical imaging "
        "with higher accuracy than traditional methods. Meanwhile, the financial sector leverages "
        "predictive algorithms to detect fraudulent transactions in real-time, saving billions annually. "
        "However, this rapid adoption raises critical ethical questions regarding data privacy, algorithmic "
        "bias, and the displacement of human labor. Mitigating these risks requires robust regulatory frameworks "
        "and collaborative efforts between tech developers and policymakers."
    )

    inputs = {
        "text": sample_text,
        "target_language": "Spanish"
    }

    print("Running sequential pipeline via Groq... Please wait...\n")
    try:
        markdown_output = pipeline_chain.invoke(inputs)
        
        print("--- FINAL MARKDOWN OUTPUT ---\n")
        print(markdown_output)
        
        # Optional: Save the cleanly formatted result to a file
        with open("pipeline_output.md", "w", encoding="utf-8") as f:
            f.write(markdown_output)
        print("\n[Success] Output saved cleanly to 'pipeline_output.md'")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check that your GROQ_API_KEY environment variable is set correctly.")