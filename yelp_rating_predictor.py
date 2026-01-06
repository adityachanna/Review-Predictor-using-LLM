# Yelp Review Rating Predictor
# This script processes 150 samples in batches of 5, with a 10-second delay between API calls

import pandas as pd
import time
from datetime import datetime
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from os import getenv
from dotenv import load_dotenv
from tqdm import tqdm
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
import numpy as np

# Load environment variables
load_dotenv()

# Initialize the model with OpenRouter's base URL
model = init_chat_model(
    model="xiaomi/mimo-v2-flash:free",
    model_provider="openai",
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY")
)

# Load the dataset
print("Loading dataset...")
df = pd.read_csv("yelp.csv")
print(f"Total reviews in dataset: {len(df)}")

# Sample 150 reviews with fixed random state for reproducibility
SAMPLE_SIZE = 150
BATCH_SIZE = 10
DELAY_SECONDS = 10

df_sample = df[['text', 'stars']].sample(n=SAMPLE_SIZE, random_state=42).reset_index(drop=True)
print(f"Sample size: {len(df_sample)}")

# System prompt for rating prediction
prompt = """You are an expert Review Logic Engine specializing in nuanced sentiment analysis.

### MISSION:
Determine the precise 1-5 star rating for restaurant/service reviews by following a strict "Chain of Thought" reasoning process.

### 1. THE REASONING PROTOCOL (Execute this mentally for every review):
Before outputting JSON, you must internally evaluate the following:

**STEP A: SCAN FOR "RATING HINTS" (The Golden Rule)**
- Look for explicit scores: "I give it a 3", "10/10", "Score: 4".
- Look for rounding hints: "3.5 stars", "solid 4.5".
- **RULE:** If a user *explicitly* states a number, that number OVERRIDES all sentiment analysis.
  - *Example:* "Food was trash, service was rude, but I give it 4 stars." -> Result: 4 (User intent rules).

**STEP B: SEGMENT & WEIGH COMPONENTS**
- **Food/Product:** Is it "edible", "good", or "life-changing"?
- **Service:** Is it "slow", "rude" (dealbreaker), or "friendly"?
- **Value/Price:** Is it "overpriced" or "worth it"?
- **Atmosphere:** Is it "dirty" or "vibrant"?

**STEP C: RESOLVE CONFLICTS (The "But" Logic)**
- **Great Food vs. Terrible Service:** Usually results in **2 or 3 Stars**. (Bad service ruins good food).
- **Average Food vs. Amazing Service:** Usually results in **3 or 4 Stars**. (Great service saves a meal).
- **"It was okay/fine":** This is the definition of **3 Stars**.
- **"I wanted to love it but...":** Usually **2 Stars** (Disappointment).

### 2. SCORING DEFINITIONS (Strict Boundaries):
- **1 STAR (Fails):** "Never coming back." Anger, regret, health hazards, or zero redeeming qualities.
- **2 STARS (Poor):** "Disappointing." Had potential, but negatives significantly outweighed positives. A "bad" experience, but not a disaster.
- **3 STARS (Average):** "Decent." Met expectations but didn't exceed them. Or, a balanced mix of great highs and terrible lows.
- **4 STARS (Good):** "Enjoyable." High quality, but had minor nitpicks (e.g., parking, slight wait, price). I would return.
- **5 STARS (Excellent):** "Flawless." Enthusiastic recommendation. If they mention a negative, they immediately dismiss it as irrelevant.

### 3. EDGE CASE HANDLING:
- **Sarcasm Check:** If the text is "Best food ever... NOT!", detect the negative intent.
- **Half-Stars:** If the user says "3.5", round based on tone. (Enthusiastic 3.5 -> 4. Reluctant 3.5 -> 3).
- **Short Reviews:** "It was good." -> 3 or 4 (based on intensity). "It was bad." -> 1 or 2.

### OUTPUT FORMAT:
Return ONLY a valid JSON array. The "explanation" must summarize your *logic*, not just repeat the text.

[
  {{
    "review_index": <int>,
    "predicted_stars": <int>,
    "explanation": "<reasoning>"
  }}
]

### REVIEWS TO CLASSIFY:
{input}
"""
# Create the chat prompt template
chat = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("human", "{input}"),
])

# Initialize JSON parser
output_parser = JsonOutputParser()

# Store all predictions
all_predictions = []
failed_batches = []

# Calculate total number of batches
total_batches = (len(df_sample) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"\n{'='*60}")
print(f"Starting prediction process...")
print(f"Total samples: {SAMPLE_SIZE}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Total batches: {total_batches}")
print(f"Delay between calls: {DELAY_SECONDS} seconds")
print(f"Estimated time: ~{total_batches * DELAY_SECONDS // 60} minutes")
print(f"{'='*60}\n")

start_time = datetime.now()

# Process in batches
for batch_idx in tqdm(range(0, len(df_sample), BATCH_SIZE), desc="Processing batches"):
    batch_num = batch_idx // BATCH_SIZE + 1
    
    # Get current batch of 5 rows
    batch_df = df_sample.iloc[batch_idx : batch_idx + BATCH_SIZE].copy()
    
    # Create the string input: "0: text\n1: text..."
    reviews_input = ""
    for idx, row in enumerate(batch_df.itertuples()):
        reviews_input += f"{idx}: {row.text}\n\n"
    
    try:
        # Invoke the chat template with dynamic batch size
        response = chat.invoke({
            "input": reviews_input,
            "batch_size": len(batch_df)
        })
        
        # Get the model response
        final = model.invoke(response)
        
        # Parse the JSON output
        parsed_output = output_parser.invoke(final.content)
        
        # Map predictions back to sample indices
        # We use a more robust mapping in case the LLM skips indices
        for pred in parsed_output:
            try:
                # Ensure the review_index is valid
                rel_idx = int(pred['review_index'])
                if 0 <= rel_idx < len(batch_df):
                    sample_idx = batch_idx + rel_idx
                    
                    all_predictions.append({
                        'sample_index': sample_idx,
                        'predicted_stars': int(pred['predicted_stars']),
                        'explanation': pred['explanation']
                    })
            except (KeyError, ValueError, TypeError) as e:
                print(f"  Warning: Could not parse prediction in batch {batch_num}: {e}")
        
        print(f"  Batch {batch_num}/{total_batches}: Successfully processed batch results")
        
    except Exception as e:
        print(f"  Batch {batch_num}/{total_batches}: ERROR - {str(e)}")
        failed_batches.append({
            'batch_num': batch_num,
            'start_idx': batch_idx,
            'end_idx': min(batch_idx + BATCH_SIZE, len(df_sample)),
            'error': str(e)
        })
    
    # Add delay between calls to avoid rate limiting (except for the last batch)
    if batch_idx + BATCH_SIZE < len(df_sample):
        time.sleep(DELAY_SECONDS)

end_time = datetime.now()
processing_time = end_time - start_time

print(f"\n{'='*60}")
print(f"Processing completed!")
print(f"Total time: {processing_time}")
print(f"Successful predictions: {len(all_predictions)}")
print(f"Failed batches: {len(failed_batches)}")
print(f"{'='*60}\n")

# Create predictions DataFrame
predictions_df = pd.DataFrame(all_predictions)

# Merge predictions with original sample data
if len(predictions_df) > 0:
    # Add original stars to predictions
    df_sample['sample_index'] = df_sample.index
    
    results_df = df_sample.merge(
        predictions_df, 
        on='sample_index', 
        how='left'
    )
    
    # Calculate the difference between predicted and actual ratings
    results_df['rating_difference'] = results_df['predicted_stars'] - results_df['stars']
    results_df['absolute_difference'] = results_df['rating_difference'].abs()
    
    # Calculate metrics
    print("\n" + "="*60)
    print("RATING COMPARISON ANALYSIS")
    print("="*60)
    
    # Only analyze rows with predictions
    analyzed_df = results_df.dropna(subset=['predicted_stars'])
    
    print(f"\nTotal reviews analyzed: {len(analyzed_df)}")
    
    # Accuracy at different levels
    exact_matches = (analyzed_df['rating_difference'] == 0).sum()
    within_1_star = (analyzed_df['absolute_difference'] <= 1).sum()
    within_2_stars = (analyzed_df['absolute_difference'] <= 2).sum()
    
    print(f"\n--- Accuracy Metrics ---")
    print(f"Exact matches: {exact_matches}/{len(analyzed_df)} ({exact_matches/len(analyzed_df)*100:.1f}%)")
    print(f"Within ±1 star: {within_1_star}/{len(analyzed_df)} ({within_1_star/len(analyzed_df)*100:.1f}%)")
    print(f"Within ±2 stars: {within_2_stars}/{len(analyzed_df)} ({within_2_stars/len(analyzed_df)*100:.1f}%)")
    
    # Average differences
    print(f"\n--- Average Differences ---")
    print(f"Mean Absolute Error (MAE): {analyzed_df['absolute_difference'].mean():.2f} stars")
    print(f"Mean Error (bias): {analyzed_df['rating_difference'].mean():.2f} stars")
    
    # Distribution of differences
    print(f"\n--- Difference Distribution ---")
    diff_counts = analyzed_df['rating_difference'].value_counts().sort_index()
    for diff, count in diff_counts.items():
        sign = "+" if diff > 0 else ""
        print(f"  {sign}{int(diff)} stars: {count} reviews ({count/len(analyzed_df)*100:.1f}%)")
    
    # Comparison by original star rating
    print(f"\n--- Performance by Original Rating ---")
    for star in sorted(analyzed_df['stars'].unique()):
        star_subset = analyzed_df[analyzed_df['stars'] == star]
        if len(star_subset) > 0:
            exact = (star_subset['rating_difference'] == 0).sum()
            mae = star_subset['absolute_difference'].mean()
            print(f"  {star} star reviews: {len(star_subset)} reviews, "
                  f"Exact: {exact} ({exact/len(star_subset)*100:.1f}%), MAE: {mae:.2f}")

    # Detailed Classification Metrics
    print(f"\n--- Classification Report ---")
    y_true = analyzed_df['stars']
    y_pred = analyzed_df['predicted_stars']
    
    report = classification_report(y_true, y_pred, labels=[1, 2, 3, 4, 5], zero_division=0)
    print(report)

    # Calculate weighted metrics for summary
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    
    # Save results to CSV
    output_file = "yelp_rating_predictions.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n✓ Results saved to: {output_file}")
    
    # Also save a summary
    summary_data = {
        'metric': [
            'Total Samples',
            'Successfully Predicted',
            'Failed Batches',
            'Exact Matches',
            'Exact Match %',
            'Within ±1 Star',
            'Within ±1 Star %',
            'Mean Absolute Error',
            'Mean Error (Bias)',
            'Weighted Precision',
            'Weighted Recall',
            'Weighted F1-Score',
            'Processing Time (seconds)'
        ],
        'value': [
            SAMPLE_SIZE,
            len(analyzed_df),
            len(failed_batches),
            exact_matches,
            f"{exact_matches/len(analyzed_df)*100:.1f}%",
            within_1_star,
            f"{within_1_star/len(analyzed_df)*100:.1f}%",
            f"{analyzed_df['absolute_difference'].mean():.2f}",
            f"{analyzed_df['rating_difference'].mean():.2f}",
            f"{precision:.2f}",
            f"{recall:.2f}",
            f"{f1:.2f}",
            f"{processing_time.total_seconds():.0f}"
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_file = "yelp_prediction_summary.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"✓ Summary saved to: {summary_file}")
    
    # Display sample of results
    print(f"\n--- Sample Results (first 10) ---")
    display_cols = ['sample_index', 'stars', 'predicted_stars', 'rating_difference', 'text']
    print(results_df[display_cols].head(10).to_string(max_colwidth=50))

else:
    print("No predictions were successfully made. Please check the error logs above.")

# Print failed batches if any
if failed_batches:
    print(f"\n--- Failed Batches Details ---")
    for batch in failed_batches:
        print(f"  Batch {batch['batch_num']}: indices {batch['start_idx']}-{batch['end_idx']}")
        print(f"    Error: {batch['error'][:100]}...")

print(f"\n{'='*60}")
print("Script completed!")
print(f"{'='*60}")
