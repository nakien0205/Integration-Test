import os
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from openai import OpenAI
import sys

load_dotenv()
os.environ["API"] = os.environ.get("API", "")

MODEL_NAME = "meta-llama/llama-4-maverick:free"
SYS_PROMPT = (
    "You are a helpful assistant. Be concise. "
    "Use tools when they would improve accuracy or access fresh info."
)


@function_tool
def end_conversation():
    """
    End the conversation with the user when they intent to.
    """
    sys.exit(0)


BUILT_IN_TOOLS = [
    "web_search",        # let the model browse the web when needed
    # "file_search",       # RAG over files you attach
]


assistant = Agent(
    name="Shopping assistant",
    model=MODEL_NAME,
    instructions=SYS_PROMPT,
    tools=[end_conversation, *BUILT_IN_TOOLS],
)

def main():
    while True:
        try:
            user_text = input("You: ")

            # The SDK handles tool-calling and multi-step loops for you.
            result = Runner.run(assistant, user_text)
            print(f"\nAssistant: {result.throw}\n")

        except KeyboardInterrupt:
            print("\n[Interrupted]")
            break
        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    main()
