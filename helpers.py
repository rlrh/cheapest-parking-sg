import json
import requests
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty

def str_to_time(string):
    split = list(map(lambda number: int(number), string.split(":")))
    if len(split) == 2:
        hour, minute = split
        return time(hour=hour, minute=minute)
    elif len(split) == 3:
        hour, minute, second = split
        return time(hour=hour, minute=minute, second=second)
    else:
        raise Exception("Invalid time string.")

# returns integer representing price calculated for duration at carpark in cents
def carpark_charges(carpark, start_datetime, end_datetime, schema):

    result = 0

    carpark_rates = carpark[schema["rates"]]

    # Iterate until reach end datetime
    curr_datetime = start_datetime
    while curr_datetime < end_datetime:

        if curr_datetime >= end_datetime:
            return result

        start_day = curr_datetime.weekday()
        start_time = curr_datetime.time().isoformat()
        end_day = curr_datetime.weekday()
        end_time = curr_datetime.time().isoformat()

        # find matching rate
        for rate in carpark_rates:
            # Run through all days conatined in rate
            for i, day in enumerate(rate[schema["start_days"]]):
                rate_start_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(day - start_day)), str_to_time(rate[schema["start_time"]]))
                rate_end_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(rate[schema["end_days"]][i] - start_day)), str_to_time(rate[schema["end_time"]]))
                if rate_start_datetime <= curr_datetime < rate_end_datetime:
                    curr_rate = rate
                    curr_day_idx = i
                    curr_rate_end_datetime = rate_end_datetime
                    break

        # Proceed if there is a matching rate
        try:
            charges = curr_rate[schema["rate"]]
        except:
            return -1

        #calculate cost in current rate interval, stoppping if end date is reached.
        for charge in charges:

            if curr_datetime >= end_datetime:
                return result

            cents, per_duration, for_duration = charge.values()

            if for_duration != 0: # initial charges
                charge_end_datetime = min(curr_rate_end_datetime, curr_datetime + timedelta(minutes=for_duration))
            else: # subsequent charges
                charge_end_datetime = curr_rate_end_datetime

            if per_duration == 0: # per entry
                result += cents
                curr_datetime = charge_end_datetime
            else: # not per entry
                while curr_datetime < charge_end_datetime:
                    if curr_datetime >= end_datetime:
                        return result
                    result += cents
                    curr_datetime = min(curr_datetime + timedelta(minutes=per_duration), charge_end_datetime)
    return result

# returns raw data from LTA DataMall
def all_carparks_availability():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

# returns a dictionary with key as carpark id and value as available lots
def carparks_availability(carparks, schema):
    result = {}
    carpark_ids = list(map(lambda carpark: str(carpark[schema["carpark_id"]]), carparks))
    data = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, all_carparks_availability() ))
    for datum in data:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    return result

# returns a list of nearby carparks with each element as the complete data for each carpark, plus distance
def nearby_carparks(data, center_location, radius, schema):
    result = []
    for i, carpark in enumerate(data):
        distance = vincenty(center_location, carpark[schema["location"]]).m
        if distance <= radius:
            result.append(carpark)
            result[-1][schema["distance"]] = distance
            result[-1][schema["index"]] = i
    return result


# returns a list of nearby carparks with each element as the complete data for each carpark, plus price and lots
def cheapest_carparks_within_radius(data, center_location, radius, start_datetime, end_datetime, schema):

    valid_data = nearby_carparks(data, center_location, radius, schema)
    if not valid_data:
        return []
    available_lots = carparks_availability(valid_data, schema)
    for carpark in valid_data:
        carpark[schema["price"]] = carpark_charges(carpark, start_datetime, end_datetime, schema)

        try:
            if carpark[schema["carpark_id"]] in available_lots:
                carpark[schema["lots"]] = available_lots[carpark[schema["carpark_id"]]]
            else:
                carpark[schema["lots"]] = -1
        except:
            carpark[schema["lots"]] = -1
    return valid_data

def sort_carparks(data, schema, price_first=True):
    if price_first == True:
        data.sort(key = lambda carpark: carpark[schema["distance"]])
        data.sort(key = lambda carpark: carpark[schema["price"]])
    else:
        data.sort(key = lambda carpark: carpark[schema["price"]])
        data.sort(key = lambda carpark: carpark[schema["distance"]])

def add_carparks_availability(data, schema):
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
