import tkinter as tk
from tkinter import ttk, messagebox
import pymongo
import subprocess
import os
import csv
from tkinter.filedialog import asksaveasfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import poster_api

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
import numpy as np

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
collection = db["movies"]

# --- USER LOGIN DATA ---
VALID_USERS = {
    "admin": "1234",
    "user": "pass"
}

# --- MAIN GUI ---
def launch_main_app():
    root = tk.Tk()
    root.title("🎮 Movie Recommendation System")
    root.geometry("950x720")

    def refresh_genres():
        all_genres = set()
        for movie in collection.find():
            all_genres.update(movie.get("genres", []))
        genre_combo['values'] = sorted(list(all_genres))

    def recommend_movies():
        result_box.delete(0, tk.END)
        genre = genre_var.get()
        min_rating = rating_var.get()
        query = {"rating": {"$gte": min_rating}}

        if genre:
            query["genres"] = genre
        if title_var.get():
            query["title"] = {"$regex": title_var.get(), "$options": "i"}

        sort_dir = -1 if sort_order.get() else 1
        results = list(collection.find(query).sort("rating", sort_dir).limit(20))

        if not results:
            result_box.insert(tk.END, "No matching movies found.")
            return

        for movie in results:
            result_box.insert(tk.END, f"{movie['title']} | {', '.join(movie['genres'])} | Rating: {movie['rating']}")

        avg = sum(m['rating'] for m in results) / len(results)
        result_box.insert(tk.END, f"\nAverage Rating: {round(avg, 2)}")

    def cluster_similar_movies():
        movies = list(collection.find({}, {"title": 1, "genres": 1, "rating": 1}))
        if not movies:
            messagebox.showwarning("No Data", "Movie database is empty.")
            return

        movies = [m for m in movies if m.get("genres") and m.get("rating") is not None]
        if len(movies) < 5:
            messagebox.showwarning("Insufficient Data", "Need at least 5 movies with genre and rating.")
            return

        titles = [m["title"] for m in movies]
        genres = [", ".join(m["genres"]) for m in movies]
        ratings = [m["rating"] for m in movies]

        vectorizer = CountVectorizer()
        genre_matrix = vectorizer.fit_transform(genres).toarray()

        scaler = MinMaxScaler()
        ratings_scaled = scaler.fit_transform(np.array(ratings).reshape(-1, 1))
        combined = np.hstack((genre_matrix, ratings_scaled))

        imputer = SimpleImputer(strategy='mean')
        combined_clean = imputer.fit_transform(combined)

        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        labels = kmeans.fit_predict(combined_clean)

        selection = result_box.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a movie to find similar ones.")
            return

        selected_title = result_box.get(selection[0]).split(" | ")[0].strip()
        try:
            idx = titles.index(selected_title)
        except ValueError:
            messagebox.showerror("Not Found", "Selected movie not found.")
            return

        selected_cluster = labels[idx]
        similar_movies = [titles[i] for i in range(len(labels)) if labels[i] == selected_cluster and i != idx]

        if similar_movies:
            messagebox.showinfo("🎯 Similar Movies", f"Movies like '{selected_title}':\n\n" + "\n".join(similar_movies))
        else:
            messagebox.showinfo("No Matches", f"No similar movies found for '{selected_title}'.")

    def show_top_movies():
        result_box.delete(0, tk.END)
        for movie in collection.find().sort("rating", -1).limit(5):
            result_box.insert(tk.END, f"🔥 {movie['title']} | Rating: {movie['rating']}")

    def clear_results():
        result_box.delete(0, tk.END)

    def add_new_movie():
        title = new_title.get().strip()
        genres = [g.strip() for g in new_genres.get().split(",") if g.strip()]
        try:
            rating = float(new_rating.get())
        except ValueError:
            messagebox.showerror("Invalid Rating", "Please enter a valid rating between 0.0 and 5.0")
            return

        if not title or not genres:
            messagebox.showerror("Input Error", "Both title and genres are required.")
            return

        collection.insert_one({"title": title, "genres": genres, "rating": rating})
        messagebox.showinfo("Success", f"Movie '{title}' added successfully.")

        new_title.delete(0, tk.END)
        new_genres.delete(0, tk.END)
        new_rating.delete(0, tk.END)
        genre_var.set("")
        title_var.set("")
        rating_var.set(0)

        refresh_genres()
        recommend_movies()

    def delete_selected_movie():
        selection = result_box.curselection()
        if not selection:
            messagebox.showwarning("No selection", "Please select a movie to delete.")
            return

        movie_text = result_box.get(selection[0])
        title = movie_text.split(" | ")[0].strip()

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?")
        if confirm:
            result = collection.delete_one({"title": title})
            if result.deleted_count:
                messagebox.showinfo("Deleted", f"Movie '{title}' deleted successfully.")
                recommend_movies()
                refresh_genres()
            else:
                messagebox.showerror("Error", "Could not delete movie.")

    def export_to_csv():
        data = result_box.get(0, tk.END)
        if not data:
            messagebox.showwarning("No Data", "No recommendations to export.")
            return

        file_path = asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Genres", "Rating"])
                for line in data:
                    parts = line.split(" | ")
                    if len(parts) == 3:
                        writer.writerow(parts)
            messagebox.showinfo("Export Successful", f"Saved to {file_path}")

    def show_movie_details(event):
        selection = result_box.curselection()
        if selection:
            movie_text = result_box.get(selection[0])
            title = movie_text.split(" | ")[0].strip()
            movie = collection.find_one({"title": title})
            if movie:
                info = f"Title: {movie['title']}\nGenres: {', '.join(movie['genres'])}\nRating: {movie['rating']}"
                messagebox.showinfo("Movie Details", info)

    def draw_genre_chart():
        chart_win = tk.Toplevel(root)
        chart_win.title("Genre Frequency Chart")

        genre_count = {}
        for movie in collection.find():
            for g in movie.get("genres", []):
                genre_count[g] = genre_count.get(g, 0) + 1

        sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:10]
        genres, counts = zip(*sorted_genres)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(genres, counts, color="skyblue")
        ax.set_title("Top 10 Genres by Frequency")
        ax.invert_yaxis()

        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_selected_movie_poster():
        selection = result_box.curselection()
        if selection:
            movie_text = result_box.get(selection[0])
            title = movie_text.split(" | ")[0].strip()
            poster_api.show_poster(title)

    tk.Label(root, text="Movie Recommendation System", font=("Arial", 18, "bold")).pack(pady=10)

    sort_order = tk.BooleanVar(value=True)
    tk.Checkbutton(root, text="Sort by Rating (Descending)", variable=sort_order).pack()

    filter_frame = tk.Frame(root)
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Genre:").grid(row=0, column=0)
    genre_var = tk.StringVar()
    genre_combo = ttk.Combobox(filter_frame, textvariable=genre_var, state="readonly", width=20)
    genre_combo.grid(row=0, column=1)

    tk.Label(filter_frame, text="Min Rating:").grid(row=0, column=2)
    rating_var = tk.DoubleVar()
    rating_slider = ttk.Scale(filter_frame, from_=0, to=5, variable=rating_var, orient='horizontal', length=150)
    rating_slider.grid(row=0, column=3)

    tk.Label(filter_frame, text="Title Search:").grid(row=1, column=0, pady=10)
    title_var = tk.StringVar()
    tk.Entry(filter_frame, textvariable=title_var, width=40).grid(row=1, column=1, columnspan=3)

    result_box = tk.Listbox(root, width=100, height=20)
    result_box.pack(pady=10)
    result_box.bind("<Double-1>", show_movie_details)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    buttons = [
        ("🎯 Recommend", recommend_movies, "blue"),
        ("🔥 Top 5 Movies", show_top_movies, "green"),
        ("❌ Clear", clear_results, "red"),
        ("🗑️ Delete Movie", delete_selected_movie, "darkred"),
        ("📤 Export CSV", export_to_csv, "gray"),
        ("📊 Genre Chart", draw_genre_chart, "teal"),
        ("🎯 Cluster Similar", cluster_similar_movies, "orange")
    ]

    for i, (text, cmd, color) in enumerate(buttons):
        tk.Button(btn_frame, text=text, command=cmd, width=15, bg=color, fg="white").grid(row=0, column=i, padx=5)

    tk.Label(root, text="➕ Add New Movie", font=("Arial", 14, "bold")).pack(pady=10)
    add_frame = tk.Frame(root)
    add_frame.pack()

    tk.Label(add_frame, text="Title:").grid(row=0, column=0)
    new_title = tk.Entry(add_frame, width=25)
    new_title.grid(row=0, column=1)

    tk.Label(add_frame, text="Genres (comma):").grid(row=0, column=2)
    new_genres = tk.Entry(add_frame, width=25)
    new_genres.grid(row=0, column=3)

    tk.Label(add_frame, text="Rating:").grid(row=0, column=4)
    new_rating = tk.Entry(add_frame, width=5)
    new_rating.grid(row=0, column=5)

    tk.Button(root, text="Add Movie", command=add_new_movie, bg="purple", fg="white").pack(pady=5)

    tk.Label(root, text="Double-click a movie to view details", fg="gray").pack()

    tk.Button(btn_frame, text="🖼️ Show Poster", command=show_selected_movie_poster, width=15, bg="purple", fg="white").grid(row=1, column=1, padx=5)

    refresh_genres()
    root.mainloop()

# --- LOGIN WINDOW ---
def login_screen():
    login = tk.Tk()
    login.title("Login - Movie Recommendation System")
    login.geometry("350x200")

    tk.Label(login, text="Login", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(login, text="Username:").pack()
    username_entry = tk.Entry(login)
    username_entry.pack()

    tk.Label(login, text="Password:").pack()
    password_entry = tk.Entry(login, show="*")
    password_entry.pack()

    def try_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if VALID_USERS.get(username) == password:
            login.destroy()
            launch_main_app()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    tk.Button(login, text="Login", command=try_login, bg="blue", fg="white").pack(pady=10)

    login.mainloop()

# Run the app
login_screen()
