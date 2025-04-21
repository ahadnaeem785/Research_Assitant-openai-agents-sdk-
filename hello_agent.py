from agents import Agent, Runner
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# gemini_api_key = os.getenv("GEMINI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY") 


agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "whats my name")
print(result.final_output)
