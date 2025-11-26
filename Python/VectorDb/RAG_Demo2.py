from dotenv import load_dotenv
load_dotenv()
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

@tool
def retrieve_context(query: str):
    """Search for info related to Techy Prakash"""
    #try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    vector_store = Chroma(collection_name="techyprakash_info", embedding_function=embeddings, persist_directory="./chroma_genai")
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    print(f"Querying retrieve_context with: {query}")
    print("--------------------------------------------------------------")
    results = retriever.invoke(query)
    print(f"Retrieved documents: {len(results)} matches found")
    for i, doc in enumerate(results):
        print(f"Document {i + 1}: {doc.page_content[:100]}...")

    print("--------------------------------------------------------------")

    content = "\n".join([doc.page_content for doc in results])
    if not content:
        print(f"No content retrieved for query: {query}")
        return f"No reviews found for '{query}'."

    print("--------------------------------------------------------------")
    print(f"Returning content: {content[:200]}...")
    return content
#   except Exception as e:
#       print(f"Error in retrieve_context: {e}")
#       return f"Error retrieving reviews for '{query}'. Please try again."

from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

agent_executor = create_react_agent(llm, [retrieve_context])

input_message = (
  "what are the key hobbies of techy prakash?"
)
for event in agent_executor.stream(
  {"messages": [{"role": "user", "content": input_message}]},
  stream_mode="values"
  ):
    event["messages"][-1].pretty_print()