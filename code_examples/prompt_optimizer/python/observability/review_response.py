from langsmith import evaluate, Client
from langsmith.schemas import Example, Run

# 1. Create and/or select your dataset
client = Client()
dataset = client.clone_public_dataset("https://smith.langchain.com/public/a63525f9-bdf2-4512-83e3-077dc9417f96/d")

# 2. Define an evaluator
def is_helpful(root_run: Run, example: Example) -> dict:
    score = len(root_run.outputs["output"]) < 3 * len(example.outputs["answer"])
    return {"key": "is_concise", "score": int(score)}

# 3. Run an evaluation
evaluate(
    lambda x: x + "is a good question. I don't know the answer.",
    data=dataset.name,
    evaluators=[is_helpful],
    experiment_prefix="my first experiment"
)