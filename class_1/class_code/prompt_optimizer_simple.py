import openai
import pandas as pd
from typing import Callable, Dict
from langsmith import traceable

class SimplePromptOptimizer:
    def __init__(self, model_name: str = "gpt-4o-mini-0125"):
        self.client = openai.OpenAI()
        self.model_name = model_name

    def optimize(self, system_prompt: str, dataset_path: str, evaluate_func: Callable, max_iterations: int = 3) -> tuple:
        
        # Load dataset
        examples = pd.read_csv(dataset_path)
        
        best_prompt = system_prompt
        best_score = 0
        
        # Optimization loop
        for iteration in range(max_iterations):
            current_score = 0
            
            # Test current prompt on all examples
            for index, example in examples.iterrows():
                # Create messages for OpenAI
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": example["Review"]}
                ]
                
                response = self.test_prompt(messages)
                
                # Evaluate response
                score = evaluate_func(response.choices[0].message.content, {"Sentiment": example["Sentiment"]})
                current_score += score
            
            avg_score = current_score / len(examples)
            print(f"Iteration {iteration + 1}, Average Score: {avg_score}")
            
            # Update best prompt if current score is better
            if avg_score > best_score:
                best_score = avg_score
                best_prompt = system_prompt
            
            # If perfect score or last iteration, break
            if avg_score == 1.0 or iteration == max_iterations - 1:
                break
                
            # Generate improved prompt
            system_prompt = self._improve_prompt(system_prompt, examples, avg_score)
            print(f"Improved prompt: {system_prompt}")
        
        return best_prompt, best_score
    
    @traceable(
        name="prompt-tester",
        tags=["prompt-tester"]
    )
    def test_prompt(self, messages: list) -> str:
        return self.client.chat.completions.create(model=self.model_name, messages=messages, temperature=0)

    @traceable(
            name="prompt-optimizer",
            tags=["prompt-optimizer"]
    )
    def _improve_prompt(self, current_prompt: str, examples: pd.DataFrame, current_score: float) -> str:
        # Create improvement prompt
        example_strings = "\n\n".join(f"""Review: {obj["Review"]}\nSentiment: {obj["Sentiment"]}""" for obj in examples.to_dict('records'))
        messages = [
            {
                "role": "system",
                "content": """You are an expert prompt engineer. Your task is to improve a prompt template to get better results.
                             Analyze the current prompt and examples, then suggest an improved version that will lead to better performance.
                             Keep the same basic structure but enhance the instructions and constraints."""
            },
            {
                "role": "user",
                "content": f"""Current prompt template: {current_prompt}
                           Current performance score: {current_score}
                           Example inputs and outputs: {example_strings}
                           
                           Please provide an improved version of the prompt template that will lead to better results.
                           Only return the new prompt template, nothing else."""
            }
        ]
        
        # Get improvement suggestion
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0
        )
        
        return response.choices[0].message.content

# Example usage:
if __name__ == "__main__":
    def evaluate_sentiment(output: str, expected: Dict) -> float:
        return 1.0 if expected["Sentiment"].lower() == output.strip().lower() else 0.0
    
    optimizer = SimplePromptOptimizer()
    best_prompt, best_score = optimizer.optimize(
        dataset_path="../datasets/movie_reviews.csv",
        evaluate_func=evaluate_sentiment,
        system_prompt="You determine if movie reviews are either positive or negative."
        # system_prompt="Given a movie review, analyze the sentiment as either positive or negative by evaluating the overall tone, specific aspects mentioned, and the context in which they are presented. Ensure to consider the nuances of the language used and the overall impact on the viewer's experience to make a precise judgment. The result should be either 'positive' or 'negative'"
    )
    
    print(f"\nBest Score: {best_score}")
    print(f"\nBest Prompt:\n{best_prompt}")