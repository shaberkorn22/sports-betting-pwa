import os
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

def fetch_odds():
    """
    Fetch odds data from a public API specified by THE_ODDS_API_BASE_URL and THE_ODDS_API_KEY.
    Returns a list of event dictionaries. This function combines data across multiple sports.
    """
    api_key = os.environ.get('THE_ODDS_API_KEY')
    base_url = os.environ.get('THE_ODDS_API_BASE_URL', 'https://api.the-odds-api.com/v4/sports/')
    sports = ['basketball_nba', 'americanfootball_nfl', 'baseball_mlb', 'mixed_martial_arts_mma']
    events = []
    for sport in sports:
        url = f"{base_url}{sport}/odds/?apiKey={api_key}&regions=us&markets=h2h,spreads,totals"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                events += resp.json()
            else:
                print(f"API error for {sport}: {resp.status_code}")
        except Exception as e:
            print(f"Error fetching {sport}: {e}")
    return events

def transform_events(events):
    """
    Transform raw event dictionaries into a pandas DataFrame with basic features for modelling.
    """
    records = []
    for event in events:
        sport_key = event.get('sport_key')
        for bookmaker in event.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                for outcome in market.get('outcomes', []):
                    record = {
                        'sport_key': sport_key,
                        'market_key': market.get('key'),
                        'team': outcome.get('name'),
                        'price': outcome.get('price'),
                        'point': outcome.get('point'),
                        'timestamp': pd.Timestamp.utcnow(),
                    }
                    records.append(record)
    return pd.DataFrame(records)

def train_simple_model(df):
    """
    Train a simple logistic regression model to classify favourable bets.
    We use a simplistic target where negative prices imply favourites.
    """
    df = df.dropna(subset=['price'])
    df['target'] = (df['price'] < 0).astype(int)
    X = df[['price']].values
    y = df['target'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression()
    model.fit(X_train, y_train)
    print(f"Training accuracy: {model.score(X_test, y_test):.3f}")
    return model

def select_picks(model, df):
    """
    Use the trained model to generate pick recommendations based on predicted probability.
    Returns a DataFrame with sport_key, market_key, pick, confidence and timestamp.
    """
    probabilities = model.predict_proba(df[['price']].values)[:, 1]
    df = df.copy()
    df['confidence'] = probabilities
    picks = df[df['confidence'] > 0.6].copy()
    picks['pick'] = picks['team']
    return picks[['sport_key', 'market_key', 'pick', 'confidence', 'timestamp']]

def save_to_db(df_raw, df_picks):
    """
    Save raw odds data and generated picks into PostgreSQL tables raw_odds and picks.
    Tables will be created if they do not exist.
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL provided; skipping database save.")
        return
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_odds (
            id SERIAL PRIMARY KEY,
            sport_key TEXT,
            market_key TEXT,
            team TEXT,
            price FLOAT,
            point FLOAT,
            timestamp TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id SERIAL PRIMARY KEY,
            sport_key TEXT,
            market_key TEXT,
            pick TEXT,
            confidence FLOAT,
            timestamp TIMESTAMP
        );
    """)
    # Insert raw data
    for _, row in df_raw.iterrows():
        cur.execute(
            "INSERT INTO raw_odds (sport_key, market_key, team, price, point, timestamp) VALUES (%s,%s,%s,%s,%s,%s)",
            (row['sport_key'], row['market_key'], row['team'], row['price'], row['point'], row['timestamp'])
        )
    # Insert picks
    for _, row in df_picks.iterrows():
        cur.execute(
            "INSERT INTO picks (sport_key, market_key, pick, confidence, timestamp) VALUES (%s,%s,%s,%s,%s)",
            (row['sport_key'], row['market_key'], row['pick'], row['confidence'], row['timestamp'])
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved {len(df_raw)} raw records and {len(df_picks)} picks to the database.")

def main():
    events = fetch_odds()
    if not events:
        print("No events fetched; exiting.")
        return
    df_raw = transform_events(events)
    model = train_simple_model(df_raw)
    df_picks = select_picks(model, df_raw)
    save_to_db(df_raw, df_picks)

if __name__ == '__main__':
    main()
