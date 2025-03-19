import requests, json, os

SEND_TO_V2 = True

ACCESS_TOKEN = ""

def login_and_get_csrf(session, login_url, credentials):
    """Log in to get session and CSRF token."""
    response = session.post(login_url, data=credentials)
    return json.loads(response.text)["token"]

"""
def load_processed_customers():
    #Load processed customer IDs from file.
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()
"""

def fetch_customers(api_url, HEADERS):
    customers = []
    url = api_url
    #processed_customers = load_processed_customers()
    LABTALK_V2_HEADERS = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    CUSTOMER_URL = "http://127.0.0.1:8000/core/customers/"

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for customer in data.get("results", []):
                new_customer = {}
                customer_id = customer.get("id")  # Adjust if ID field is named differently
                print (customer_id)
                new_customer["name"] = customer.get("name")
                new_customer["third_party_id"] = customer.get("id")
                new_customer["address_1"] = customer.get("address_1")
                new_customer["address_2"] = customer.get("address_2")
                new_customer["city"] = customer.get("city")
                new_customer["state"] = customer.get("state")
                new_customer["zipcode"] = customer.get("zipcode")
                if SEND_TO_V2:
                    response = requests.post(CUSTOMER_URL, json=new_customer, headers=LABTALK_V2_HEADERS)
            url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return customers

if __name__ == "__main__":
    #Log into labtalk v2
    LOGIN_DATA = {
        "username": "admin",
        "password": "admin99!"
    }

    TOKEN_URL = "http://127.0.0.1:8000/api/token/"
    headers = {"Content-Type": "application/json"}
    if SEND_TO_V2:
        response = requests.post(TOKEN_URL, json=LOGIN_DATA, headers=headers)
        ACCESS_TOKEN = response.json()["access"]
    
    API_URL = "https://www.labtalkonline.net/core/api/customers"
    LOGIN_URL = "https://www.labtalkonline.net/api-token-auth/"  # Adjust login endpoint

    session = requests.Session()
    
    credentials = {
        "username": "labtalkadmin",
        "password": "Labtalk99!"
    }

    csrf_token = login_and_get_csrf(session, LOGIN_URL, credentials)

    if csrf_token:
        """
        HEADERS = {
            "accept": "application/json",
            "X-CSRFToken": csrf_token
        }
        """
        HEADERS = {
            "accept": "application/json",
            "Authorization": f"Token {csrf_token}"  # Use 'Token' before the actual token
        }
        customers = fetch_customers(API_URL, HEADERS)
        print(f"Fetched {len(customers)} customers.")
    else:
        print("Failed to authenticate or retrieve CSRF token.")
