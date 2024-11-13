from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def extract_event_info():
    # Initialize the ChatOpenAI model
    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    
    # Create the messages
    messages = [
        ("system", "Extract the event information."),
        ("user", "Alice and Bob are going to a science fair on Friday.")
    ]
    
    # Get the response
    response = chat(messages)
    
    return response

# Example usage
if __name__ == "__main__":
    result = extract_event_info()
    print(result)
    print(f"\nContent:\n{result.content}")