import subprocess
import json

# List of URLs to fetch JSON-LD from
urls = [
    #overlap the session
    'https://musicbrainz.org/release/20027ad4-6667-49b6-bd07-5ac12d57f8dd', #cooleys reels
    "https://musicbrainz.org/release/4c9190a2-6098-41f4-bbbf-7e9d41e3539e/disc/1#066d7ff5-9df1-4277-9a6b-aa9baed6fe48", #just piping (in the session)

    #overlap simssadb
    "https://musicbrainz.org/release/a1ede063-6042-49da-9d82-0e928074649f", #ave maria by sue ann pinner
    "https://musicbrainz.org/release/cd5d7022-84e0-4ba2-86aa-9272dec2f210/disc/1#f4d5d16c-5a91-4fb6-a8bf-e0461089b67f", #alpine airs: music of switzerland, 13th-16th centuries

    #overlap cantusdb
    "https://musicbrainz.org/release/cd3e5b98-c384-41fe-8171-ae91bc24b278/disc/2#f05ed215-eecf-456c-a91d-1ac3bdc6091d", # renaissance masterpieces
    "https://musicbrainz.org/release/f0b0bd94-9743-4114-98c1-9d4dd8ab95cc/disc/1#3b41dd32-2c84-4fb8-9051-313393f25058", #croisade

    #random ones
    "https://musicbrainz.org/release/d6010be3-98f8-422c-a6c9-787e2e491e58", #abbey road -  the beatles
    "https://musicbrainz.org/release/2b52af44-db64-4055-9c1b-ad94080400ba", #julie is her name - julie london
    "https://musicbrainz.org/release/6c3d4577-b205-4719-a63d-fa2d5ef4aa68", #debussy, ravel; the philadelphia orchestra,...
    "https://musicbrainz.org/release/023abf42-e340-4a45-84d1-1fc95eaa46e9", #in rainbows: from the basement - radiohead
    "https://musicbrainz.org/release/46637412-a759-4fd2-bdce-9340be3675e4", #street by street (single) - laufey

]
jsonld_responses = []

    


# Loop through the list of URLs and fetch JSON-LD
for idx, url in enumerate(urls):
    try:
        # Define the curl command for the current URL
        curl_command = ['curl','-H','Accept: application/ld+json',url]

        # Execute the curl command and capture the output
        output = subprocess.check_output(curl_command, text=True)
        print(output)
        # Parse the JSON-LD response
        jsonld_data = json.loads(output)
        

        # add them all to a list
        jsonld_responses.append(jsonld_data) 

    except subprocess.CalledProcessError as e:
        # Handle errors if the curl command fails
        print(f"Error fetching JSON-LD from {url}: {e}")


with open("data/initial.jsonld", 'w', encoding='utf-8') as outfile:
    json.dump(jsonld_responses, outfile, indent=2)