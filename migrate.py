import requests, json, os

PROCESSED_FILE = "processed_customers.json"



lab_lookup = {}
lab_lookup["1"] = "Camilla - M1"
lab_lookup["5"] = "Camilla - M3"
lab_lookup["2"] = "Owensboro"
lab_lookup["6"] = "Owensboro - Bray"
lab_lookup["8"] = "Owensboro - M1"
lab_lookup["7"] = "Owensboro - Olsen"
lab_lookup["4"] = "Vicksburg"
lab_lookup["3"] = "Warsaw"

def login_and_get_csrf(session, login_url, credentials):
    """Log in to get session and CSRF token."""
    response = session.post(login_url, data=credentials)
    return json.loads(response.text)["token"]

def load_processed_customers():
    """Load processed customer IDs from file."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_processed_customer(customer_id):
    """Save a customer ID to the processed file."""
    processed = load_processed_customers()
    processed.add(customer_id)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed), f)

def fetch_customers(api_url, HEADERS, V2_ACCESS_TOKEN):
    #get Labs#
    V2_LAB_API_URL = "http://127.0.0.1:8000/reference/labs/"
    LABTALK_V2_HEADERS = {
                    "Authorization": f"Bearer {V2_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
    response_labs = requests.get(V2_LAB_API_URL, headers=LABTALK_V2_HEADERS)
    lab_ref = response_labs.json()["results"]

    customers = []
    url = api_url
    processed_customers = load_processed_customers()
    
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for customer in data.get("results", []):
                customer_id = customer.get("id")  # Adjust if ID field is named differently
                if customer_id not in processed_customers:
                    process_customer(customer)  # Your processing function
                    save_processed_customer(customer_id)
                    print ("Getting Growers")
                    growers = fetch_growers(customer_id,HEADERS)
                    print ("Get Events")
                    fetch_sample_events(customer_id,growers,HEADERS,V2_ACCESS_TOKEN, lab_ref)
            url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return customers

def process_customer(customer):
    print(f"Processing customer: {customer['id']}")
    ##Set each sample event for a customer

def fetch_growers(customer, HEADERS):
    growers = []
    grower_url = "https://www.labtalkonline.net/core/api/growers/?customer=%s" % (customer)
    while grower_url:
        response = requests.get(grower_url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for grower in data.get("results", []):
                growers.append(grower)
            grower_url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return growers

def fetch_sample_events(customer, growers, HEADERS, V2_ACCESS_TOKEN, lab_ref):
    event_url = "https://www.labtalkonline.net/samples/api/sampleevents?customer=%s" % (customer)
    while event_url:
        response = requests.get(event_url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            #customers.extend(data.get("results", []))  # Adjust based on API response structure
            for event in data.get("results", []):
                event_data = {}
                ##Get the new customer ID###############
                LABTALK_V2_HEADERS = {
                    "Authorization": f"Bearer {V2_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                V2_CUSTOMER_URL = "http://127.0.0.1:8000/core/customers/?third_party_id="
                customer_response = requests.get(V2_CUSTOMER_URL + str(event.get("customer")), headers=LABTALK_V2_HEADERS)
                new_customer_id = customer_response.json()["results"][0]["id"]
                print ("New Customer ID " + str(new_customer_id))
                ########################################
                details_url = "https://www.labtalkonline.net/samples/api/sampleevent/%s/details" % (event.get("id"))
                detail_response = requests.get(details_url, headers=HEADERS)
                detail_data = detail_response.json()
                event_data["customer_id"] = new_customer_id
                if event.get("plant_results") == True:
                    event_data["result_type"] = "plant"
                if event.get("soil_results") == True:
                    event_data["result_type"] = "soil"
                if event.get("nematode_results") == True:
                    event_data["result_type"] = "nematode"

                event_data["comment"] = event.get("comment")
                ##Get new lab number##
                ##
                event_data["lab_number"] = event.get("lab_number")
                event_data["layer_id"] = event.get("third_party_id")
                #print (event.get("lab"))
                if event.get("lab"):
                    event_data["lab_id"] = [obj['id'] for obj in lab_ref if obj['third_party_id'] == str(event.get("lab"))][0]
                else:
                    event_data["lab_id"] = None
                event_data["date_collected"] = event.get("sampled_date")
                event_data["date_processed"] = event.get("processed_date")
                grower = [obj for obj in growers if obj["id"] == event.get("grower")]
                event_data["grower_name"] = grower[0].get("name")
                event_data["farm_name"] = event.get("farm").split(" - ")[0]
                if len(event.get("farm").split(" - ")) > 1:
                    event_data["field_name"] = event.get("farm").split(" - ")[1]
                else:
                    event_data["field_name"] = event.get("farm").split(" - ")[0]
                
                #Get Crops
                crops = detail_data.get("crop")
                if len(crops) > 0:
                    event_data["crop"] = crops[0]["crop"]
                    event_data["growth_stage"] = crops[0]["growth_stage"]

                ##Check for plant
                if event.get("plant_results") == True:
                    event_data["results"] = {}
                    event_data["recommendations"] = []
                    ##Get the meta data for the elements
                    event_data["results"]["meta"] = []
                    nutrients = common_plant_names(detail_data.get("samples"))

                    event_data["results"]["meta"].append({
                        "dt": "S",
                        "att": "ID",
                        "pos": 0,
                        "unit": "none"
                    })
                    
                    counter = 1
                    for common_name, unit in nutrients:
                        event_data["results"]["meta"].append({
                            "dt": "N",
                            "att": common_name,
                            "pos": counter,
                            "unit": unit
                        })
                        counter += 1
                    counter += 1
                    
                    event_data["results"]["meta"].append({
                        "dt": "S",
                        "att": "COMMENT",
                        "pos": counter,
                        "unit": "none"
                    })

                    ##get sample data
                    event_data["results"]["atts"] = []
                    for sample in detail_data.get("samples"):
                        nutrientArray = []
                        nutrientArray = [None] * (counter)
                        nutrientArray[0] = sample["number"]
                        
                        for nutrient in sample["plantnutrient"]:
                            nutrient["test"]["common_name"]
                            pos = get_pos_by_att(event_data["results"]["meta"],nutrient["test"]["common_name"])
                            nutrientArray[pos] = nutrient["value"]
                        nutrientArray[-1] = sample["comment"]
                        event_data["results"]["atts"].append(nutrientArray)
                        #Get the recs
                        unique_names = {entry["name"] for entry in sample["soilrecommendation"]}


                ##Check for soil data
                if event.get("soil_results") == True:
                    #Get results
                    event_data["results"] = {}
                    event_data["recommendations"] = []

                    ##Get the meta data for the elements
                    event_data["results"]["meta"] = []
                    nutrients = common_names(detail_data.get("samples"))
                    rec_name = common_rec_names(detail_data.get("samples"))
                    rec_elm_name = common_rec_elm_names(detail_data.get("samples"))

                    event_data["results"]["meta"].append({
                        "dt": "S",
                        "att": "ID",
                        "pos": 0,
                        "unit": "none"
                    })
                    
                    counter = 1
                    for common_name, unit in nutrients:
                        event_data["results"]["meta"].append({
                            "dt": "N",
                            "att": common_name,
                            "pos": counter,
                            "unit": unit
                        })
                        counter += 1
                    counter += 1
                    
                    event_data["results"]["meta"].append({
                        "dt": "S",
                        "att": "COMMENT",
                        "pos": counter,
                        "unit": "none"
                    })
                    
                    
                    
                    ##End of meta data
                    ##get sample data
                    event_data["results"]["atts"] = []
                    for sample in detail_data.get("samples"):
                        nutrientArray = []
                        nutrientArray = [None] * (counter)
                        nutrientArray[0] = sample["number"]
                        
                        for nutrient in sample["soilnutrient"]:
                            nutrient["test"]["common_name"]
                            pos = get_pos_by_att(event_data["results"]["meta"],nutrient["test"]["common_name"])
                            nutrientArray[pos] = nutrient["value"]
                        nutrientArray[-1] = sample["comment"]
                        event_data["results"]["atts"].append(nutrientArray)
                        #Get the recs
                        unique_names = {entry["name"] for entry in sample["soilrecommendation"]}

                    #get the recs ready
                    for name in rec_name:
                        rec = {}
                        ##setup the rec meta
                        rec["name"] = name
                        rec["meta"] = []
                        rec["meta"].append({
                            "dt": "S",
                            "att": "ID",
                            "pos": 0,
                            "unit": "none"
                        })
                        rec["recs"] = []

                        counter = 1
                        for common_name, unit in rec_elm_name:
                            rec["meta"].append({
                                "dt": "N",
                                "att": common_name,
                                "pos": counter,
                                "unit": unit
                            })
                            counter += 1

                        for sample in detail_data.get("samples"):
                            recArray = []
                            recArray = [None] * (counter)
                            recArray[0] = sample["number"]
                            for nutrient in sample["soilrecommendation"]:
                                if (name == nutrient["name"]):
                                    pos = get_pos_by_att(rec["meta"],nutrient["recommendation_element"]["abbreviation"])
                                    recArray[pos] = nutrient["value"]
                            rec["recs"].append(recArray)
                        event_data["recommendations"].append(rec)
                event_data["documents"] = []
                for report in detail_data.get("reports"):
                    event_data["documents"].append({
                        "url": report["url"],
                        "display_name": report["file_name"]
                    })
                
                file_name = "out/%s.json" % (event.get("id"))
                with open(file_name, "w") as json_file:
                    json.dump(event_data, json_file, indent=4) 
                #break

            event_url = data.get("next")  # Adjust if the API uses a different pagination format
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return True

def get_pos_by_att(meta, att_value):
    return next((item["pos"] for item in meta if item["att"] == att_value), None)


def common_names(samples):
    # Extract unique common_name and unit pairs
    unique_nutrient_info = set()

    # Loop through each sample
    for sample in samples:
        # Loop through each soilnutrient in the sample
        for nutrient in sample["soilnutrient"]:
            # Add the tuple (common_name, unit) to the set
            unique_nutrient_info.add((nutrient["test"]["common_name"], nutrient["unit"]))

    # Convert the set to a list if needed, to display the results
    unique_nutrient_info_list = list(unique_nutrient_info)
    return unique_nutrient_info_list

def common_plant_names(samples):
    # Extract unique common_name and unit pairs
    unique_nutrient_info = set()

    # Loop through each sample
    for sample in samples:
        # Loop through each soilnutrient in the sample
        for nutrient in sample["plantnutrient"]:
            # Add the tuple (common_name, unit) to the set
            unique_nutrient_info.add((nutrient["test"]["common_name"], nutrient["unit"]))

    # Convert the set to a list if needed, to display the results
    unique_nutrient_info_list = list(unique_nutrient_info)
    return unique_nutrient_info_list

def common_rec_names(samples):
    # Extract unique common_name and unit pairs
    unique_rec_info = set()

    # Loop through each sample
    for sample in samples:
        # Loop through each soilnutrient in the sample
        for rec in sample["soilrecommendation"]:
            # Add the tuple (common_name, unit) to the set
            unique_rec_info.add((rec["name"]))

    # Convert the set to a list if needed, to display the results
    unique_rec_info_list = list(unique_rec_info)
    return unique_rec_info_list

def common_rec_elm_names(samples):
    # Extract unique common_name and unit pairs
    unique_rec_info = set()

    # Loop through each sample
    for sample in samples:
        # Loop through each soilnutrient in the sample
        for rec in sample["soilrecommendation"]:
            # Add the tuple (common_name, unit) to the set
            unique_rec_info.add((rec["recommendation_element"]["abbreviation"], rec["unit"]))

    # Convert the set to a list if needed, to display the results
    unique_rec_info_list = list(unique_rec_info)
    return unique_rec_info_list

if __name__ == "__main__":
    LOGIN_DATA = {
        "username": "admin",
        "password": "admin99!"
    }

    TOKEN_URL = "http://127.0.0.1:8000/api/token/"
    headers = {"Content-Type": "application/json"}
   
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
        customers = fetch_customers(API_URL, HEADERS, ACCESS_TOKEN)
        print(f"Fetched {len(customers)} customers.")
    else:
        print("Failed to authenticate or retrieve CSRF token.")
