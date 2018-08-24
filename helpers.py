import json
import requests
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty
from copy import deepcopy

holidays = [ date(2018,8,9), date(2018,8,22), date(2018,11,6), date(2018,12,25), date(2019,1,1), date(2019,2,5), date(2019,2,6), date(2019,4,19), date(2019,5,1), date(2019,5,19), date(2019,6,5), date(2019,8,9), date(2019,8,11), date(2019,10,27), date(2019,12,25) ]

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

        has_rate = False
        curr_rate = 0
        # curr_rate_end_datetime = 0

        days_diff = 0
        if curr_datetime.date() in holidays:
            days_diff = curr_datetime.weekday() - 6
            curr_datetime += timedelta(days = -days_diff)
            end_datetime += timedelta(days= -days_diff)

        start_day = curr_datetime.weekday()
        # find matching rate
        for rate in carpark_rates:
            # Run through all days contained in rate
            for i, day in enumerate(rate[schema["start_days"]]):
                rate_start_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(day - start_day)), str_to_time(rate[schema["start_time"]]))
                rate_end_datetime = datetime.combine(curr_datetime.date() + timedelta(days=(rate[schema["end_days"]][i] - start_day)), str_to_time(rate[schema["end_time"]]))
                if rate_start_datetime <= curr_datetime < rate_end_datetime:
                    has_rate = True
                    curr_rate = rate
                    curr_rate_end_datetime = rate_end_datetime
                    break
            else:
                continue
            break

        # Proceed if there is a matching rate
        if not has_rate:
            return -1
        else:
            #calculate cost in current rate interval, stoppping if end datetime is reached.
            charges = curr_rate[schema["rate"]]
            for charge in charges:

                if curr_datetime >= end_datetime:
                    return result

                cents = charge[schema["rate_cost"]]
                per_duration = charge[schema["rate_per"]]
                for_duration = charge[schema["rate_for"]]

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

            curr_datetime += timedelta(days = days_diff)
            end_datetime += timedelta(days = days_diff)

    return result

# returns a list of nearby carparks with each element as the complete data for each carpark, plus distance
def nearby_carparks(data, center_location, radius, schema):
    result = []
    for i, carpark in enumerate(data):
        distance = vincenty(center_location, carpark[schema["location"]]).m
        if distance <= radius:
            result.append(deepcopy(carpark))
            result[-1][schema["distance"]] = distance
            result[-1][schema["index"]] = i
    return result

# warning - sorts in place
def sort_carparks(data, schema, price_first):
    if not data:
        return []
    if price_first == True:
        data.sort(key = lambda carpark: carpark[schema["distance"]])
        data.sort(key = lambda carpark: carpark[schema["price"]])
        #if len(list(filter(lambda carpark: carpark[schema["price"]] != -1, data))) > 0:
        if len([1 for carpark in data if carpark[schema["price"]] != -1]) > 0:
            while data[0][schema["price"]] == -1:
                data.append(data.pop(0))
    else:
        data.sort(key = lambda carpark: carpark[schema["price"]])
        #if len(list(filter(lambda carpark: carpark[schema["price"]] != -1, data))) > 0:
        if len([1 for carpark in data if carpark[schema["price"]] != -1]) > 0:
            while data[0][schema["price"]] == -1:
                data.append(data.pop(0))
        data.sort(key = lambda carpark: carpark[schema["distance"]])

# returns a list of nearby carparks with each element as the complete data for each carpark, plus price and lots
def cheapest_carparks_within_radius(data, center_location, radius, start_datetime, end_datetime, schema, price_first):

    valid_data = nearby_carparks(data, center_location, radius, schema)
    if not valid_data:
        return []
    for carpark in valid_data:
        carpark[schema["price"]] = carpark_charges(carpark, start_datetime, end_datetime, schema)
    sort_carparks(valid_data, schema, price_first)
    return valid_data

def cheapest_carparks_for_durations(data, center_location, radius, start_datetime, start_hr, end_hr, schema):

    results = []

    valid_data = nearby_carparks(data, center_location, radius, schema)
    if not valid_data:
        return []

    for hours in range(start_hr, end_hr + 1):
        #print("from:", from_datetime, "to:", start_datetime + timedelta(hours=hours))
        new_data = deepcopy(valid_data)
        for carpark in new_data:
            carpark[schema["price"]] = carpark_charges(carpark, start_datetime, start_datetime + timedelta(hours=hours), schema)
        sort_carparks(new_data, schema, price_first=True)
        #print("name:", new_data[0][d_name], "price:", new_data[0][d_price])
        results.append(new_data[0])

    return results