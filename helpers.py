import json
import requests
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty

# datafile settings
d_file = "data-minified.json"
d_id = "id"
d_name = "name"
d_location = "location"
d_address = "address"
d_updated = "updated"
d_rates = "rates"
d_start_days = "start_days"
d_start_time = "start_time"
d_end_days = "end_days"
d_end_time = "end_time"
d_rate = "rate"
d_rate_cost = "cost"
d_rate_per = "per"
d_rate_for = "for"
d_distance = "distance"
d_price = "price"
d_lots = "lots"

def str_to_time(string):
    split = list(map(lambda number: int(number), string.split(":")))
    if len(split) == 2:
        hour, minute = split
        return time(hour=hour, minute=minute)
    elif len(split) == 3:
        return time(hour=hour, minute=minute, second=second)
    else:
        raise Exception("Invalid time string.")

# returns integer representing price calculated for duration at carpark in cents
def charges(carpark, start_datetime, end_datetime):

    result = 0

    carpark_rates = carpark[d_rates]

    # Iterate until reach end datetime
    curr_datetime = start_datetime
    while curr_datetime < end_datetime:

        start_day = curr_datetime.weekday()
        start_time = curr_datetime.time().isoformat()
        end_day = curr_datetime.weekday()
        end_time = curr_datetime.time().isoformat()

        # find matching rate
        for rate in carpark_rates:
            # Run through all days conatined in rate
            for i, day in enumerate(rate[d_start_days]):
                rate_start_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(day - start_day)), str_to_time(rate[d_start_time]))
                rate_end_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(rate[d_end_days][i] - start_day)), str_to_time(rate[d_end_time]))
                if rate_start_datetime <= curr_datetime < rate_end_datetime:
                    curr_rate = rate
                    curr_day_idx = i
                    curr_rate_end_datetime = rate_end_datetime
                    break

        # Proceed if there is a matching rate
        try:
            charges = curr_rate[d_rate]
        except:
            return -1

        #calculate cost in current rate interval, stoppping if end date is reached.
        for charge in charges:
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
def carparks_availability(carparks):
    result = {}
    carpark_ids = list(map(lambda carpark: str(carpark["id"]), carparks))
    data = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, all_carparks_availability() ))
    for datum in data:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    return result

# returns a list of nearby carparks with each element as the complete data for each carpark, plus distance
def nearby_carparks(data, center_location, radius):
    result = []
    for carpark in data:
        distance = vincenty(center_location, carpark[d_location]).m
        if distance <= radius:
            result.append(carpark)
            result[-1][d_distance] = distance
    return result


# returns a list of nearby carparks with each element as the complete data for each carpark, plus price and lots
def cheapest_carparks_within_radius(data, center_location, radius, start_datetime, end_datetime):

    valid_data = nearby_carparks(data, center_location, radius)
    if not valid_data:
        return []
    available_lots = carparks_availability(valid_data)
    for carpark in valid_data:
        carpark[d_price] = charges(carpark, start_datetime, end_datetime)
        if carpark[d_id] in available_lots:
            carpark[d_lots] = available_lots[carpark[d_id]]
        else:
            carpark[d_lots] = "Unknown"
    return valid_data

def sort_carparks(data, price_first=True):
    if price_first == True:
        data.sort(key = lambda carpark: carpark[d_distance])
        data.sort(key = lambda carpark: carpark[d_price])
    else:
        data.sort(key = lambda carpark: carpark[d_price])
        data.sort(key = lambda carpark: carpark[d_distance])