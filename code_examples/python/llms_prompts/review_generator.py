from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize LangChain chat model
chat = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=150
)

def generate_response(review):
    """Generate a friendly response to a customer review"""
    try:
        # Create the messages for LangChain
        messages = [
            SystemMessage(content="""
                          You are a friendly customer service representative at a car dealership. 
                          Keep responses professional, empathetic, and under 100 words. 
                          Generate a resonse to these Google reviews. 
            """),
            HumanMessage(content=f"{review}")
        ]

        # Get response from LangChain
        response = chat.invoke(messages)
        
        return response.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def main():
    # Sample reviews
    reviews = [
        "My recent purchase of a truck from Sammy at AutoSalesInc was the easiest automobile buying experience I have had.  We found the truck with the options I wanted, gave it a test drive and talked about what I was willing to pay. From this point I put it in Sammy's hands. Sammy and the AutoSalesInc team went to work and in the next day they figured out the financing.  When everything was ready I went back, and signed the paperwork.  Sammy had the truck detailed and he delivered it to my house.  How much better does a car buying experience get than this?  Thank you Sammy and the whole AutoSalesInc team!",
        "I am so frustrated with AutoSalesInc. My husband and I purchased a car for our son in May for graduating high school. The salesperson that we working with was amazing, but that is where it ends. The person that did our financing is 100% the reason people avoid dealerships. He did a number dump trying to get us to purchase all of the extended warranties, which is fine. I was very clear when I arrived that I wanted our financing to go through State Credit Union, even if the interest rate is a little higher, they are amazing to work with. The jerk still submitted 5 hard injuries by satelliting my credit application around, and that kind of crap really hurts your credit score. Now I will have 5 hard pulls on there for 3 years. Thanks for not listening to me AutoSalesInc. This was a first and a last time for me.",
        "Could not order what my car needs because it was more than what the Springfield Heights dealership charges"
    ]

    # Generate responses for each review
    for i, review in enumerate(reviews, 1):
        print(f"\nReview {i}: {review}")
        print(f"Response {i}: {generate_response(review)}")
        print("-" * 50)

if __name__ == "__main__":
    main()
