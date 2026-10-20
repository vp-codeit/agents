from dotenv import load_dotenv
from openai import OpenAI
import json
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
import os

load_dotenv(override=True)

# import urllib.request

# def get_book_from_gutenberg(url, output_file):
#     print("Downloading book...")
#     urllib.request.urlretrieve(url, output_file)
#     print(f"Saved successfully as {output_file}!")

# download the book from gutenberg

# get_book_from_gutenberg("https://www.gutenberg.org/cache/epub/75570/pg75570.txt", "psychology_of_stock_market.txt")

# # Get the text from the pdf file- use it as a context for the agent
# reader = PdfReader("/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/Psychology_of_Stock_Market.pdf")
# psychology_sm = ""
# for page in reader.pages:
#     if page.page_number >=4:
#         text = page.extract_text(extraction_mode="layout")
#         if text:
#             psychology_sm += text

# A tool must be defined as the ollama uses local models; custom function tools supported     
tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Use web search to check for answers online",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query term",
                }
            },
            "required": ["query"],
        },
    },
}]

# Pydantic Model for evaluation
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class StockPsychologyAgent:

    def __init__(self):
        with open(f"/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/psychology_of_stock_market.txt","r",encoding="utf-8") as f:
            self.psychology_sm = f.read()
        with open(f"/Users/macminived/vpvprojects/agents/1_foundations/Dev_Handson/Market_Sentiment_Expert_Summary.txt","r",encoding="utf-8") as f:
            self.summary = f.read()

        # self.name = "Vedant"

        # Ollama initialized - To deploy to hugging faces dont need ollama as it runs on local
        # self.ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        # self.model_name = "qwen2.5-coder:3b"
        
        # OpenAI initialized
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_model_name = "gpt-4o-mini"

        #Gemini initialized- it supports only chat completions not responses
        self.gemini = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY"), 
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.evaluator_model_name = "gemini-2.0-flash" # only certain model supported by googleapi so far

        # Agent Name
        self.agent_name = "RJ"

    def system_prompt(self):
        # define the system prompt
        system_prompt = f"""
        # Your role

        You are a helpful assistant named {self.agent_name} that can answer questions about the psychology of stock market on your website. You are given a summary of your role and background as well as \
        a context of the psychology of stock market based on which you can answer questions from the user. 

        Here are the details of your role and background:

        Your job is to stay true to the context and answer as accurately as possible. Do NOT assume anything.\
        TOOL USE INSTRUCTIONS:
        1. ALWAYS refer to the Context you are provided with and the conversation history FIRST 
        2. If the user's question can be answered using the provided context DO NOT CALL any tools
        3. Use your tools to do a web search on live internet ONLY IF the answer is not available in the context.
        """
        system_prompt+=f"\n\n## Summary:\n{self.summary}\n\n## Context:\n{self.psychology_sm}\n\n"
        system_prompt+= f"With this information, answer as if the user is a potential client or future employer who came across the website."

        # print(system_prompt[:2000])
        return system_prompt

    def evaluator_system_prompt(self):
        # define evaluator system prompt
        evaluator_system_prompt = f"""You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is of acceptable quality. \
        The Agent is someone who can answer questions about the psychology of stock market on a website. \
        The Agent has been provided with a role summary and context. Here's the information:"

        evaluator_system_prompt+=f"\n\n## Summary:\n{self.summary}\n\n## Context:\n{self.psychology_sm}\n\n"
        evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback.You must respond strictly in valid JSON format with the following keys: \
        1. "is_acceptable": boolean (true or false) \
        2. "feedback": string (Provide detailed, constructive feedback explaining why the response is acceptable or what needs to be improved. It should not be empty)"""

        return evaluator_system_prompt

    #Evaluate using other model- OpenAI

    def evaluate(self,message,reply,history) -> Evaluation:
        messages = [{"role":"system","content":self.evaluator_system_prompt()}]+[{"role":"user","content":f"Message from user:{message}\n\n Reply from agent:{reply}\n\n Conversation history:{history}"}]
        # using gemini for evaluation so it supports create and not parsed so the code is adapted to give response_format as a json object which can be processed in Evaluation
        response = self.gemini.beta.chat.completions.create(model = self.evaluator_model_name,messages = messages,response_format = {"type":"json_object"})
        evaluation_output = response.choices[0].message.content
        evaluation_output_parsed = json.loads(evaluation_output)

        return Evaluation(
            is_acceptable=evaluation_output_parsed.get("is_acceptable", True),
            feedback=evaluation_output_parsed.get("feedback", "")
        )

    def rerun(self,reply,message,history,feedback):
        messages = history+[{"role":"user","content":message}]
        response = self.openai.responses.create(model=self.chat_model_name,instructions=self.system_prompt()+f"\n Your previous answer:{reply} got rejected.\n Feedback for rejected answer: {feedback}",input=messages) 
        reply = response.output_text
        
        return reply

    # define chat function 
    # using responses api - only supported by openai currently while chat.completions is standard
    # using in built tools from ollama/openai. Imported web_search but passing the value using custom function
    def chat(self,message,history):
        input_items = []
        for item in history:
            if isinstance(item, dict):
                input_items.append({"role": item.get("role", "user"), "content": item.get("content", "")})
            else:
                input_items.append(item)
        input_items.append({"role": "user", "content": message})
        messages = input_items
        response = self.openai.responses.create(model = self.chat_model_name,instructions = self.system_prompt(),input = messages,tools = [{"type":"web_search"}])
        reply = response.output_text

        # response_message = response.choices[0].message
        # if response_message.tool_calls:
        #     messages.append(response_message)
        #     for item in response_message.tool_calls:
        #         if item.function.name == "web_search":
        #             args = json.loads(item.function.arguments)
        #             result = web_search(args.get("query",""))
        #             # Safely parse result: avoid sending empty dict/list string
        #             if not result:
        #                 content_result = (
        #                     "No web search results found. Proceed using your base"
        #                     " knowledge."
        #                 )
        #             elif isinstance(result, (dict, list)):
        #                 content_result = json.dumps(result)
        #             else:
        #                 content_result = str(result)
        #             print(f"Web search results:\n{content_result}")
        #             messages.append({
        #                 "role":"tool",
        #                 "content":content_result,
        #                 "tool_call_id":item.id
        #             })
            # response = self.ollama.chat.completions.create(
            #     model=self.model_name,
            #     messages=messages,
            #     # tools = tools, # dont need a tool call here again
            #     extra_body={
            #         "options": {
            #         "num_ctx": 8192  # Caps context window to 8k tokens (saves ~2-3 GB RAM)
            #         }
            #     }
            # ) 
            # reply = response.choices[0].message.content
        # else:
        #     reply = response.choices[0].message.content
            
        evaluation = self.evaluate(message,reply,history)

        if(evaluation.is_acceptable):
            print(f"Response from {self.agent_name} is acceptable")
            print(f"Feedback from evaluaor: {evaluation.feedback}")
        else:
            print(f"Response from {self.agent_name} is not acceptable")
            print(f"Feedback from evaluator: {evaluation.feedback}")
            print("Retrying...")
            reply = self.rerun(reply,message,history,evaluation.feedback)
        
        return reply

    # chat("Hi ! How does the market sentiment cause rise and fall in prices of a stock?",[])

if __name__ == "__main__":
    agent = StockPsychologyAgent()
    demo = gr.ChatInterface(agent.chat, type="messages")

    try:
        demo.launch(server_name="0.0.0.0", server_port = 7860)
    except KeyboardInterrupt:
        demo.close()


