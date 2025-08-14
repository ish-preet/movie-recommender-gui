from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
from pymongo import MongoClient
import numpy as np

client = MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
collection = db["movies"]

def perform_clustering(k=3):
    movies = list(collection.find())

    if not movies:
        print("❌ No movies found in database.")
        return

    titles = [movie['title'] for movie in movies]
    genres = [movie.get('genres', []) if movie.get('genres') else [] for movie in movies]
    ratings = [movie.get('rating', 0.0) if movie.get('rating') is not None else 0.0 for movie in movies]

    # Convert genres to one-hot encoding
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(genres)

    # Combine genre features + rating
    features = np.hstack((genre_matrix, np.array(ratings).reshape(-1, 1)))

    # Replace NaNs with 0 (safe fallback)
    features = np.nan_to_num(features, nan=0.0)

    # Standardize
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # KMeans clustering
    kmeans = KMeans(n_clusters=k, random_state=42)
    clusters = kmeans.fit_predict(features_scaled)

    # Save cluster label in DB
    for i, movie in enumerate(movies):
        collection.update_one(
            {"_id": movie["_id"]},
            {"$set": {"cluster": int(clusters[i])}}
        )

    print(f"✅ Assigned movies to {k} clusters.")

if __name__ == "__main__":
    perform_clustering(k=4)
