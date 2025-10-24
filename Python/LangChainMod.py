def LangChFn():
    from dotenv import load_dotenv
    from langchain.chat_models import init_chat_model

    load_dotenv()

    model = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")
    # model = init_chat_model("gpt-4o-mini", model_provider="openai")
    response = model.invoke("who is Osho?")
    print(response.content)