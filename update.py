import json
import requests

input_file = "/home/rlrh1996/mysite/data-lta-orchard-cbd-cbdnorth-cbdsouth-jurong-ura-hdb-lhn-metro-minified.json"
output_file = "/home/rlrh1996/mysite/data.json"
data_schema_file = "/home/rlrh1996/mysite/data-schema.json"

# returns raw data from LTA DataMall
def lta_carparks_availability():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

def lta_carparks_availability2():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip=500' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

def lta_carparks_availability3():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip=1000' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

def lta_carparks_availability4():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2?$skip=1500' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

def ura_carparks_availability():
    with open("/home/rlrh1996/mysite/ura_token.json", "r") as f:
        token = json.load(f)
    headers = {'AccessKey': '1fa1d271-92db-46ef-8191-f8f277cefce1', 'Token': token} #this is by default
    url = 'https://www.ura.gov.sg/uraDataService/invokeUraDS?service=Car_Park_Availability' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["Result"]

def gov_carparks_availability():
    url = 'https://api.data.gov.sg/v1/transport/carpark-availability' #Resource URL
    r = requests.get(url)
    return r.json()["items"]["carpark_data"]

# returns a dictionary with key as carpark id and value as available lots
def carparks_availability(carparks, schema):
    result = {}
    carparks_with_id = list(filter(lambda carpark: schema["carpark_id"] in carpark, carparks))
    carpark_ids = list(map(lambda carpark: str(carpark[schema["carpark_id"]]), carparks_with_id))
    data1 = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, lta_carparks_availability() ))
    for datum in data1:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    data2 = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, lta_carparks_availability2() ))
    for datum in data2:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    data3 = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, lta_carparks_availability3() ))
    for datum in data3:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    data4 = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, lta_carparks_availability4() ))
    for datum in data4:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    data5 = list(filter(lambda carpark: carpark["carparkNo"] in carpark_ids and carpark["lotType"] == "C", ura_carparks_availability() ))
    for datum in data5:
        result[datum["carparkNo"]] = datum["lotsAvailable"]
    #data3 = list(filter(lambda carpark: carpark["carpark_number"] in carpark_ids, gov_carparks_availability() ))
    #for datum in data3:
    #    result[datum["carpark_number"]] = datum["carpark_info"][0]["lots_available"]

    return result

def add_carparks_availability(data, schema):
    if not data:
        return data
    available_lots = carparks_availability(data, schema)
    for carpark in data:
        try:
            if carpark[schema["carpark_id"]] in available_lots:
                carpark[schema["lots"]] = available_lots[carpark[schema["carpark_id"]]]
            else:
                carpark[schema["lots"]] = -1
        except:
            carpark[schema["lots"]] = -1
    return data

with open(data_schema_file, "r") as schema_file:
    schema = json.load(schema_file)

with open(input_file, "r") as f:
    data = json.load(f)

add_carparks_availability(data, schema)

with open(output_file, "w") as output_f:
    json.dump(data, output_f, separators=(',', ':'))