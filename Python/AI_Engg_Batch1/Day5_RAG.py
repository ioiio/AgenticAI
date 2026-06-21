def RAG_Pipeline():
    import os
    import uuid
    import numpy as np
    from google import genai
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()

    # =====================================================================
    # 0. GLOBAL SETUP & CLIENT INITIALIZATION
    # =====================================================================
    client = genai.Client()
    EMBED_MODEL = "gemini-embedding-2"
    LLM_MODEL = "gemini-2.5-flash"

    # =====================================================================
    # 1. INGESTION PHASE: Document Parsing & Sliding Window Chunking
    # =====================================================================
    def parse_and_chunk_file(file_path: str, chunk_size: int = 150, chunk_overlap: int = 30):
        print(f"\n--- PHASE 1: DOCUMENT PROCESSING ---")
        print(f"[*] Reading localized raw documentation: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        # Implementing sliding-window mechanics via LangChain's recursive splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_text(raw_text)
        print(f"[+] Successfully split text into {len(chunks)} overlapping chunks.")
        return chunks

    # =====================================================================
    # 2. EMBEDDING PHASE: Generating Vector Numbers
    # =====================================================================
    def generate_google_embeddings(text_chunks: list):
        print(f"\n--- PHASE 2: EMBEDDING GENERATION ---")
        print(f"[*] Pushing chunks downstream to Google API ({EMBED_MODEL})...")
        
        embeddings = []
        try:
            # Loop over each chunk to guarantee a dedicated vector result
            for i, chunk in enumerate(text_chunks):
                response = client.models.embed_content(model=EMBED_MODEL, contents=chunk)
                vector = response.embeddings[0].values
                embeddings.append(vector)
                print(f"    [->] Embedded Chunk {i} successfully.")
                
            print(f"[+] Successfully generated {len(embeddings)} dense vectors.")
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            print(f"[!] Error generating embeddings: {e}")
            return np.array([], dtype=np.float32)

    # =====================================================================
    # 3. INDEXING PHASE: Populating ChromaDB
    # =====================================================================
    def index_in_chromadb(chunks: list, embeddings: np.ndarray):
        import chromadb
        print(f"\n--- PHASE 3: CHROMADB INDEXING ---")
        print("[*] Initializing local ChromaDB database...")
        
        # Creates an in-memory database client
        chroma_client = chromadb.Client() 
        collection = chroma_client.get_or_create_collection(name="student_rag_demo")
        
        # Generate structured IDs and simple metadata for accountability
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": "local_documentation", "chunk_index": i} for i in range(len(chunks))]
        
        # Store documents alongside their pre-computed vectors
        collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[+] ChromaDB: Successfully indexed {collection.count()} text blocks and vectors.")
        return collection

    # =====================================================================
    # 4. EXECUTION PHASE: Native ChromaDB Retrieval & LLM Generation
    # =====================================================================
    def run_production_rag(student_question: str, chroma_collection):
        print(f"\n==============================================")
        print(f"=== RUNNING CHROMADB VECTOR RETRIEVAL ===")
        print(f"==============================================")
        print(f"[Student Question]: '{student_question}'")
        
        # Step 1: Turn the query string into coordinates
        print("\n[*] Step 1: Converting query into vector coordinates...")
        query_response = client.models.embed_content(model=EMBED_MODEL, contents=student_question)
        query_vector = query_response.embeddings[0].values
        
        # Step 2: Query ChromaDB natively (It handles calculations & document lookup)
        print("[*] Step 2: Querying ChromaDB collection index...")
        chroma_results = chroma_collection.query(
            query_embeddings=[query_vector],
            n_results=1  # Pulls the single top closest match
        )
        
        # Unpack the raw text directly from the database response object
        retrieved_context = chroma_results['documents'][0][0]
        print(f"[+] Database Found Context: \"{retrieved_context}\"")
        
        # Step 3: Construct the context-shield prompt
        print("\n[*] Step 3: Grounding prompt with database text...")
        grounded_prompt = f"""
        Answer the student's question using ONLY the provided reference context.
        If the context doesn't contain the answer, say "I don't know based on the documentation."
        
        Context:
        {retrieved_context}
        
        Question:
        {student_question}
        """
        
        # Step 4: Generation via Gemini
        print("[*] Step 4: Dispatching to Gemini LLM engine...")
        ai_response = client.models.generate_content(model=LLM_MODEL, contents=grounded_prompt)
        
        print("\n=== FINAL GROUNDED ANSWER ===")
        print(ai_response.text.strip())
        print("==============================================\n")

    # =====================================================================
    # SYSTEM MAIN INVOCATION
    # =====================================================================
    sample_file = "localized_documentation.txt"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(
            "Retrieval-Augmented Generation (RAG) architectural mechanics depend significantly on chunking structures.\n"
            "Sliding-window approaches preserve localized contextual integrity between text chunk fragments.\n"
            "Dense vector embeddings capture latent semantics across multi-dimensional spaces.\n"
            "Indexing components like HNSW or IVF graphs inside vector databases minimize approximate nearest neighbor query latencies."
        )

    try:
        # 1. Parse documentation using sliding window
        chunks = parse_and_chunk_file(sample_file, chunk_size=120, chunk_overlap=30)
        
        # 2. Extract numeric embeddings
        embeddings = generate_google_embeddings(chunks)
        
        if embeddings.size > 0:
            # 3. Index everything inside ChromaDB
            chroma_collection = index_in_chromadb(chunks, embeddings)
            
            # 4. Search and Generate
            test_question = "How do we reduce lookup latencies inside a vector database?"
            run_production_rag(test_question, chroma_collection)
            
    finally:
        # Clean up local environment mock file
        if os.path.exists(sample_file):
            os.remove(sample_file)