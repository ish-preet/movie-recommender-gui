from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import difflib

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
collection = db["movies"]

# Load data from MongoDB
movies = list(collection.find())

# Check if we have movies
if not movies:
    print("⚠️ No movies found in the database. Please add some first.")
    exit()

# Convert to DataFrame
df = pd.DataFrame(movies)

# Drop rows without genres or non-lists
df = df[df['genres'].map(lambda x: isinstance(x, list))].copy()

# Check if anything is left
if df.empty:
    print("⚠️ No valid movies with genre data found. Please check your database.")
    exit()

# Combine genres into a single string
df["genre_text"] = df["genres"].apply(lambda g: " ".join(g).lower())

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(df["genre_text"])

# Cosine similarity matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Map titles to DataFrame indices
indices = pd.Series(df.index, index=df['title']).drop_duplicates()

# 🎯 Recommend similar movies
def recommend(title, top_n=5):
    all_titles = list(indices.keys())
    
    # Fuzzy match to find closest movie title
    closest = difflib.get_close_matches(title, all_titles, n=1, cutoff=0.6)
    if not closest:
        print(f"❌ No similar movie found for '{title}'.")
        print("✅ Available titles:", all_titles[:10], "...")
        return []

    matched_title = closest[0]
    print(f"✅ Using closest match: '{matched_title}'")

    idx = indices[matched_title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
    movie_indices = [i[0] for i in sim_scores]

    return df.iloc[movie_indices][["title", "genres", "rating"]].to_dict("records")


if __name__ == "__main__":
    movie_name = input("🎬 Enter a movie name to get recommendations: ").strip()
    results = recommend(movie_name)

    print(f"\n🎯 Top recommendations for '{movie_name}':")
    if results:
        for r in results:
            print(f"- {r['title']} | Genres: {', '.join(r['genres'])} | Rating: {r['rating']}")
    else:
        print("No recommendations found.")
