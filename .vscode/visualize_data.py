import pymongo
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set theme
sns.set(style="whitegrid")

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
collection = db["movies"]

# Load data into Pandas DataFrame
movies = list(collection.find())
df = pd.DataFrame(movies)

# Drop missing/invalid rows
df.dropna(subset=["genres", "rating"], inplace=True)

# Explode genres list to rows
df_exploded = df.explode("genres")

# -------------------------
# 1. Genre Distribution Pie Chart
# -------------------------
genre_counts = df_exploded["genres"].value_counts().head(10)
plt.figure(figsize=(8, 8))
genre_counts.plot.pie(autopct="%1.1f%%", startangle=140)
plt.title("Top 10 Genres Distribution")
plt.ylabel("")
plt.tight_layout()
plt.savefig("genre_distribution.png")
plt.show()

# -------------------------
# 2. Average Rating per Genre
# -------------------------
avg_ratings = df_exploded.groupby("genres")["rating"].mean().sort_values(ascending=False).head(10)
plt.figure(figsize=(10, 5))
sns.barplot(x=avg_ratings.values, y=avg_ratings.index, palette="viridis")
plt.title("Top 10 Genres by Average Rating")
plt.xlabel("Average Rating")
plt.ylabel("Genre")
plt.tight_layout()
plt.savefig("avg_rating_per_genre.png")
plt.show()

# -------------------------
# 3. Top Rated Movies Overall
# -------------------------
top_movies = df.sort_values(by="rating", ascending=False).head(10)
plt.figure(figsize=(10, 5))
sns.barplot(x=top_movies["rating"], y=top_movies["title"], palette="magma")
plt.title("Top 10 Rated Movies")
plt.xlabel("Rating")
plt.ylabel("Movie Title")
plt.tight_layout()
plt.savefig("top_movies.png")
plt.show()
