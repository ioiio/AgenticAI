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
    # Ensure GEMINI_API_KEY is set in your environment variables
    client = genai.Client()
    EMBED_MODEL = "gemini-embedding-2"
    LLM_MODEL = "gemini-2.5-flash"

    # =====================================================================
    # 1. INGESTION PHASE: Document Parsing & Sliding Window Chunking
    # =====================================================================
    def parse_and_chunk_file(file_path: str, chunk_size: int = 150, chunk_overlap: int = 30):
        """
        Reads a local documentation file and chops it using a sliding window strategy.
        """
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
        for i, chunk in enumerate(chunks):
            print(f"    Chunk {i}: '{chunk[:60]}...'")
        return chunks

    # =====================================================================
    # 2. EMBEDDING PHASE: Generating Vector Numbers via Google Engine
    # =====================================================================
    def generate_google_embeddings(text_chunks: list):
        """
        Pushes text chunks downstream to Google's embedding engine to get math coordinates.
        Guarantees a 1:1 vector match for every individual text chunk.
        """
        print(f"\n--- PHASE 2: EMBEDDING GENERATION ---")
        print(f"[*] Pushing chunks downstream to Google API ({EMBED_MODEL})...")
        
        embeddings = []
        try:
            # Loop over each individual chunk to guarantee a dedicated vector result
            for i, chunk in enumerate(text_chunks):
                response = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=chunk
                )
                # Pull the float array values for this specific chunk
                vector = response.embeddings[0].values
                embeddings.append(vector)
                print(f"    [->] Embedded Chunk {i} successfully (Dimensions: {len(vector)})")
                
            print(f"[+] Successfully generated {len(embeddings)} dense vectors.")
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            print(f"[!] Error generating embeddings via Google: {e}")
            return np.array([], dtype=np.float32)

    # =====================================================================
    # 3. INDEXING PHASE: Populating Vector Stores (ChromaDB & FAISS)
    # =====================================================================
    def index_in_chromadb(chunks: list, embeddings: np.ndarray):
        """
        Indexes structural text data and pre-computed vectors into ChromaDB.
        """
        import chromadb
        print(f"\n--- PHASE 3A: CHROMADB INDEXING ---")
        print("[*] Initializing local ChromaDB vector store...")
        
        chroma_client = chromadb.Client() 
        collection = chroma_client.get_or_create_collection(name="student_rag_demo")
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": "local_documentation", "chunk_index": i} for i in range(len(chunks))]
        
        # Convert numpy matrix back to standard python list for Chroma compatibility
        vector_list = embeddings.tolist()
        
        collection.add(
            embeddings=vector_list,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[+] ChromaDB: Successfully indexed {collection.count()} structural entries.")
        return collection

    def index_in_faiss(embeddings: np.ndarray):
        """
        Indexes raw vector matrices directly into a flat FAISS index layout.
        """
        import faiss
        print(f"\n--- PHASE 3B: FAISS INDEXING ---")
        print("[*] Initializing memory-optimized FAISS Index...")
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension) # Exact L2 distance search matrix
        index.add(embeddings)
        
        print(f"[+] FAISS: Successfully indexed {index.ntotal} raw vector footprints.")
        return index

    # =====================================================================
    # 4. EXECUTION PHASE: The RAG Query Loop (Retrieval & Generation)
    # =====================================================================
    def execute_rag_query(student_question: str, text_chunks: list, embeddings_matrix: np.ndarray):
        """
        Takes a question, finds the best contextual chunk, and augments the LLM response.
        """
        print(f"\n==============================================")
        print(f"=== RUNNING THE LIVE RAG LOOP ===")
        print(f"==============================================")
        print(f"[Student Question]: '{student_question}'")
        
        # --- STEP 1: EMBED THE USER QUESTION ---
        print("\n[*] Step 1: Converting student query into vector coordinates...")
        query_response = client.models.embed_content(model=EMBED_MODEL, contents=student_question)
        query_vector = np.array(query_response.embeddings[0].values, dtype=np.float32)
        
        # --- STEP 2: SIMULATE THE DB LOOKUP (VECTOR SEARCH) ---
        print("[*] Step 2: Calculating vector distances (Cosine Similarity)...")
        best_chunk = None
        highest_similarity = -1.0
        
        for i, chunk in enumerate(text_chunks):
            chunk_vector = embeddings_matrix[i]
            
            # Mathematical Dot Product calculation to determine directional similarity
            similarity = np.dot(query_vector, chunk_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector))
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_chunk = chunk
                
        print(f"[+] Search Match Found (Similarity Score: {highest_similarity:.4f}):")
        print(f"    Selected Context: \"{best_chunk}\"")

        # --- STEP 3: CONSTRUCT GROUNDED PROMPT ---
        print("\n[*] Step 3: Wrapping context inside a structured prompt...")
        grounded_prompt = f"""
        You are an AI teaching assistant. Answer the student's question using ONLY the provided reference context.
        If the context doesn't contain the answer, say "I don't know based on the documentation." Do not make things up.
        
        Reference Context:
        {best_chunk}
        
        Student Question:
        {student_question}
        
        Answer:
        """
        
        # --- STEP 4: GENERATION ---
        print("[*] Step 4: Dispatching augmented data to Gemini LLM engine...")
        ai_response = client.models.generate_content(
            model=LLM_MODEL,
            contents=grounded_prompt,
        )
        
        print("\n=== FINAL GROUNDED ANSWER ===")
        print(ai_response.text.strip())
        print("==============================================\n")

    # =====================================================================
    # MAIN SYSTEM INVOCATION
    # =====================================================================

    # Create temporary localized documentation file
    sample_file = "localized_documentation.txt"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(
            "Retrieval-Augmented Generation (RAG) architectural mechanics depend significantly on chunking structures.\n"
            "Sliding-window approaches preserve localized contextual integrity between text chunk fragments.\n"
            "Dense vector embeddings capture latent semantics across multi-dimensional spaces.\n"
            "Indexing components like HNSW or IVF graphs inside vector databases minimize approximate nearest neighbor query latencies."
        )

    try:
        # Run Ingestion Mechanics Pipeline
        chunks = parse_and_chunk_file(sample_file, chunk_size=120, chunk_overlap=30)
        embeddings = generate_google_embeddings(chunks)
        
        if embeddings.size > 0:
            # Index into both engines to confirm database readiness
            chroma_collection = index_in_chromadb(chunks, embeddings)
            faiss_index = index_in_faiss(embeddings)
            
            # Fire up the live interactive student query loop
            test_question = "How do we reduce lookup latencies inside a vector database?"
            execute_rag_query(test_question, chunks, embeddings)
            
    finally:
        # Automated Clean-up
        if os.path.exists(sample_file):
            os.remove(sample_file)