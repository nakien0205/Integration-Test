from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('api'),
)

# changable parameter
sys_prompt = '''You are a helpful image describing assistant, you will be given infomation about the image and the image 
itself. Your goal is to describe it to the user.'''
detail_response = 'auto' # low = fast but bad, high = slow but good
test_url = "https://m.media-amazon.com/images/I/61okhX4ooWL._AC_SL1000_.jpg"
# end of changable

vision_checker = [
    r"\bimage\b", r"\bpicture\b", r"\bphoto\b", r"\bsee\b",
    r"\bspot\b", r"in this image", r"describe (this|the) (image|photo|picture)"
]

def is_vision(text) -> bool:
    t = text.lower()
    return any(re.search(pat, t) for pat in vision_checker)

def build_user_content(user_text: str, image_urls=None, detail=detail_response):
    """
    Returns appropriate 'content' for a user message:
    - text-only -> string
    - text + image(s) -> list of content blocks
    """
    if image_urls:
        blocks = [{"type": "text", "text": user_text}]
        for url in image_urls:
            blocks.append({"type": "image_url", "image_url": {"url": url, "detail": detail}})
        return blocks
    else:
        return user_text


message = [
    {"role": "system", "content": sys_prompt}
]

while True:
    image_urls = None
    user_input = input("You: ")

    if is_vision(user_input):
        image_urls = [test_url]

    content = build_user_content(user_input, image_urls=image_urls, detail=detail_response)

    # Add user query to chat
    message.append({"role": "user", "content": content})

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.2-11b-vision-instruct:free",
        messages=message
    )

    assistant_response = completion.choices[0].message.content
    print(assistant_response)
    
    # Add assistant response to chat
    message.append({"role": "assistant", "content": assistant_response})