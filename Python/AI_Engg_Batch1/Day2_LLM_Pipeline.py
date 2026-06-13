def LLM_Pipeline():
    import os
    from typing import List, Literal
    from groq import Groq
    from pydantic import BaseModel, Field, ValidationError
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # =====================================================================
    # 1. Define the Desired Output Schema using Pydantic
    # =====================================================================

    class CustomerEmailAnalysis(BaseModel):
        sentiment: Literal["Positive", "Neutral", "Negative"] = Field(
            description="The overall emotional tone of the email."
        )
        urgency: Literal["Low", "Medium", "High", "Critical"] = Field(
            description="How quickly this email requires a response based on tone and content."
        )
        core_entities: List[str] = Field(
            description="Key entities mentioned (e.g., product names, order IDs, tracking numbers, specific employee names)."
        )
        summary: str = Field(
            description="A concise, one-sentence summary of the customer's primary issue or request."
        )

    # =====================================================================
    # 2. Main Pipeline Function
    # =====================================================================

    def analyze_customer_email(email_content: str) -> CustomerEmailAnalysis | None:
        # Initialize the Groq client

        client = Groq()

        # System instructions to enforce JSON output matching the schema
        system_prompt = (
            "You are an advanced customer service AI. Your job is to analyze unstructured emails "
            "and extract specific structured information. You must respond ONLY with a valid JSON object "
            "matching this exact schema:\n"
            "{\n"
            '  "sentiment": "Positive" | "Neutral" | "Negative",\n'
            '  "urgency": "Low" | "Medium" | "High" | "Critical",\n'
            '  "core_entities": ["item1", "item2"],\n'
            '  "summary": "string"\n'
            "}"
        )

        try:
            # Requesting completion from Groq using a fast, capable model
            # Enforcing JSON mode via response_format
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze the following email:\n\n{email_content}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0, # Low temperature for more deterministic, schema-adherent output
            )

            raw_json_output = completion.choices[0].message.content
            
            # Validate the raw JSON against our Pydantic schema
            validated_data = CustomerEmailAnalysis.model_validate_json(raw_json_output)
            return validated_data

        except ValidationError as ve:
            print(f"\n[Validation Error] LLM output failed to match schema: {ve}")
            # In production, you might log this or route it to a fallback parser/human review
            return None
        except Exception as e:
            print(f"\n[API Error] Something went wrong with the Groq API: {e}")
            return None

    # =====================================================================
    # 3. Test Drive with Sample Data
    # =====================================================================

    # Sample unstructured, frustrated customer email
    sample_email = """
    Subject: Broken item and missing parts!! ORDER #99281A
    
    Hi support team, 
    I ordered the QuantumX Blender last week, and it finally arrived today. However, the glass pitcher 
    is completely shattered inside the box! On top of that, I couldn't find the recipe booklet that 
    was supposed to be included. 
    
    I need a replacement sent out immediately because I'm hosting a catering event this weekend 
    and absolutely need this blender. Please get back to me ASAP.
    
    Thanks,
    Sarah Jenkins
    """

    print("Analyzing email with Groq...")
    result = analyze_customer_email(sample_email)

    if result:
        print("\n--- Successfully Extracted & Validated Data ---")
        # Pydantic v2 dump to dict / pretty print
        import json
        print(json.dumps(result.model_dump(), indent=2))
        
        # You can now safely access fields with dot notation and full IDE autocomplete
        print(f"\nTrigger alerts? {'YES' if result.urgency in ['High', 'Critical'] else 'NO'}")
