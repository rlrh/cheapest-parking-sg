import json
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
from datetime import date, time, datetime, timedelta
from geopy.distance import vincenty
from copy import deepcopy
from helpers import *
from flask_mail import Mail, Message

data_file = "data-lta-orchard-cbd-minified.json"
data_schema_file = "data-schema.json"

app = Flask(__name__)
#app.config["DEBUG"] = True

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sender.carparkssg@gmail.com'
app.config['MAIL_PASSWORD'] = 'sgparkscar'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

with app.open_resource(data_file) as f:
    data = json.load(f)
    data_length = len(data)
with app.open_resource(data_schema_file) as schema_file:
    schema = json.load(schema_file)

# WEBSITE ROUTES

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
            if to_datetime < from_datetime:
                raise Exception("End datetime earlier than start datetime.")
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
            if radius > 2000:
                raise Exception("Radius too big.")
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
            messages.append("Error ocurred while searching for carparks.")
            messages.append(str(e))

        search_params = {"start": from_datetime.strftime("%a, %-d %b %Y, %-I:%M %p"), "end": to_datetime.strftime("%a, %-d %b %Y, %-I:%M %p"), "center": center_loc, "radius": radius, "place":request.form["place"]}

        if not messages:
            return render_template("results.html", search_params=search_params, results=cheapest_carparks, schema=schema)
        else:
            return render_template("apology.html", messages=messages)
    else:
        carpark_id = int(request.args.get('id', -1))
        markers = list(map(lambda carpark: carpark[schema["location"]], data))
        if carpark_id != -1 and carpark_id < data_length:
            center = data[carpark_id][schema["location"]]
            name = data[carpark_id][schema["name"]]
            return render_template("index.html", markers=markers, schema=schema, center=center, name=name)
        else:
            return render_template("index.html", markers=markers, schema=schema)

@app.route('/find')
def cheapest():
    messages = []
    try:
        from_datetime = datetime.strptime(request.args["start"], "%Y-%m-%dT%H:%M")
    except Exception as e:
        messages.append("Start datetime invalid. " + str(e))
    try:
        to_datetime = datetime.strptime(request.args["end"], "%Y-%m-%dT%H:%M")
        if to_datetime < from_datetime:
                raise Exception("End datetime earlier than start datetime.")
    except Exception as e:
        messages.append("End datetime invalid. " + str(e))
    try:
        lat = float(request.args["lat"])
        lng = float(request.args["lng"])
        center_loc = [lat, lng]
    except Exception as e:
        messages.append("Lat and lng invalid. " + str(e))
    try:
        try:
            radius = int(request.args.get("radius", 500))
        except:
            radius = 500
        if radius > 2000:
            raise Exception("Radius too big.")
    except Exception as e:
        messages.append("Radius invalid. " + str(e))
    try:
        radio = bool(int(request.form.get("pricefirst", 1)))
    except Exception as e:
        messages.append("Sorting method invalid.")
        messages.append(str(e))
    try:
        place = request.args.get("place", "")
    except Exception as e:
        messages.append("Place invalid. " + str(e))
    try:
        cheapest_carparks = cheapest_carparks_within_radius(data, center_loc, radius, from_datetime, to_datetime, schema, pricefirst=radio)
    except Exception as e:
        messages.append("Error ocurred while searching for carparks. " + str(e))

    #search_params = {"start": from_datetime.strftime("%a, %-d %b %Y, %-I:%M %p"), "end": to_datetime.strftime("%a, %-d %b %Y, %-I:%M %p"), "center": center_loc, "radius": radius, "place":place}
    search_params = {"start": from_datetime.strftime("%Y-%m-%dT%H:%M"), "end": to_datetime.strftime("%Y-%m-%dT%H:%M"), "center": center_loc, "radius": radius, "place":place}

    if not messages:
        return render_template("results_dynamic.html", search_params=search_params, results=cheapest_carparks, schema=schema)
    else:
        return render_template("apology.html", messages=messages)

@app.route('/multi', methods=["GET", "POST"])
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
            if radius > 2000:
                raise Exception("Radius too big.")
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

@app.route('/browse')
def browse():
    carpark_id = int(request.args.get('id', -1))
    markers = list(map(lambda carpark: carpark[schema["location"]], data))
    add_carparks_availability(data, schema)
    if carpark_id != -1 and carpark_id < data_length:
        center = data[carpark_id][schema["location"]]
        return render_template("browse_ajax.html", markers=markers, id=carpark_id, center=center, name=data[carpark_id][schema["name"]])
    else:
        return render_template("browse_ajax.html", markers=markers)

@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            msg = Message(request.form.get("subject","No subject"), sender = 'sender.carparkssg@gmail.com', recipients = ['carparkssg@gmail.com'])
            msg.body = "From: " + request.form.get("email","No email") + "\n\n" + request.form.get("message","No message")
            mail.send(msg)
            return render_template("about.html", sent=1)
        except:
            return render_template("about.html", sent=0)
    else:
        today = date.today().isoformat()
        if "place" in request.args:
            return render_template("about.html", place=request.args["place"], date=today)
        else:
            return render_template("about.html", date=today)

@app.route('/terms')
def terms():
    return render_template("terms.html")

# API ROUTES

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

@app.route('/api/multipleprice')
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

@app.route('/pwabuilder-sw.js', methods=['GET'])
def pwabuildersw():
    return app.send_static_file('pwabuilder-sw.js')
