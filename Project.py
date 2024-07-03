import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import logging

def search_movie(movie_name):
    # IMDb search URL
    search_url = f"https://www.imdb.com/find/?q={movie_name}&ref_=nv_sr_sm"

    # Set custom headers with a user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }

    # Send a GET request to the IMDb search URL with custom headers
    response = requests.get(search_url, headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")

        # Find search results
        results = soup.find_all("a", class_="ipc-metadata-list-summary-item__t")

        # Filter results containing the searched word
        filtered_results = []
        for result in results:
            parent = result.parent
            if parent:
                # Extract title, year, and href_id from parent element
                title = result.text.strip()
                year_element = parent.find("span", class_="ipc-metadata-list-summary-item__li")
                year = year_element.text.strip() if year_element else "N/A"
                href = result.get('href')  # Get the href attribute value
                filtered_results.append({"title": title, "year": year, "href": href})

        if not filtered_results:
            messagebox.showinfo("Info", f"No movies found containing '{movie_name}'.")
            return []

        # Return filtered movie titles with their years and href_ids
        return filtered_results
    else:
        messagebox.showerror("Error", f"Failed to fetch search results. Status code: {response.status_code}")
        return []

def get_movie_details(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }

    # Send a GET request to the movie URL with custom headers
    response = requests.get(movie_url, headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract director's name
        director_element = soup.find("span", class_="ipc-metadata-list-item__label", string="Director")
        director = director_element.find_next("a", class_="ipc-metadata-list-item__list-content-item--link").text.strip() if director_element else "N/A"

        # Extract top 3 cast members' names
        cast = []
        cast_container = soup.find("div", class_="ipc-metadata-list-item__content-container")
        cast_elements = cast_container.find_all("a", class_="ipc-metadata-list-item__list-content-item--link")
        for cast_element in cast_elements:
            cast.append(cast_element.text.strip())

        return {"director": director, "cast": cast[:3]}  # Return top 3 cast members
    else:
        messagebox.showerror("Error", f"Failed to fetch movie details. Status code: {response.status_code}")
        return {}

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calculate_average_rating(director_href, html_content):
    # Initialize a list to store movie ratings
    ratings = []

    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all <span> elements containing ratings
    rating_spans = soup.find_all("span")

    # Extract ratings from each <span> element
    previous_rating = None
    for span in rating_spans:
        # Check if the <span> contains a rating
        text = span.text.strip()
        if '.' in text and text.replace('.', '', 1).isdigit():
            rating = float(text)
            # Filter out ratings above 10 and remove immediate duplicates
            if rating <= 10 and rating != previous_rating:
                ratings.append(rating)
                previous_rating = rating
                logger.debug(f"Found rating: {rating}")

    # Calculate average rating
    if ratings:
        average_rating = sum(ratings) / len(ratings)
        logger.debug(f"All ratings: {ratings}")
        return round(average_rating, 1)
    else:
        return "N/A"

def show_movie_details(href_id):
    # IMDb movie URL
    movie_url = f"https://www.imdb.com{href_id}"
    print("Movie URL:", movie_url)  # Debug print

    # Set custom headers with a user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }

    # Send a GET request to the movie URL with custom headers
    response = requests.get(movie_url, headers=headers)

    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract director's name and href
        director_element = soup.find("span", class_="ipc-metadata-list-item__label", string="Director")
        director = director_element.find_next("a", class_="ipc-metadata-list-item__list-content-item--link") if director_element else None
        director_name = director.text.strip() if director else "N/A"
        director_href = director["href"] if director else None

        if director_href:
            # Send a GET request to the director's IMDb page to get the HTML content
            director_response = requests.get(f"https://www.imdb.com{director_href}", headers=headers)

            # Check if request to director's IMDb page was successful
            if director_response.status_code == 200:
                # Calculate average rating using director's IMDb page HTML content
                average_rating = calculate_average_rating(director_href, director_response.content)
                print("Average Rating:", average_rating)  # Debug print
               
                # Open a new pop-up window to display the predicted rating
                messagebox.showinfo("Predicted Score", f"The Predicted Rating for this Movie is {average_rating}.")

            else:
                print(f"Failed to fetch director's IMDb page. Status code: {director_response.status_code}")
                average_rating = "N/A"
        else:
            print("Director's page URL not found.")
            average_rating = "N/A"

        # Extract top 3 cast members' names
        cast = []
        cast_container = soup.find("div", class_="ipc-metadata-list-item__content-container")
        cast_elements = cast_container.find_all("a", class_="ipc-metadata-list-item__list-content-item--link")
        for cast_element in cast_elements:
            cast.append(cast_element.text.strip())

        return {"director": director_name, "cast": cast[:3], "average_rating": average_rating}  # Return top 3 cast members and average rating
    else:
        print(f"Failed to fetch movie details. Status code: {response.status_code}")
        return {}

def search_movie_and_display():
    # Clear previous search results
    for widget in result_frame.winfo_children():
        widget.destroy()

    movie_name = entry.get()
    search_results = search_movie(movie_name)
    if search_results:
        for i, movie in enumerate(search_results):
            movie_title = movie["title"]
            year = movie["year"]
            href = movie["href"]
            # Check if the year contains any text
            if not any(char.isalpha() for char in year):
                button = ttk.Button(result_frame, text=f"{movie_title} ({year})", command=lambda h=href: show_movie_details(h))
                button.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
    else:
        messagebox.showinfo("Info", f"No movies found containing '{movie_name}'.")

# Create the main window
root = tk.Tk()
root.title("Movie Search")

# Create a frame to contain widgets
frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create a label and entry for searching movie
search_label = ttk.Label(frame, text="Enter Movie Name:")
search_label.grid(row=0, column=0)

entry = ttk.Entry(frame, width=30)
entry.grid(row=0, column=1)

# Create a button to trigger the search
search_button = ttk.Button(frame, text="Search", command=search_movie_and_display)
search_button.grid(row=0, column=2, padx=(10, 0))

# Create a frame to display search results
result_frame = ttk.Frame(frame, padding="10")
result_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))

# Start the main event loop
root.mainloop()