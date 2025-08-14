import requests
from duckduckgo_search import DDGS
from PIL import Image
from io import BytesIO

def download_poster(title):
    try:
        print(f"🔍 Searching poster for: {title}")

        # Use DuckDuckGo search
        with DDGS() as ddgs:
            results = list(ddgs.images(title + " movie poster", max_results=1))
            if not results:
                print("❌ No image results found.")
                return
            url = results[0]['image']
            print(f"✅ Poster URL: {url}")

        # Fix TMDB host if needed
        if "themoviedb.org/t/p" in url:
            url = url.replace("www.themoviedb.org/t/p", "image.tmdb.org/t/p")
            print(f"🔁 Fixed TMDB URL: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        img.verify()
        img = Image.open(BytesIO(response.content))

        img.show()
        filename = f"{title.replace(' ', '_')}_poster.jpg"
        img.save(filename)
        print(f"💾 Poster saved as: {filename}")

    except Exception as e:
        print("⚠️ Error fetching poster:", e)

# Test
if __name__ == "__main__":
    download_poster("Nixon (1995)")
