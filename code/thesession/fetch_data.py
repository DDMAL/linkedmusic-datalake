# This script downloads CSV files containing data from "The Session" (a traditional Irish music community) from a GitHub repository.
"""
Get the newest data from https://github.com/adactio/TheSession-data/tree/main/csv.
"""
import os # The OS module in Python provides a way of using operating system dependent functionality.
import time # The time module provides various time-related functions.
import requests # The requests module allows you to send HTTP requests using Python.
# List of GitHub raw links
github_raw_links = [
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/aliases.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/recordings.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/tune_popularity.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/tunes.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/events.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/sessions.csv",
    "https://raw.githubusercontent.com/adactio/TheSession-data/main/csv/sets.csv"
]
# --
# Defines a list of URLs pointing to raw CSV files on GitHub
# Each URL points to a different dataset file related to traditional Irish music


# Loop through the GitHub raw links and download the files
for link in github_raw_links:
    # Extract the filename from the URL
    filename = link.rsplit("/", maxsplit=1)[-1]
    # Loops through each URL in the list
    # Extracts just the filename part from the URL using rsplit() with a limit of 1 split from the right

    # Construct the complete path to save the file
    save_path = os.path.join('./data/thesession/raw', filename)

    # Send an HTTP GET request to the URL
    response = requests.get(link, timeout=10)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the content of the response to a file
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")
    time.sleep(2)

print("Download complete.")

# This script is a simple data collector that fetches Irish music datasets for further analysis or processing.