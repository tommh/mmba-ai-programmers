# Observability

## Introduction

Observability is the ability to momnitor, log, and understand a system's behavior. Observability is a broad term that can synonmous with other termins like logging, but with LLMs, there are many unique features that are essential. Features like LLM tracing, datasets, and evaluations are all features that every LLM project needs to ensure their app maintains a high level of output. We'll cover all of these as well as some strategies to help build an observability system that keeps your apps humming. 

## Core Competencies

Tracks LLM performance and optimizes prompts
Key topics:
Setting up LangSmith
Observing LLM calls
Building datasets and scoring
Human-in-the-loop for evaluations

Examples:
Health insurance chatbot
Local document chatbot
SQL evaluations

### The student must demonstrate...

1. Set up a logging system (e.g., using LangSmith) to track LLM performance and identify areas for optimization.
2. Create a dataset to evaluate model performance using a scoring metric (e.g., accuracy, F1 score).
3. Implement human-in-the-loop feedback mechanisms to improve model performance.

## Coding Problems

1. **Observability Platforms and Setting up LangSmith**
   
   - **Core Competency:** Know that LangSmith and Langfuse are two good options, setting up LangSmith in your app, find the traces, navigating a trace, these platforms usually have options for HIPPA compliance. 

   - **Relevance:** Understanding how to set up a logging mechanism like LangSmith is crucial for monitoring LLM performance as it helps us avoid model drift and poor actors

   - **Procedure:**
    1. Discuss observability and how it supports LLM performance
    2. Install the LangSmith library in your project using pip or npm.
    2. Set up a logger instance and configure it to track key metrics (e.g., model accuracy, response time).
    3. Use tracing mechanisms to monitor and analyze AI model performance.

1. **Datasets**
   
   - **Core Competency:** What are datasets, why do we use datasets, setting up a dataset, the value of example data, generating synthetic data, adding items to datasets

   - **Relevance:** Datasets provide a basis for evaluating model performance and identifying areas for improvement.
   
   - **Procedure:**
    1. Create a dataset in LangSmith using a data source (e.g., CSV file, API).
    2. Define a scoring metric to evaluate model performance (e.g., accuracy, F1 score).
    3. Use the dataset to train and test your LLM.

1. **Evaluations**
   
   - **Core Competency:** What are evaluations, evaluation stratgies like llm judge and relevancy, what is LLM drift and how do we avoid it

   - **Relevance:** Evaluating model performance is crucial for identifying areas of improvement.

   - **Procedure:**
      1. Choose a suitable metric (e.g., accuracy, F1 score) for evaluating model performance.
      2. Use the chosen metric to evaluate your LLM's performance on a dataset.
      3. Analyze results and adjust model parameters as needed.
      4. Use different strategies to improve the prompt and, thereby, the score


1. **Human-in-the-Loop**
   
   - **Core Competency:** What is human-in-the-loop, cost-benefit of human-in-the-loop, ways to have users grade the outputs 

   - **Relevance:** Human feedback provides valuable insights for improving model performance.
   - **Procedure:**
      1. Set up a mechanism for collecting user feedback (e.g., thumbs up/down, evaluate generated output with corrected output).
      2. Use collected feedback to adjust model parameters and improve performance.
         - add items to datasets to run the prompt optimizer
      3. Evaluate the impact of human feedback on model performance.


### Challenge 1: 

**Objective:** 

## Conclusion

