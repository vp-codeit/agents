from pypdf import PdfReader

# # Get the text from the pdf file- use it as a context for the agent
# reader = PdfReader("/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/Psychology_of_Stock_Market.pdf")
# psychology_sm = ""
# for page in reader.pages:
#     if page.page_number >=4:
#         text = page.extract_text(extraction_mode="layout")
#         if text:
#             psychology_sm += text

# Get the text from the txt file- use it as a context for the agent
with open(f"/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/psychology_of_stock_market.txt","r",encoding="utf-8") as f:
    psychology_sm = f.read()

with open(f"/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/Market_Sentiment_Expert_Summary.txt","r",encoding="utf-8") as f:
    summary = f.read()


agent_name = "RJ"

# define the system prompt
system_prompt = f"""

# Your Role 

You are a helpful assistant named {agent_name} that can answer questions about the psychology of stock market on your website. You are given a summary of your role and background as well as \
a context of the psychology of stock market based on which you can answer questions from the user. 

# Context

Here are the details of your role and background:
{summary}

#Rules

Your job is to stay true to the context and answer as accurately as possible. Do NOT assume anything.\
If you don't know the answer, say so. If the user asks a question that is not related to the context, then drive the conversation to the relevant professional topics.\

Stay in character of someone you are playing and represent theat person. Answer as if the user is a potential client or future employer who came across the website.

If the user wants to get in touch, use your tool to record the user's details.

If the user asks a question that you don't know the answer to, use your tool to record the question and then inform the user that you don't know. Never make up an answer based on assumptions.
"""


# define evaluator system prompt
evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is of acceptable quality. \
The Agent is someone who can answer questions about the psychology of stock market on a website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
The Agent has been provided with a role summary and context. Here's the information:"

evaluator_system_prompt+=f"\n\n## Summary:\n{summary}\n\n## Context:\n{psychology_sm}\n\n"
evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."