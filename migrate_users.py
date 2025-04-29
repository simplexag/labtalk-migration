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

def fetch_users(api_url, HEADERS):
    url = api_url
    #processed_customers = load_processed_customers()
    LABTALK_V2_HEADERS = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    USER_URL = "http://127.0.0.1:8000/accounts/users/"
    
    V1_USER_ACCESS_URL = "https://www.labtalkonline.net/core/api/customeraccesses"

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for user in data.get("results", []):
                new_user = {}
                user_id = user.get("id")  # Adjust if ID field is named differently
                print ("Add user " + str(user_id))
                new_user["username"] = user.get("username")
                new_user["password"] = "WatersAgLab99!"
                new_user["email"] = user.get("email")
                new_user["first_name"] = user.get("first_name")
                new_user["last_name"] = user.get("last_name")
                if SEND_TO_V2:
                    try:
                        #new_user_response = requests.post(USER_URL, json=new_user, headers=LABTALK_V2_HEADERS).json()
                        new_user_response = requests.post(USER_URL, json=new_user, headers=LABTALK_V2_HEADERS)
                        new_user_response.raise_for_status()  # Raise an error for HTTP errors (4xx, 5xx)
                        new_user_response = new_user_response.json()
                    except requests.exceptions.RequestException as e:
                        print(f"Error making request: {e}")
                        new_user_response = None  # Handle the error case gracefully
                        break
                #new_user_id = response.json()["id"]
                ##Get user access from V1
                access = []
                access_url = V1_USER_ACCESS_URL + "?user=" + str(user_id)
                while access_url:
                    access_response = requests.get(access_url, headers=HEADERS)
                    if access_response.status_code == 200:
                        access_data = access_response.json()
                        access.extend(access_data.get("results", []))
                        access_url = access_data.get("next")  # Adjust if the API uses a different pagination format
                    else:
                        print(f"Error {access_response.status_code}: {access_response.text}")
                        break
                V2_CUSTOMER_URL = "http://127.0.0.1:8000/core/customers/?third_party_id="
                V2_CUSTOMER_ACCESS_URL = "http://127.0.0.1:8000/core/customer_access/"
                customer_array=[]
                for v1_access in access:
                    ##Get the custome from V2
                    v1_customer_id = v1_access["customer"]
                    #if SEND_TO_V2 == False:
                    #    v1_customer_id = 157
                    customer_response = requests.get(V2_CUSTOMER_URL + str(v1_customer_id), headers=LABTALK_V2_HEADERS)
                    customer_array.append(customer_response.json()["results"][0]["id"])
                
                new_access = {
                    "user": new_user_response["id"],
                    "customer": customer_array
                }
                if SEND_TO_V2:
                    print ("Add Access to" + str(new_user_response["id"]))
                    new_access_response = requests.post(V2_CUSTOMER_ACCESS_URL, json=new_access, headers=LABTALK_V2_HEADERS).json()

                ##get the customer the user has access to

            url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return []

if __name__ == "__main__":
    #Log into labtalk v2
    LOGIN_DATA = {
        "username": "hunt",
        "password": "psuy2k99!"
    }

    TOKEN_URL = "http://127.0.0.1:8000/api/token/"
    headers = {"Content-Type": "application/json"}
   
    response = requests.post(TOKEN_URL, json=LOGIN_DATA, headers=headers)
    ACCESS_TOKEN = response.json()["access"]
    
    API_URL = "https://www.labtalkonline.net/core/api/users/"
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
        customers = fetch_users(API_URL, HEADERS)
        print(f"Fetched {len(customers)} customers.")
    else:
        print("Failed to authenticate or retrieve CSRF token.")
