from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Initialize model (OpenRouter)
model = init_chat_model(
    model="xiaomi/mimo-v2-flash:free",
    model_provider="openai",
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
    temperature=0.1
)

# JSON output parser
parser = JsonOutputParser()

# SYSTEM PROMPT (instructions only)
system_prompt = """
You are an AI assistant helping a business analyze customer feedback.

You will be given:
- A star rating (1–5)
- A user-written review (may be very short, unclear, repetitive, or low-quality text)

Your task is to generate THREE things:

1. ai_summary:
   - A concise, neutral, one-sentence summary of what the user experienced.
   - Written for internal (admin) use.
   - If the review text is unclear or low-information, summarize primarily from the rating.

2. ai_recommended_action:
   - One clear, actionable recommendation for the business.
   - Written for internal (admin) use.
   - If the review lacks details, suggest monitoring or maintaining quality.

3. ai_user_response:
   - A short, polite, empathetic message addressed directly to the user.
   - Do NOT mention internal analysis.
   - Tone should align with the rating.

Return ONLY valid JSON in this format:
{{
  "ai_summary": "<string>",
  "ai_recommended_action": "<string>",
  "ai_user_response": "<string>"
}}
"""

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Rating: {rating}\nReview: {review}")
])

# Chain = prompt → model → JSON parser
chain = prompt | model | parser
