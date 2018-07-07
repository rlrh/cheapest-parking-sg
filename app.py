import json
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty
from helpers import *

data_file = "data-minified.json"
data_schema_file = "data-schema.json"

app = Flask(__name__)
app.config["DEBUG"] = True

with app.open_resource(data_file) as f:
    data = json.load(f)
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
            #raw_loc = request.form["center"].split(" ")
            #center_loc = list(map(lambda x: float(x), raw_loc))
        except Exception as e:
            messages.append("Center location invalid.")
            messages.append(str(e))
        try:
            radius = int(request.form["radius"])
        except Exception as e:
            messages.append("Radius invalid.")
            messages.append(str(e))
        try:
            cheapest_carparks = cheapest_carparks_within_radius(data, center_loc, radius, from_datetime, to_datetime, schema)
            sort_carparks(cheapest_carparks, schema)
        except Exception as e:
            messages.append("Error ocurred while searching for carparks")
            messages.append(str(e))

        markers = list(map(lambda carpark: carpark[schema["location"]], cheapest_carparks))

        search_params = {"start": from_datetime.strftime("%a, %-d %B %Y, %-I:%M %p"), "end": to_datetime.strftime("%a, %-d %B %Y, %-I:%M %p"), "center": center_loc, "radius": radius, "place":request.form["place"]}

        if not messages:
            return render_template("results.html", search_params=search_params, results=cheapest_carparks, markers=markers, schema=schema)
        else:
            return render_template("apology.html", messages=messages)
        """
        except Exception as e:
            error = str(e)
            return render_template("apology.html", messages=[error])
        """
    else:
        markers = list(map(lambda carpark: carpark[schema["location"]], data))
        return render_template("index.html", markers=markers, schema=schema)