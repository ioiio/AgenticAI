def AdvRAGPipeline():
    import os
    import asyncio
    import numpy as np
    from typing import List, Dict, Any, Optional
    from pydantic import BaseModel, Field
    from google import genai
    from google.genai import types

    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the standard Gemini Client
    # It automatically picks up GEMINI_API_KEY from the environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL ERROR: GEMINI_API_KEY environment variable is not set.")

    client = genai.Client()

    # ----------------------------------------------------
    # 1. MOCK DATA & SIMULATED VECTOR MECHANICS
    # ----------------------------------------------------
    HR_KNOWLEDGE_BASE = [
        {
            "id": "chunk_01",
            "source": "US_Benefits_2026.pdf",
            "category": "Benefits",
            "region": "US",
            "text": "Full-time employees in the United States receive up to 4 weeks (20 business days) of paid time off (PTO) annually. Accrual occurs monthly.",
            "embedding": [0.12, 0.85, -0.23, 0.05]
        },
        {
            "id": "chunk_02",
            "source": "Global_Leave_Policy.pdf",
            "category": "Benefits",
            "region": "UK",
            "text": "UK employees are entitled to 28 days of statutory annual leave, inclusive of bank holidays. Request window opens in January.",
            "embedding": [0.10, 0.79, -0.11, 0.45]
        },
        {
            "id": "chunk_03",
            "source": "Information_Security_v4.pdf",
            "category": "Compliance",
            "region": "Global",
            "text": "Multi-factor authentication (MFA) is mandatory for all internal HR portal accesses. Password resets are enforced every 90 days.",
            "embedding": [-0.67, 0.11, 0.92, -0.14]
        },
        {
            "id": "chunk_04",
            "source": "US_Benefits_2026.pdf",
            "category": "Benefits",
            "region": "US",
            "text": "Health savings account (HSA) contributions for US employees are matched by the enterprise up to $1,500 annually for family plans.",
            "embedding": [0.15, 0.88, -0.30, 0.02]
        }
    ]

    def mock_query_embedding(query: str) -> List[float]:
        q = query.lower()
        if "vacation" in q or "pto" in q or "leave" in q:
            if "uk" in q: return [0.11, 0.80, -0.13, 0.40]
            return [0.13, 0.84, -0.21, 0.06]
        elif "password" in q or "security" in q or "mfa" in q:
            return [-0.62, 0.15, 0.89, -0.10]
        return [0.0, 0.0, 0.0, 0.0]

    def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
        arr1, arr2 = np.array(v1), np.array(v2)
        return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2)))

    # ----------------------------------------------------
    # 2. STRUCTURED Pydantic SCHEMAS FOR OBJECT MODES
    # ----------------------------------------------------
    class RouteDecision(BaseModel):
        target_category: str = Field(description="Must be either 'Benefits', 'Compliance', or 'Irrelevant'.")
        extracted_region: str = Field(description="Target region like 'US', 'UK', or 'Global' if unspecified.")
        confidence_score: float = Field(description="Float between 0.0 and 1.0")

    class EvaluationResult(BaseModel):
        is_hallucination: bool = Field(description="True if model makes claims unsupported by context chunks.")
        missing_citations: bool = Field(description="True if the response fails to quote specific chunk IDs.")
        remedy_suggestion: Optional[str] = Field(description="If flawed, how to fix it.")

    # ----------------------------------------------------
    # 3. END-TO-END WORKFLOW ENGINE
    # ----------------------------------------------------
    class EnterpriseRAGEngine:
        def __init__(self, sim_threshold: float = 0.70):
            self.sim_threshold = sim_threshold

        async def route_request(self, query: str) -> RouteDecision:
            """Step 1: Intent Routing Graph Node (Gemini Structured Outputs)"""
            prompt = f"Inspect the user query and classify it: '{query}'"
            
            # Wrapping in an async executor thread so it doesn't block the main event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model='gemini-2.5-flash', # Fast model for metadata extraction
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RouteDecision,
                        temperature=0.0
                    )
                )
            )
            return RouteDecision.model_validate_json(response.text)

        def retrieve_with_metadata_guardrails(self, query_vector: List[float], route: RouteDecision) -> List[Dict[str, Any]]:
            """Step 2: Vector Search Mechanics + Hard Meta Filters"""
            matched_chunks = []
            for chunk in HR_KNOWLEDGE_BASE:
                if route.target_category != chunk["category"]:
                    continue
                if route.extracted_region != "Global" and chunk["region"] != "Global" and route.extracted_region != chunk["region"]:
                    continue
                    
                similarity = calculate_cosine_similarity(query_vector, chunk["embedding"])
                if similarity >= self.sim_threshold:
                    chunk_copy = chunk.copy()
                    chunk_copy["similarity_score"] = similarity
                    matched_chunks.append(chunk_copy)
                    
            return sorted(matched_chunks, key=lambda x: x["similarity_score"], reverse=True)

        async def generate_source_cited_answer(self, query: str, contexts: List[Dict[str, Any]]) -> str:
            """Step 3: Prompt Augmentation & Citation Synthesis"""
            if not contexts:
                return "I am sorry, but I cannot find verified documentation in our verified knowledge databases to answer this request."

            context_str = ""
            for c in contexts:
                context_str += f"--- START CHUNK {c['id']} [Source: {c['source']}] ---\n{c['text']}\n--- END CHUNK ---\n"

            system_instruction = (
                "You are an Enterprise HR Expert. Synthesize an answer using ONLY the context fragments provided below. "
                "For every claim you make, you MUST append a bracketed citation pointing to the chunk ID (e.g., [chunk_01]). "
                "If the context does not contain the answer, you must state 'Data source unavailable' and stop."
            )
            user_content = f"Context Material:\n{context_str}\n\nUser Question: {query}"

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model='gemini-2.5-pro', # Strong reasoning model for strict grounding
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )
            )
            return response.text

        async def evaluate_output(self, query: str, context: List[Dict[str, Any]], candidate_answer: str) -> EvaluationResult:
            """Step 4: Hallucination and Quality Guardrail Evaluation Node"""
            if not context:
                return EvaluationResult(is_hallucination=False, missing_citations=False, remedy_suggestion=None)

            prompt = f"""
            Analyze this RAG system output against the retrieved documentation matrix.
            Retrieved Context Chunks: {[c['text'] for c in context]}
            Candidate Answer Generated: {candidate_answer}
            Original User Query: {query}

            Verify that the answer contains zero information outside the context and references chunk IDs explicitly.
            """
            
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EvaluationResult,
                        temperature=0.0
                    )
                )
            )
            return EvaluationResult.model_validate_json(response.text)

        async def execute_loop(self, user_query: str):
            """Coordinates execution lifecycle across runtime paths with error isolation."""
            print(f"\n🚀 [INPUT] Processing Query: '{user_query}'")
            
            try:
                # 1. Routing Graph Node
                route = await self.route_request(user_query)
                print(f"📍 [ROUTE] Category='{route.target_category}' | Region='{route.extracted_region}' (Conf: {route.confidence_score})")
                
                if route.target_category == "Irrelevant":
                    print("🛑 [HALT] Prompt dropped out of pipeline: Irrelevant domain classification.")
                    return

                # 2. Dense Vector Mechanics Node
                query_vector = mock_query_embedding(user_query)
                retrieved_chunks = self.retrieve_with_metadata_guardrails(query_vector, route)
                print(f"📚 [RETRIEVAL] Found {len(retrieved_chunks)} relevant metadata-isolated context blocks.")
                for rc in retrieved_chunks:
                    print(f"   -> Match: {rc['id']} | Similarity: {rc['similarity_score']:.4f} | Source: {rc['source']}")

                # 3. Augmented Synthesis Node
                final_answer = await self.generate_source_cited_answer(user_query, retrieved_chunks)
                
                # 4. Critical Verification Guardrail
                eval_report = await self.evaluate_output(user_query, retrieved_chunks, final_answer)
                
                if eval_report.is_hallucination or eval_report.missing_citations:
                    print("⚠️ [GUARDRAIL ALERT] Faithfulness check failed! Applying fallback strategy...")
                    print(f"   Reasoning: {eval_report.remedy_suggestion}")
                    final_answer = "Generation blocked: System flag raised on contextual alignment verification guidelines."

                print(f"\n✨ [FINAL SYSTEM RESPONSE]:\n{final_answer}\n" + "="*50)

            except Exception as e:
                print(f"❌ EXECUTION FAILED: {str(e)}")

    # ----------------------------------------------------
    # 4. RUNTIME EXECUTION
    # ----------------------------------------------------
    async def main():
        rag_engine = EnterpriseRAGEngine(sim_threshold=0.72)
        
        # Test Case A: Valid US Benefits request
        await rag_engine.execute_loop("How many weeks of vacation time do US employees get standard?")
        
        # Test Case B: Route correctly to InfoSec compliance
        await rag_engine.execute_loop("What is the enterprise password rotation cadence?")
        
        # Test Case C: Out of bounds domain handling
        await rag_engine.execute_loop("Can you help me write an application code block in Javascript?")

    asyncio.run(main())