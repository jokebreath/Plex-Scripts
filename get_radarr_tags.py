import requests

# Define all the variables used throughout the script that require user input

radarr_address = $RADARR_ADDRESS
plex_address = $PLEX_ADDRESS

radarr_api_key = $RADARR_API_KEY
plex_api_key = $PLEX_API_KEY

radarr_tag = $RADARR_TAG
plex_collection_name = $PLEX_COLLECTION_NAME

# Set the API key for the Radarr server
api_key = radarr_api_key
headers = {
    "X-Api-Key": api_key,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Send a GET request to the Radarr API to retrieve the movie library
response = requests.get(f"{radarr_address}/api/v3/tag/detail?apikey={radarr_api_key}", headers=headers)

# Get the list of movies from the API response
movies = response.json()

# Set an empty list to store the movies with the tag we want and sizeOnDisk not equal to 0
tagged_movies = []

# Loop through the tags in the JSON data
for tag in movies:
    # Check if the tag has the label we want
    if radarr_tag in tag["label"]:
        # Loop through the movie IDs in the tag
        for movie_id in tag["movieIds"]:
            # Send a GET request to the Radarr API to retrieve the movie details
            response = requests.get(f"{radarr_address}/api/v3/movie/{movie_id}", headers=headers)

            # Get the movie details from the API response
            movie = response.json()

            # Check if the sizeOnDisk is not equal to 0
            if movie["sizeOnDisk"] != 0:
                # Add the movie to the list
                tagged_movies.append(movie)

###
# Add Radarr tags to Plex instance
###

# Set the API key for the Plex server
headers = {
    "X-Plex-Token": plex_api_key,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

for movie in tagged_movies:
    # Get the movie title and year
    title = movie["title"]
    year = movie["year"]

    # Search for the movie in the Plex library using the movie title and year
    params = dict(query=title, year=year)
    response = requests.get(f"{plex_address}/search", params=params, headers=headers)
    search_results = response.json()

    # Get the first search result (assumes the movie is in the Plex library)
    try:
        result = search_results["MediaContainer"]["Metadata"][0]
    except(KeyError):
        print(f"{title} ({year}) not found in Plex library.")
        continue

    # Get the ratingKey, title & year for the movie
    movie_id = result["ratingKey"]
    title = result["title"]
    year = result["year"]

    # Send a GET request to the Plex API to retrieve the movie details
    response = requests.get(f"{plex_address}/library/metadata/{movie_id}", headers=headers)

    # Get the movie details from the API response
    movie_details = response.json()

    # Update the list of collections
    in_collection = False

    query_string = ""
    try:
        collections = movie_details["MediaContainer"]["Metadata"][0]["Collection"]

        for collection in collections:
            if collection["tag"] == plex_collection_name:
                in_collection = True
                break

        for i, collection in enumerate(collections):
            query_string += f"collection[{i}].tag.tag={collection['tag']}&"
    except(KeyError): 
        collections = []
        pass
    query_string += f"collection[{len(collections)}].tag.tag={plex_collection_name}"

    if not in_collection:
    # Movie is not in the collection, so add it
        # Send a PUT request to the Plex API to update the movie metadata
        response = requests.put(f"{plex_address}/library/metadata/{movie_id}?{query_string}", headers=headers)

            # Check the status code of the response 
        if response.status_code == 200:
            # Movie was added to the collection successfully
            print(f"ID {movie_id} ({title}, {year}) added to collection '{plex_collection_name}'")
        else:
            # There was an error adding the movie to the collection
            print(f"Error adding ID {movie_id} ({title}, {year}) to collection '{plex_collection_name}'")
    else:
        # Movie is already in the collection
        print(f"ID {movie_id} ({title}, {year}) is already in the collection {plex_collection_name}")
