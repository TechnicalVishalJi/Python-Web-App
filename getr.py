import requests

def make_get_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Successful GET request
            return response.text
        else:
            # Handle non-200 status codes
            return f"Error: {response.status_code}"
    except requests.RequestException as e:
        # Handle exceptions
        return f"Request Exception: {str(e)}"

# Example usage
external_url = 'https://google.com/jd'
response_text = make_get_request(external_url)
print(response_text)
