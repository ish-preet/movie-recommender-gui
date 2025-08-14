import os
import csv
import pymongo
from collections import defaultdict
from pprint import pprint

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_CSV = os.path.join(SCRIPT_DIR, "movies.csv")
RATINGS_CSV = os.path.join(SCRIPT_DIR, "rating.csv")

# --- Debug: Verify Files Exist ---
print("\n=== DEBUG: Checking Files ===")
print(f"Script directory: {SCRIPT_DIR}")
print(f"Looking for movies at: {MOVIES_CSV}")
print(f"Looking for ratings at: {RATINGS_CSV}")
print("Files in directory:", os.listdir(SCRIPT_DIR))

if not all(os.path.exists(f) for f in [MOVIES_CSV, RATINGS_CSV]):
    print("\n❌ ERROR: Missing CSV files!")
    exit(1)

# --- MongoDB Setup ---
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
collection = db["movies"]
collection.delete_many({})  # Clear old data

# --- Step 1: Process Ratings ---
print("\n=== Processing Ratings CSV ===")
ratings_sum = defaultdict(float)
ratings_count = defaultdict(int)

try:
    with open(RATINGS_CSV, encoding='utf-8') as rfile:
        reader = csv.DictReader(rfile)
        for i, row in enumerate(reader, 1):
            try:
                movie_id = int(row["movieId"])
                rating = float(row["rating"])
                ratings_sum[movie_id] += rating
                ratings_count[movie_id] += 1
            except (ValueError, KeyError) as e:
                print(f"⚠️ Skipping bad row {i}: {e}")
                continue

    avg_ratings = {
        mid: round(ratings_sum[mid] / ratings_count[mid], 2)
        for mid in ratings_sum
    }
    print(f"✅ Processed ratings for {len(avg_ratings)} movies")

except Exception as e:
    print(f"\n❌ Failed to process ratings: {e}")
    exit(1)

# --- Step 2: Process Movies ---
print("\n=== Processing Movies CSV ===")
movies_without_ratings = 0
inserted_count = 0

try:
    with open(MOVIES_CSV, encoding='utf-8') as mfile:
        reader = csv.DictReader(mfile)
        for row in reader:
            try:
                movie_id = int(row["movieId"])
                title = row["title"]
                genres = row["genres"].split("|") if row["genres"] else []
                
                # Get rating or mark as None if missing
                if movie_id in avg_ratings:
                    rating = avg_ratings[movie_id]
                else:
                    rating = None
                    movies_without_ratings += 1

                movie_doc = {
                    "movieId": movie_id,
                    "title": title,
                    "genres": genres,
                    "rating": rating
                }

                collection.insert_one(movie_doc)
                inserted_count += 1

            except Exception as e:
                print(f"⚠️ Skipping bad movie row: {e}")
                continue

except Exception as e:
    print(f"\n❌ Failed to process movies: {e}")
    exit(1)

# --- Results ---
print("\n=== Final Results ===")
print(f"✅ Successfully inserted {inserted_count} movies")
print(f"⚠️  {movies_without_ratings} movies had no ratings")

# Sample output from MongoDB
print("\nSample movies from database:")
for movie in collection.find().limit(5):
    pprint(movie)

print("\nOperation completed!")