from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Initialize model (same as Prediction.py)
model = init_chat_model(
    model="xiaomi/mimo-v2-flash:free",
    model_provider="openai",
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
    temperature=0.1
)

# JSON output parser
parser = JsonOutputParser()

# ===== OVERALL SENTIMENT CHAIN =====
sentiment_system_prompt = """
You are an AI analytics assistant helping a business understand overall customer sentiment.

You will be given a list of recent customer reviews. Each review contains:
- rating: The star rating (1-5)
- review_text: The customer's original feedback
- ai_summary: A concise summary of the review

Your task is to analyze ALL the reviews together and generate:

1. overall_sentiment:
   - Overall sentiment classification: "Positive", "Neutral", "Negative", or "Mixed"
   
2. sentiment_score:
   - A numerical score from 0-100 representing overall satisfaction
   - 0-30: Poor, 31-50: Below Average, 51-70: Average, 71-85: Good, 86-100: Excellent

3. key_themes:
   - A list of 3-5 key themes or patterns you noticed across reviews
   - Each theme should be a short phrase (e.g., "Food quality praised", "Slow service concerns")

4. admin_insight:
   - A 2-3 sentence actionable insight for the business owner
   - Focus on what's working well and what needs immediate attention

Return ONLY valid JSON in this format:
{{
  "overall_sentiment": "<Positive|Neutral|Negative|Mixed>",
  "sentiment_score": <number 0-100>,
  "key_themes": ["<theme1>", "<theme2>", "<theme3>"],
  "admin_insight": "<string>"
}}
"""

sentiment_prompt = ChatPromptTemplate.from_messages([
    ("system", sentiment_system_prompt),
    ("human", "Analyze these recent reviews:\n\n{reviews_data}")
])

# Chain for sentiment analysis
sentiment_chain = sentiment_prompt | model | parser


# ===== RECOMMENDATION PRIORITY CHAIN =====
priority_system_prompt = """
You are an AI assistant helping a business prioritize action items from customer feedback.

You will be given a list of AI-generated recommendations based on customer reviews.

Your task is to:
1. Analyze all recommendations
2. Group similar recommendations together
3. Prioritize them based on:
   - Frequency (how often the issue appears)
   - Impact (how much it affects customer satisfaction)
   - Urgency (how quickly it should be addressed)

Return a prioritized list with:

1. priority_recommendations:
   - A list of 5 prioritized action items
   - Each item should have:
     - action: Clear, specific action to take
     - priority: "Critical", "High", "Medium", or "Low"
     - reason: Brief explanation of why this priority level

2. quick_wins:
   - 2-3 recommendations that can be implemented quickly with high impact

3. long_term_improvements:
   - 2-3 recommendations that require more time/resources but will have significant impact

Return ONLY valid JSON in this format:
{{
  "priority_recommendations": [
    {{
      "action": "<string>",
      "priority": "<Critical|High|Medium|Low>",
      "reason": "<string>"
    }}
  ],
  "quick_wins": ["<action1>", "<action2>"],
  "long_term_improvements": ["<action1>", "<action2>"]
}}
"""

priority_prompt = ChatPromptTemplate.from_messages([
    ("system", priority_system_prompt),
    ("human", "Prioritize these recommendations:\n\n{recommendations_data}")
])

# Chain for priority analysis
priority_chain = priority_prompt | model | parser
