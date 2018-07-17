import json
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty
from copy import deepcopy
from helpers import *

data_file = "data-minified-16072018.json"
data_schema_file = "data-schema.json"

app = Flask(__name__)
app.config["DEBUG"] = True

with app.open_resource(data_file) as f:
    data = json.load(f)
    data_length = len(data)
with app.open_resource(data_schema_file) as schema_file:
    schema = json.load(schema_file)

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        messages = []
        try:
            from_datetime = datetime.strptime(request.form["start"], "%Y-%m-%dT%H:%M")
        except Exception as e:
            messages.append("Start datetime invalid.")
            messages.append(str(e))
        try:
            to_datetime = datetime.strptime(request.form["end"], "%Y-%m-%dT%H:%M")
        except Exception as e:
            messages.append("End datetime invalid.")
            messages.append(str(e))
        try:
            lat = float(request.form["lat"])
            lng = float(request.form["lng"])
            center_loc = [lat, lng]
        except Exception as e:
            messages.append("Center location invalid.")
            messages.append(str(e))
        try:
            radius = int(request.form["radius"])
        except Exception as e:
            messages.append("Radius invalid.")
            messages.append(str(e))
        try:
            radio = bool(int(request.form["radio"]))
        except Exception as e:
            messages.append("Sorting method invalid.")
            messages.append(str(e))
        try:
            cheapest_carparks = cheapest_carparks_within_radius(data, center_loc, radius, from_datetime, to_datetime, schema, pricefirst=radio)
        except Exception as e:
            messages.append("Error ocurred while searching for carparks")
            messages.append(str(e))

        #markers = list(map(lambda carpark: carpark[schema["location"]], cheapest_carparks))

        search_params = {"start": from_datetime.strftime("%a, %-d %B %Y, %-I:%M %p"), "end": to_datetime.strftime("%a, %-d %B %Y, %-I:%M %p"), "center": center_loc, "radius": radius, "place":request.form["place"]}

        if not messages:
            return render_template("results.html", search_params=search_params, results=cheapest_carparks, schema=schema)
        else:
            return render_template("apology.html", messages=messages)
    else:
        carpark_id = int(request.args.get('id', -1))
        markers = list(map(lambda carpark: carpark[schema["location"]], data))
        if carpark_id > -1 and carpark_id < data_length:
            center = data[carpark_id][schema["location"]]
            name = data[carpark_id][schema["name"]]
            return render_template("index.html", markers=markers, schema=schema, center=center, name=name)
        else:
            return render_template("index.html", markers=markers, schema=schema)

@app.route('/browse')
def browse():
    carpark_id = int(request.args.get('id', -1))
    return render_template("browse.html", data=add_carparks_availability(data, schema), schema=schema, id=carpark_id)

@app.route('/terms')
def terms():
    return render_template("terms.html")

@app.route('/api/all')
def api_all():
    try:
        return jsonify(add_carparks_availability(data, schema))
    except:
        return abort(400)

@app.route('/api/single')
def api_single():
    try:
        carpark_id = int(request.args["id"])
        #
        return jsonify(data[carpark_id], schema)
    except Exception as e:
        return str(e)

@app.route('/api/singleprice')
def api_single_price():
    messages = []
    try:
        from_datetime = datetime.strptime(request.args["start"], "%Y-%m-%dT%H:%M")
    except Exception as e:
        messages.append("Start datetime invalid. " + str(e))
    try:
        to_datetime = datetime.strptime(request.args["end"], "%Y-%m-%dT%H:%M")
    except Exception as e:
        messages.append("End datetime invalid. " + str(e))
    try:
        carpark_id = int(request.args["id"])
    except Exception as e:
        messages.append("Carpark ID invalid. " + str(e))
    try:
        priceonly = bool(request.args.get("priceonly", 0))
    except Exception as e:
        messages.append("Price only invalid. " + str(e))
    try:
        carpark = deepcopy(data[carpark_id])
        charges = carpark_charges(carpark, from_datetime, to_datetime, schema)
    except Exception as e:
        messages.append("Error occurred. " + str(e))
    if messages:
        return jsonify(messages)
    else:
        if priceonly:
            return jsonify(charges)
        else:
            carpark[schema["price"]] = charges
            return jsonify(carpark)

@app.route('/api/multiple')
def api_multiple():
    messages = []
    try:
        from_datetime = datetime.strptime(request.args["start"], "%Y-%m-%dT%H:%M")
    except Exception as e:
        messages.append("Start datetime invalid. " + str(e))
    try:
        to_datetime = datetime.strptime(request.args["end"], "%Y-%m-%dT%H:%M")
    except Exception as e:
        messages.append("End datetime invalid. " + str(e))
        messages.append(str(e))
    try:
        lat = float(request.args["lat"])
        lng = float(request.args["lng"])
        center_loc = [lat, lng]
    except Exception as e:
        messages.append("lat and lng invalid. " + str(e))
    try:
        radius = int(request.args["radius"])
    except Exception as e:
        messages.append("Radius invalid. " + str(e))
    try:
        cheapest_carparks = cheapest_carparks_within_radius(data, center_loc, radius, from_datetime, to_datetime, schema)
    except Exception as e:
        messages.append("Error ocurred while searching for carparks. " + str(e))

    if not messages:
        return jsonify(cheapest_carparks)
    else:
        abort(400)
        # return jsonify(messages)

@app.route('/fuzzy', methods=["GET", "POST"])
def fuzzy():
    if request.method == "POST":
        messages = []
        try:
            from_datetime = datetime.strptime(request.form["start"], "%Y-%m-%dT%H:%M")
        except Exception as e:
            messages.append("Start datetime invalid.")
            messages.append(str(e))
        try:
            start_hr = int(request.form["start_hr"])
            end_hr = int(request.form["end_hr"])
            if end_hr < start_hr:
                raise Exception
        except Exception as e:
            messages.append("Start and/or end hour invalid.")
            messages.append(str(e))
        try:
            lat = float(request.form["lat"])
            lng = float(request.form["lng"])
            center_loc = [lat, lng]
        except Exception as e:
            messages.append("Center location invalid.")
            messages.append(str(e))
        try:
            radius = int(request.form["radius"])
        except Exception as e:
            messages.append("Radius invalid.")
            messages.append(str(e))
        try:
            cheapest_carparks2 = cheapest_carparks_for_durations(data, center_loc, radius, from_datetime, start_hr, end_hr, schema)
        except Exception as e:
            messages.append("Error ocurred while searching for carparks.")
            messages.append(str(e))

        markers = {}
        for i, carpark in enumerate(cheapest_carparks2):
            if tuple(carpark[schema["location"]]) in markers:
                markers[tuple(carpark[schema["location"]])]["hours"].append(start_hr + i)
            else:
                markers[tuple(carpark[schema["location"]])] = {}
                markers[tuple(carpark[schema["location"]])]["hours"] = [start_hr + i]
                markers[tuple(carpark[schema["location"]])]["index"] = i + 1

        search_params = {"start": from_datetime.strftime("%a, %-d %B %Y, %-I:%M %p"), "start_hr": start_hr, "end_hr": end_hr, "center": center_loc, "radius": radius, "place":request.form["place"]}

        if not messages:
            return render_template("fuzzy_results.html", search_params=search_params, markers=markers, results=cheapest_carparks2, schema=schema)
        else:
            return render_template("apology.html", messages=messages)
    else:
        markers = list(map(lambda carpark: carpark[schema["location"]], data))
        return render_template("fuzzy.html", markers=markers, schema=schema)

@app.route('/calc')
def calculator():
    return render_template("calculator.html", data=add_carparks_availability(data, schema), schema=schema)

@app.route('/browse2')
def browse2():
    carpark_id = int(request.args.get('id', -1))
    markers = list(map(lambda carpark: carpark[schema["location"]], data))
    add_carparks_availability(data, schema)
    return render_template("browse2.html", markers=markers, id=carpark_id)