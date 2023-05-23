import requests


def parse_category_page() -> None:
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

            # Set the parameters for retrieving page content
            content_params = {
                "action": "query",
                "format": "json",
                "titles": page_title,
                "prop": "extracts",
                "explaintext": True,
            }

            # Send a GET request to retrieve the page content
            content_response = requests.get(url, params=content_params)
            content_data = content_response.json()

            # Extract the page content
            pages = content_data["query"]["pages"]
            for _, page_info in pages.items():
                page_title = page_info["title"]
                page_extract = page_info["extract"]

                # Print the page title and plain text extract
                print(f"Page Title: {page_title}")
                print(f"Extract: {page_extract}")
                print()

            # FIXME: This is temporary
            return


def recursive_subcategories():
    # Define the endpoint URL for the Wikipedia API
    url = "https://en.wikipedia.org/w/api.php"

    # Set the parameters for retrieving category members
    category = "Germany"
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": 500,
    }

    # Function to retrieve category members recursively
    def retrieve_category_members(category):
        # Set the category title in the API parameters
        params["cmtitle"] = f"Category:{category}"

        # Send a GET request to the API
        response = requests.get(url, params=params)
        data = response.json()

        # Process the category members
        for member in data["query"]["categorymembers"]:
            if member["ns"] == 14:  # Check if the member is a subcategory
                # Retrieve information from the subcategory page
                subcategory_title = member["title"]
                subcategory_name = subcategory_title.replace("Category:", "")
                print(f"Processing subcategory: {subcategory_name}")

                # Recursively retrieve category members from the subcategory
                retrieve_category_members(subcategory_name)
            else:
                # Process the page within the category
                page_title = member["title"]
                print(f"Processing page: {page_title}")
                # Perform further operations or retrieve page content here


if __name__ == "__main__":
    parse_category_page()
