# Review Analysis Project

This project consists of two main components:

## Project Structure

```
Key/
├── task1/                  # Data Analysis & Evaluation
│   ├── Task_Eval.ipynb    # Main evaluation notebook
│   ├── Notebook.ipynb     # Additional analysis notebook
│   ├── yelp.csv           # Original Yelp dataset
│   ├── yelp_rating_predictions.csv      # Prediction results
│   ├── yelp_prediction_summary.csv      # Summary statistics
│   ├── output.png         # Visualization output
│   └── yelp_rating_predictor.py         # Batch prediction script
│
├── back-end/              # FastAPI Backend Application
│   ├── main.py           # FastAPI application entry point
│   ├── api.py            # API routes and endpoints
│   ├── models.py         # SQLAlchemy database models
│   ├── database.py       # Database connection setup
│   ├── schemas.py        # Pydantic response schemas
│   ├── Prediction.py     # LangChain prediction chain
│   ├── analytics.py      # Analytics chains (sentiment & recommendations)
│   └── requirements.txt  # Python dependencies
│
├── .env                  # Environment variables (database, API keys)
└── .gitignore           # Git ignore rules
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd back-end
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with:

```env
# Database Configuration
user=postgres
password=YOUR_SUPABASE_PASSWORD
host=db.qibdynpydojobdnkkxbc.supabase.co
port=5432
dbname=postgres

# OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Run the Backend Server

```bash
cd back-end
python main.py
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs
- **Base URL**: http://localhost:8000

## API Endpoints

### User Endpoints
- `POST /api/reviews` - Submit a new review

### Admin Analytics Endpoints
- `GET /api/analytics/sentiment` - Overall sentiment analysis (last 20 reviews)
- `GET /api/analytics/recommendations` - Priority recommendations list (last 50)
- `GET /api/analytics/ratings` - All ratings data for visualization

## Task 1: Data Analysis

The `task1` folder contains:
- Jupyter notebooks for evaluating different prompting approaches
- Yelp dataset and prediction results
- Batch processing scripts for rating predictions

To run the analysis:
```bash
cd task1
jupyter notebook Task_Eval.ipynb
```

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **LLM Framework**: LangChain
- **LLM Provider**: OpenRouter (xiaomi/mimo-v2-flash)
- **Data Analysis**: pandas, numpy, scikit-learn
