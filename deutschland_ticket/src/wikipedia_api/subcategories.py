import requests

# Define the endpoint URL for the Wikipedia API
url = "https://en.wikivoyage.org/w/api.php"

# Set the parameters for retrieving category members
category = "Germany"
params = {
    "action": "query",
    "format": "json",
    "list": "categorymembers",
    "cmtitle": f"Category:{category}",
    "cmlimit": 500,
}

# Send a GET request to the API
response = requests.get(url, params=params)
data = response.json()

# Process the sub-categories
for member in data["query"]["categorymembers"]:
    if member["ns"] == 14:  # Check if the member is a sub-category
        # Process the sub-category
        subcategory_title = member["title"]
        subcategory_name = subcategory_title.replace("Category:", "")
        print(f"Processing sub-category: {subcategory_name}")
        # Perform further operations or retrieve page content for the sub-category here
    if member["ns"] == 0:  # Check if the member is a page
        # Process the page
        page_title = member["title"]
        print(f"Processing page: {page_title}")
        # Perform further operations or retrieve page content for the sub-category here
