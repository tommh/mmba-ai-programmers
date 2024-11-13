from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llms = [
    ChatOpenAI(model="gpt-4"),
    ChatOpenAI(model="gpt-4o-mini"),
    OllamaLLM(model='llama2'), 
    OllamaLLM(model='zephyr'), 
]

model_names = [
    "gpt-4",
    "gpt-4o-mini",
    "llama2",
    "zephyr",
]

prompt = """
    I want you to tell me if the following movie review is positive or negative.

    Review: This film shouldn't work at all. It doesn't have much of a story and the whole 
    dial up internet thing is incredibly dated. However Hanks and Ryan sell it beautifully.
"""


for i, llm in enumerate(llms):
    parser = StrOutputParser()
    response = llm.invoke(prompt)
    content = parser.invoke(response)
    result = f"{model_names[i].upper()}\n{content}\n_________________________\n"
    print(result)



















    # The final response should be in the following format:
    # reasoning: reason for giving the sentiment
    # sentiment: "positive" or "negative"