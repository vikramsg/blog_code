import requests

# Define the endpoint URL for the Wikipedia API
url = "https://en.wikivoyage.org/w/api.php"

# Set the parameters for the API request
params = {
    "action": "query",
    "format": "json",
    "prop": "extracts",
    "titles": "Category:Germany",
    "explaintext": True,
}

# Send a GET request to the API
response = requests.get(url, params=params)
data = response.json()

# Extract the page content for Germany
page_id = next(iter(data["query"]["pages"]))
page_content = data["query"]["pages"][page_id]["extract"]

# Print the page content
print(page_content)
