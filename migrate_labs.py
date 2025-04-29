import requests, json, os

SEND_TO_V2 = True
V1_HEADERS = ""
ACCESS_TOKEN = ""
V2_HEADERS = ""
V1_LAB_API_URL = "https://www.labtalkonline.net/core/api/labs/"
V2_LAB_API_URL = "http://127.0.0.1:8000/reference/labs/"


def login_and_get_csrf(session, login_url, credentials):
    """Log in to get session and CSRF token."""
    response = session.post(login_url, data=credentials)
    return json.loads(response.text)["token"]


##Get labs
def fetch_labs():

    url = V1_LAB_API_URL
    labs = []
    while url:
        response = requests.get(V1_LAB_API_URL, headers=V1_HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for lab in data.get("results", []):
                new_lab = {}
                new_lab["name"] = lab.get("name")
                new_lab["third_party_id"] = lab.get("id")
                new_lab["address_1"] = lab.get("address_1")
                new_lab["address_2"] = lab.get("address_2")
                new_lab["city"] = lab.get("city")
                new_lab["state"] = lab.get("state")
                new_lab["zipcode"] = lab.get("zipcode")
                if SEND_TO_V2:
                    response2 = requests.post(V2_LAB_API_URL, json=new_lab, headers=V2_HEADERS)
                    labs.append(response2.json())
                else:
                    labs = [{'id': '6bc5da23-07fc-44dc-84c0-7c158fbfe146', 'name': 'Camilla - M1', 'third_party_id': '1', 'address_1': '257 Newton Highway', 'address_2': None, 'city': 'Camilla', 'state': 'GA', 'zipcode': '31730', 'phone': None}, {'id': 'f9fbe352-741a-45d2-8ca2-b5c006531907', 'name': 'Camilla - M3', 'third_party_id': '5', 'address_1': '257 Newton Highway', 'address_2': None, 'city': 'Camilla', 'state': 'GA', 'zipcode': '31730', 'phone': None}, {'id': '0be1d7b9-ee7b-47be-86b5-ff0f8465fadb', 'name': 'Owensboro', 'third_party_id': '2', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': '2b8085ba-9e6b-4718-b97d-f2f120749ef7', 'name': 'Owensboro - Bray', 'third_party_id': '6', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': 'dd4074ad-0c05-45c6-9bc1-ab145354e444', 'name': 'Owensboro - M1', 'third_party_id': '8', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': 'd4ae26b1-a8f9-4868-8f9a-14e1768f34d1', 'name': 'Owensboro - Olsen', 'third_party_id': '7', 'address_1': None, 'address_2': None, 'city': None, 'state': None, 'zipcode': None, 'phone': None}, {'id': '850ff4ca-8d3a-4250-9a41-b162eb130c5d', 'name': 'Vicksburg', 'third_party_id': '4', 'address_1': '4589 Highway 61 South', 'address_2': None, 'city': 'Vicksburg', 'state': 'MS', 'zipcode': '39180', 'phone': None}, {'id': '00791f22-c9aa-47ec-ba8b-80a8c773ac2a', 'name': 'Warsaw', 'third_party_id': '3', 'address_1': '364 W. Park Drive', 'address_2': None, 'city': 'Warsaw', 'state': 'NC', 'zipcode': '28398', 'phone': None}]
            url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break
    return labs


##Get Lab Equations
def fetch_lab_equations(labs):
    for lab in labs:
        V1_LAB_EQU_API = "https://www.labtalkonline.net/core/api/lab/%s/equations?limit=100" % (lab["third_party_id"],)
        V2_LAB_EQU_API = "http://127.0.0.1:8000/reference/labs_equation_sets/"
        print ("Lab V1=%s V2=%s" % (lab["third_party_id"],lab["id"],))
        response = requests.get(V1_LAB_EQU_API, headers=V1_HEADERS)
        equations = response.json()["results"]
        for equ in equations:
            new_equ = {}
            new_equ["lab"] = lab["id"]
            new_equ["name"] = equ.get("name")
            new_equ["result_type"] = 1
            new_equ["type"] = equ.get("type")
            if SEND_TO_V2:
                response2 = requests.post(V2_LAB_EQU_API, json=new_equ, headers=V2_HEADERS)
                labequ = response2.json()
                print ("Lab Eq V1=%s V2=%s" % (equ.get("id"),labequ.get("id"),))
                fetch_lab_crops(equ.get("id"),labequ.get("id"))

##Get Lab Rx Elements

##Get Lab Crops
def fetch_lab_crops(v1_equid, v2_equid):
    V1_LAB_EQU_CROPS_URL = "https://www.labtalkonline.net/core/api/lab/equation/%s/crops" % (v1_equid,)
    
    url = V1_LAB_EQU_CROPS_URL
    labs = []
    while url:
        response = requests.get(url, headers=V1_HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for crop in data.get("results", []):
                new_crop = crop
                del new_crop["id"]
                new_crop["equation_set"] = v2_equid
                print ("Crop - %s" % (new_crop["crop"],))
                
                if SEND_TO_V2:
                    V2_LAB_EQU_CROPS_URL = "http://127.0.0.1:8000/reference/labs_equation_sets/%s/crops/" % (v2_equid,)
                    response2 = requests.post(V2_LAB_EQU_CROPS_URL, json=new_crop, headers=V2_HEADERS)
                else:
                    labs = [{'id': '6bc5da23-07fc-44dc-84c0-7c158fbfe146', 'name': 'Camilla - M1', 'third_party_id': '1', 'address_1': '257 Newton Highway', 'address_2': None, 'city': 'Camilla', 'state': 'GA', 'zipcode': '31730', 'phone': None}, {'id': 'f9fbe352-741a-45d2-8ca2-b5c006531907', 'name': 'Camilla - M3', 'third_party_id': '5', 'address_1': '257 Newton Highway', 'address_2': None, 'city': 'Camilla', 'state': 'GA', 'zipcode': '31730', 'phone': None}, {'id': '0be1d7b9-ee7b-47be-86b5-ff0f8465fadb', 'name': 'Owensboro', 'third_party_id': '2', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': '2b8085ba-9e6b-4718-b97d-f2f120749ef7', 'name': 'Owensboro - Bray', 'third_party_id': '6', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': 'dd4074ad-0c05-45c6-9bc1-ab145354e444', 'name': 'Owensboro - M1', 'third_party_id': '8', 'address_1': '2101 Calhoun Road', 'address_2': None, 'city': 'Owensboro', 'state': 'KY', 'zipcode': '42301', 'phone': None}, {'id': 'd4ae26b1-a8f9-4868-8f9a-14e1768f34d1', 'name': 'Owensboro - Olsen', 'third_party_id': '7', 'address_1': None, 'address_2': None, 'city': None, 'state': None, 'zipcode': None, 'phone': None}, {'id': '850ff4ca-8d3a-4250-9a41-b162eb130c5d', 'name': 'Vicksburg', 'third_party_id': '4', 'address_1': '4589 Highway 61 South', 'address_2': None, 'city': 'Vicksburg', 'state': 'MS', 'zipcode': '39180', 'phone': None}, {'id': '00791f22-c9aa-47ec-ba8b-80a8c773ac2a', 'name': 'Warsaw', 'third_party_id': '3', 'address_1': '364 W. Park Drive', 'address_2': None, 'city': 'Warsaw', 'state': 'NC', 'zipcode': '28398', 'phone': None}]
                
            url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break





if __name__ == "__main__":
    #Log into labtalk v2
    LOGIN_DATA = {
        "username": "hunt",
        "password": "psuy2k99!"
    }

    TOKEN_URL = "http://127.0.0.1:8000/api/token/"
    headers = {"Content-Type": "application/json"}
    if SEND_TO_V2:
        response = requests.post(TOKEN_URL, json=LOGIN_DATA, headers=headers)
        ACCESS_TOKEN = response.json()["access"]
    
    V2_HEADERS = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    API_URL = "https://www.labtalkonline.net/core/api/customers"
    LOGIN_URL = "https://www.labtalkonline.net/api-token-auth/"  # Adjust login endpoint

    session = requests.Session()
    
    credentials = {
        "username": "labtalkadmin",
        "password": "Labtalk99!"
    }

    csrf_token = login_and_get_csrf(session, LOGIN_URL, credentials)

    if csrf_token:
        V1_HEADERS = {
            "accept": "application/json",
            "Authorization": f"Token {csrf_token}"  # Use 'Token' before the actual token
        }
        labs = fetch_labs()
        fetch_lab_equations(labs)

    else:
        print("Failed to authenticate or retrieve CSRF token.")
