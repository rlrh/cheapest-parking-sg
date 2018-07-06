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

def charges(carpark, start_datetime, end_datetime):

    result = 0

    carpark_rates = carpark["rates"]

    curr_datetime = start_datetime

    while curr_datetime < end_datetime:

        start_day = curr_datetime.weekday()
        start_time = curr_datetime.time().isoformat()
        end_day = curr_datetime.weekday()
        end_time = curr_datetime.time().isoformat()

        # find matching rate interval TODO: bisection search
        for rate in carpark_rates:
            #print(rate)
            rate_start_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(rate["sD"] - start_day)), str_to_time(rate["sT"]))
            rate_end_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(rate["eD"] - start_day)), str_to_time(rate["eT"]))
            if rate_start_datetime <= curr_datetime < rate_end_datetime:
                curr_rate = rate
                break
        try:
            charges = curr_rate["rate"]
            block_start_datetime = datetime.combine(curr_datetime.date(), str_to_time(curr_rate["sT"]))
            block_end_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(curr_rate["eD"] - curr_rate["sD"])), str_to_time(curr_rate["eT"]))
        except:
            return "No rate available for chosen interval"

        #calculate cost in current rate interval, stoppping if end date is reached.
        for charge in charges:
            cents, per_duration, for_duration = charge.values()

            if for_duration != 0: # initial charges
                charge_end_datetime = min(curr_datetime + timedelta(minutes=for_duration), block_end_datetime)
            else: # subsequent charges
                charge_end_datetime = block_end_datetime

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

def all_carparks_availability():
    headers = {'AccountKey': '7DXfhlXSQ3WpPNst98GfUw==', 'accept' : 'application/json'} #this is by default
    url = 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2' #Resource URL
    r = requests.get(url, headers=headers)
    return r.json()["value"]

def carparks_availability(carparks):
    result = {}
    carpark_ids = list(map(lambda carpark: str(carpark["id"]), carparks))
    data = list(filter(lambda carpark: carpark["CarParkID"] in carpark_ids, all_carparks_availability() ))
    for datum in data:
        result[datum["CarParkID"]] = datum["AvailableLots"]
    return result

def nearby_carparks(data, center_location, radius):
    result = []
    for carpark in data:
        distance = vincenty(center_location, carpark["loc"]).m
        if distance <= radius:
            result.append(carpark)
            result[-1]["dist"] = distance
    return result
    #return list(filter(lambda carpark: vincenty(center_location, carpark["loc"]).m <= radius, data))


def cheapest_carparks_within_radius(data, center_location, radius, start_datetime, end_datetime):

    valid_data = nearby_carparks(data, center_location, radius)
    if not valid_data:
        return []
    available_lots = carparks_availability(valid_data)
    for carpark in valid_data:
        carpark["price"] = charges(carpark, start_datetime, end_datetime)
        #carpark["dist"] = vincenty(center_location, carpark["loc"]).m
        if carpark["id"] in available_lots:
            carpark["lots"] = available_lots[carpark["id"]]
        else:
            carpark["lots"] = "Unknown"
    #valid_data.sort(key = lambda carpark: carpark["dist"])
    #valid_data.sort(key = lambda carpark: carpark["price"])
    return valid_data

def sort_carparks(data, price_first=True):
    if price_first == True:
        data.sort(key = lambda carpark: carpark["dist"])
        data.sort(key = lambda carpark: carpark["price"])
    else:
        data.sort(key = lambda carpark: carpark["price"])
        data.sort(key = lambda carpark: carpark["dist"])