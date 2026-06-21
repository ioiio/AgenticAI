def WriterCritic():
    import os
    import json
    from typing import Dict, Any
    from groq import Groq
    from pydantic import BaseModel, Field

     # 1. Initialize the Groq LLM
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()

    # Define the structured output schema for the Critic- using Pydantic
    class ReviewEvaluation(BaseModel):
        score: int = Field(..., description="A score from 1 to 10 evaluating the content against requirements.")
        feedback: str = Field(..., description="Detailed feedback on what to improve, or praise if it passes.")
        requirements_met: bool = Field(..., description="True if score >= 8 and all criteria are fully met, False otherwise.")

    class WriterCriticWorkspace:
        def __init__(self, model: str = "llama-3.3-70b-versatile", passing_score: int = 8, max_iterations: int = 4):
            """
            Initializes the workspace with a Groq client, model selection, and loop boundaries.
            """
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            self.model = model
            self.passing_score = passing_score
            self.max_iterations = max_iterations

        def _writer_agent(self, prompt: str, criteria: str, feedback: str = None, previous_draft: str = None) -> str: #Agent responsible for drafting and revising content based on feedback.
            """
            Agent responsible for drafting and revising content based on feedback.
            """
            system_instruction = (
                "You are an expert Content Writer. Your goal is to draft high-quality content "
                "that strictly adheres to the user's prompt and criteria."
            )
            
            user_content = f"User Prompt: {prompt}\nStrict Criteria: {criteria}\n"
            if feedback and previous_draft:
                user_content += (
                    f"\n--- This is a revision cycle ---\n"
                    f"Your Previous Draft:\n{previous_draft}\n\n"
                    f"Critic's Feedback for Improvement:\n{feedback}\n\n"
                    f"Please rewrite the content, addressing all feedback point-by-point."
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7 #Uses a higher temperature (0.7) so it has the freedom to rewrite things creatively.
            )
            return response.choices[0].message.content

        def _critic_agent(self, prompt: str, criteria: str, current_draft: str) -> ReviewEvaluation: #Agent responsible for evaluating the current draft against the original prompt and criteria, returning structured feedback.
            # Adding a strict JSON layout example to the system prompt
            system_instruction = (
                "You are a rigorous, objective Editorial Critic. Assess the provided draft against the "
                "original prompt and criteria. You must return a valid JSON object matching this exact schema:\n"
                "{\n"
                '  "score": <int 1-10>,\n'
                '  "feedback": "<string containing your detailed review>",\n'
                '  "requirements_met": <bool true/false>\n'
                "}\n"
                "CRITICAL RULE: If you give a score of 8 or higher, 'requirements_met' MUST be set to true. "
                "If the score is 7 or lower, 'requirements_met' MUST be set to false.\n"
                "Do not nest objects inside the feedback field. Ensure all fields are present."
            )
            
            user_content = (
                f"Original Prompt: {prompt}\n"
                f"Criteria to Evaluate Against: {criteria}\n\n"
                f"Current Draft to Review:\n{current_draft}"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1, # Lowered because we don't want a "creative" critic; we want an objective, strict grader who follows the rules.
                response_format={"type": "json_object"}
            )
            
            raw_json = response.choices[0].message.content
            return ReviewEvaluation.model_validate_json(raw_json)

        def run(self, prompt: str, criteria: str) -> Dict[str, Any]: #The Orchestrator/ manager that runs the loop and returns a final result summary
            """
            Orchestrates the cyclical Writer-Critic loop.
            """
            print(f"🚀 Starting Writer-Critic workspace...")
            print(f"Target Passing Score: {self.passing_score}/10 | Max Cycles: {self.max_iterations}\n")
            
            current_draft = ""
            feedback = None
            
            for iteration in range(1, self.max_iterations + 1):
                print(f"--- 🔄 Cycle {iteration} ---")
                
                # 1. Writer Phase
                print("[Writer] Drafting/Revising content...")
                current_draft = self._writer_agent(prompt, criteria, feedback, current_draft)
                
                # 2. Critic Phase
                print("[Critic] Evaluating current draft...")
                evaluation = self._critic_agent(prompt, criteria, current_draft)
                
                print(f"[Evaluation Results] Score: {evaluation.score}/10 | Meets Criteria: {evaluation.requirements_met}")
                print(f"[Critic Feedback]: {evaluation.feedback}\n")
                
                # 3. Evaluation/Exit Condition check
                if evaluation.requirements_met or evaluation.score >= self.passing_score:
                    print(f"✅ Success! Content met criteria on Cycle {iteration}.\n")
                    return {
                        "status": "success",
                        "cycles_completed": iteration,
                        "final_score": evaluation.score,
                        "final_content": current_draft,
                        "critic_notes": evaluation.feedback
                    }
                
                # Set up feedback variables for the next iteration rewrite
                feedback = evaluation.feedback

            print("⚠️ Loop reached maximum iterations without reaching target passing score.")
            return {
                "status": "max_iterations_reached",
                "cycles_completed": self.max_iterations,
                "final_score": evaluation.score,
                "final_content": current_draft,
                "critic_notes": evaluation.feedback
            }

    # --- Execution Example ---
    # Define a complex writing task requiring specific execution elements
    task_prompt = "Write a short promotional announcement email introducing a new quantum computing API."
    task_criteria = (
        "1. Must contain an attention-grabbing subject line.\n"
        "2. Must explain quantum computing benefits simply without dense jargon.\n"
        "3. Must include a clear, compelling Call to Action (CTA).\n"
        "4. Tone must be professional yet enthusiastic.\n"
        "5. Keep total length under 150 words."
    )

    workspace = WriterCriticWorkspace(
        model="llama-3.3-70b-versatile", 
        passing_score=9, 
        max_iterations=2 #Explicit Instruction
    )
    
    result = workspace.run(prompt=task_prompt, criteria=task_criteria)
    
    print("================ FINAL OUTPUT ================")
    print(result["final_content"])
    print("==============================================")