# dashboard.py

import tkinter as tk
from tkinter import messagebox
import pymongo

# MongoDB Setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["movie_db"]
movies_col = db["movies"]
likes_col = db["user_likes"]
tags_col = db["user_tags"]

CURRENT_USER = "user_01"

root = tk.Tk()
root.title("🎬 Movie Dashboard with Tags")
root.geometry("850x650")

# ----------- Functions -----------

def search_movies():
    result_listbox.delete(0, tk.END)
    title = search_var.get().strip()

    if not title:
        messagebox.showwarning("Empty Search", "Please enter a movie title.")
        return

    results = list(movies_col.find({"title": {"$regex": title, "$options": "i"}}))

    if not results:
        result_listbox.insert(tk.END, "No movies found.")
        return

    for movie in results:
        result_listbox.insert(tk.END, f"{movie['title']} | Rating: {movie['rating']}")

def like_selected_movie():
    title = get_selected_title()
    if not title:
        return

    if likes_col.find_one({"user": CURRENT_USER, "title": title}):
        messagebox.showinfo("Already Liked", "You already liked this movie.")
        return

    likes_col.insert_one({"user": CURRENT_USER, "title": title})
    messagebox.showinfo("Liked", f"You liked '{title}'.")
    refresh_like_history()

def get_selected_title():
    selection = result_listbox.curselection()
    if not selection:
        messagebox.showwarning("No selection", "Select a movie first.")
        return None

    movie_text = result_listbox.get(selection[0])
    return movie_text.split(" | ")[0].strip()

def refresh_like_history():
    like_listbox.delete(0, tk.END)
    liked = likes_col.find({"user": CURRENT_USER})
    for entry in liked:
        like_listbox.insert(tk.END, entry["title"])

def tag_movie(tag):
    title = get_selected_title()
    if not title:
        return

    existing = tags_col.find_one({"user": CURRENT_USER, "title": title})
    if existing:
        tags_col.update_one(
            {"user": CURRENT_USER, "title": title},
            {"$set": {"tag": tag}}
        )
    else:
        tags_col.insert_one({"user": CURRENT_USER, "title": title, "tag": tag})

    messagebox.showinfo("Tagged", f"'{title}' tagged as {tag.capitalize()}.")
    show_tags()

def show_tags():
    watched_listbox.delete(0, tk.END)
    towatch_listbox.delete(0, tk.END)

    for tag in tags_col.find({"user": CURRENT_USER}):
        if tag["tag"] == "watched":
            watched_listbox.insert(tk.END, tag["title"])
        elif tag["tag"] == "to_watch":
            towatch_listbox.insert(tk.END, tag["title"])

# ----------- Layout -----------

# Search
tk.Label(root, text="🔎 Search Movie:").pack()
search_frame = tk.Frame(root)
search_frame.pack()

search_var = tk.StringVar()
tk.Entry(search_frame, textvariable=search_var, width=60).pack(side=tk.LEFT, padx=10)
tk.Button(search_frame, text="Search", command=search_movies, bg="blue", fg="white").pack(side=tk.LEFT)

# Results
tk.Label(root, text="Results:").pack(pady=5)
result_listbox = tk.Listbox(root, width=100, height=10)
result_listbox.pack()

# Action Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="❤️ Like", command=like_selected_movie, bg="red", fg="white").grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="📌 Tag as Watched", command=lambda: tag_movie("watched"), bg="green", fg="white").grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="📌 Tag as To Watch", command=lambda: tag_movie("to_watch"), bg="orange", fg="black").grid(row=0, column=2, padx=5)

# Liked Movies
tk.Label(root, text="❤️ Liked Movies").pack(pady=5)
like_listbox = tk.Listbox(root, width=100, height=6)
like_listbox.pack()

# Tags Section
tags_frame = tk.Frame(root)
tags_frame.pack(pady=10)

# Watched
tk.Label(tags_frame, text="🎬 Watched").grid(row=0, column=0)
watched_listbox = tk.Listbox(tags_frame, width=40, height=6)
watched_listbox.grid(row=1, column=0, padx=10)

# To Watch
tk.Label(tags_frame, text="📺 To Watch").grid(row=0, column=1)
towatch_listbox = tk.Listbox(tags_frame, width=40, height=6)
towatch_listbox.grid(row=1, column=1, padx=10)

# Refresh
tk.Button(root, text="🔁 Refresh Tags", command=show_tags, bg="purple", fg="white").pack(pady=5)

# Init
refresh_like_history()
show_tags()

root.mainloop()
