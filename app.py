import json
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty
from helpers import *

data_file = "data-minified.json"
# update schema in helpers.py if data format changes
"""
schema = {
    "carpark_id": "id",
    "name": "name",
    "location": "location",
    "address": "address",
    "updated": "updated",
    "rates": "rates",
    "start_days": "start_days",
    "start_time": "start_time",
    "end_days": "end_days",
    "end_time": "end_time",
    "rate": "rate",
    "rate_cost": "cost",
    "rate_per": "per",
    "rate_for": "for",
    "distance": "distance",
    "price": "price",
    "lots": "lots",
}
"""

app = Flask(__name__)

with app.open_resource(data_file) as f:
    data = json.load(f)

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
            cheapest_carparks = cheapest_carparks_within_radius(data, center_loc, radius, from_datetime, to_datetime)
            sort_carparks(cheapest_carparks)
        except Exception as e:
            messages.append("Error ocurred while searching for carparks")
            messages.append(str(e))

        if not messages:
            return render_template("results.html", start=from_datetime, end=to_datetime, center=str(center_loc), radius=radius, results=cheapest_carparks)
        else:
            return render_template("apology.html", messages=messages)
        """
        except Exception as e:
            error = str(e)
            return render_template("apology.html", messages=[error])
        """
    else:
        return render_template("index.html")