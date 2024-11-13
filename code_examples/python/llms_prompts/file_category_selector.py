from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize LangChain ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

def classify_file_type(file_content):
    """Determine if a file is claims, membership, or cag type using GPT"""
    try:
        # Create prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a pharmaceutical data analyst. Classify files as 'claims', 'membership', or 'cag' based on their content.
            Here are some examples:
             
            File content: MemberID,EnrollDate,PlanType,Gender,DOB
            Classification: membership
             
            File content: ClaimID,DateOfService,NDC,Quantity,PrescriberNPI
            Classification: claims
             
            File content: GroupID,ContractType,BenefitYear,FormularyCode
            Classification: cag
            """),
            HumanMessage(content=f"File content: {file_content}")
        ])

        # Format prompt and invoke chain
        prompt = prompt_template.invoke({"content": file_content})
        response = llm.invoke(prompt)
        
        return response.content
    except Exception as e:
        return f"Error classifying file: {str(e)}"

def main():
    # Sample file contents for testing
    file1 = "PatientID,RxNumber,PharmacyID,DrugName,DaysSupply"
    file2 = "SubscriberID,EffectiveDate,TermDate,RelationshipCode"
    file3 = "ContractID,BenefitDesign,CopayTier,NetworkType"

    # Test the classifier with different files
    print(f"File 1 type: {classify_file_type(file1)}")
    print(f"File 2 type: {classify_file_type(file2)}")
    print(f"File 3 type: {classify_file_type(file3)}")

if __name__ == "__main__":
    main() 
























# Create prompt with few-shot examples in different messages
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a pharmaceutical data analyst. Classify files as 'claims', 'membership', or 'cag' based on their content."),
#     ("user", "File content: MemberID,EnrollDate,PlanType,Gender,DOB"),
#     ("assistant", "membership"),
#     ("user", "File content: ClaimID,DateOfService,NDC,Quantity,PrescriberNPI"),
#     ("assistant", "claims"),
#     ("user", "File content: GroupID,ContractType,BenefitYear,FormularyCode"),
#     ("assistant", "cag"),
#     ("user", "File content: {content}")
# ])
