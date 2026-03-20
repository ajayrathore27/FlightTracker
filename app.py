from flask import Flask, request, render_template, jsonify
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# ── Mock airline data ──────────────────────────────────────────────────────────
AIRLINES = [
    {"code": "AA", "name": "American Airlines", "logo": "✈"},
    {"code": "DL", "name": "Delta Air Lines",   "logo": "✈"},
    {"code": "UA", "name": "United Airlines",   "logo": "✈"},
    {"code": "SW", "name": "Southwest Airlines","logo": "✈"},
    {"code": "B6", "name": "JetBlue Airways",   "logo": "✈"},
    {"code": "F9", "name": "Frontier Airlines", "logo": "✈"},
]

AIRPORT_NAMES = {
    "JFK": "John F. Kennedy International",
    "LAX": "Los Angeles International",
    "ORD": "O'Hare International",
    "ATL": "Hartsfield-Jackson Atlanta",
    "DFW": "Dallas/Fort Worth International",
    "DEN": "Denver International",
    "SFO": "San Francisco International",
    "SEA": "Seattle-Tacoma International",
    "MIA": "Miami International",
    "BOS": "Boston Logan International",
    "LHR": "London Heathrow",
    "CDG": "Paris Charles de Gaulle",
    "NRT": "Tokyo Narita",
    "DXB": "Dubai International",
    "SYD": "Sydney Kingsford Smith",
}

def generate_flights(source, destination, date, trip_type="one-way", passengers=1):
    """Generate realistic mock flight results."""
    flights = []
    num_flights = random.randint(4, 8)

    try:
        dep_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        dep_date = datetime.now() + timedelta(days=7)

    base_price = random.randint(150, 900)

    for i in range(num_flights):
        airline = random.choice(AIRLINES)
        dep_hour = random.randint(5, 22)
        dep_min  = random.choice([0, 15, 30, 45])
        duration_h = random.randint(1, 14)
        duration_m = random.choice([0, 15, 30, 45])

        dep_time = dep_date.replace(hour=dep_hour, minute=dep_min)
        arr_time = dep_time + timedelta(hours=duration_h, minutes=duration_m)

        stops = random.choices([0, 1, 2], weights=[40, 45, 15])[0]
        price = base_price + random.randint(-50, 200) + (stops * -30) + (i * random.randint(-20, 40))
        price = max(49, price) * passengers

        cabin_class = random.choices(
            ["Economy", "Premium Economy", "Business", "First"],
            weights=[60, 20, 15, 5]
        )[0]

        flights.append({
            "id": f"FL{random.randint(1000,9999)}",
            "airline": airline["name"],
            "airline_code": airline["code"],
            "flight_num": f"{airline['code']}{random.randint(100,9999)}",
            "dep_time": dep_time.strftime("%H:%M"),
            "arr_time": arr_time.strftime("%H:%M"),
            "arr_next_day": arr_time.date() > dep_date.date(),
            "duration": f"{duration_h}h {duration_m:02d}m",
            "duration_mins": duration_h * 60 + duration_m,
            "stops": stops,
            "stop_label": "Nonstop" if stops == 0 else f"{stops} stop{'s' if stops>1 else ''}",
            "price": price,
            "cabin": cabin_class,
            "emissions": random.randint(80, 400),
            "co2_label": random.choice(["Low emissions", "Avg emissions", "High emissions"]),
        })

    flights.sort(key=lambda x: x["price"])
    return flights


def get_airport_label(code):
    code = code.upper().strip()
    name = AIRPORT_NAMES.get(code, code)
    return {"code": code, "name": name}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    return render_template("index.html", today=today, next_week=next_week)


@app.route("/search", methods=["POST"])
def search():
    # Collect & validate inputs
    errors = []
    source      = request.form.get("source", "").strip().upper()
    destination = request.form.get("destination", "").strip().upper()
    date        = request.form.get("date", "").strip()
    return_date = request.form.get("return_date", "").strip()
    trip_type   = request.form.get("trip_type", "one-way")
    passengers  = request.form.get("passengers", "1")
    cabin       = request.form.get("cabin", "Economy")
    sort_by     = request.form.get("sort_by", "price")

    # Validations
    if not source:
        errors.append("Please enter a departure airport.")
    if not destination:
        errors.append("Please enter a destination airport.")
    if source and destination and source == destination:
        errors.append("Departure and destination cannot be the same.")
    if not date:
        errors.append("Please select a travel date.")
    else:
        try:
            parsed = datetime.strptime(date, "%Y-%m-%d")
            if parsed.date() < datetime.now().date():
                errors.append("Travel date cannot be in the past.")
        except ValueError:
            errors.append("Invalid date format.")

    try:
        passengers = int(passengers)
        if passengers < 1 or passengers > 9:
            raise ValueError
    except ValueError:
        errors.append("Passengers must be between 1 and 9.")
        passengers = 1

    if errors:
        today     = datetime.now().strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        return render_template(
            "index.html",
            errors=errors,
            today=today,
            next_week=next_week,
            form_data=request.form,
        )

    # Generate results
    flights = generate_flights(source, destination, date, trip_type, passengers)

    # Sort
    if sort_by == "duration":
        flights.sort(key=lambda x: x["duration_mins"])
    elif sort_by == "stops":
        flights.sort(key=lambda x: x["stops"])
    else:
        flights.sort(key=lambda x: x["price"])

    src_info = get_airport_label(source)
    dst_info = get_airport_label(destination)

    best_price = flights[0]["price"] if flights else 0

    return render_template(
        "results.html",
        flights=flights,
        source=src_info,
        destination=dst_info,
        date=datetime.strptime(date, "%Y-%m-%d").strftime("%a, %b %d %Y"),
        return_date=return_date,
        trip_type=trip_type,
        passengers=passengers,
        cabin=cabin,
        sort_by=sort_by,
        best_price=best_price,
        total=len(flights),
    )


@app.route("/flight/<flight_id>")
def flight_detail(flight_id):
    return render_template("detail.html", flight_id=flight_id)


@app.errorhandler(404)
def not_found(e):
    return render_template("index.html", errors=["Page not found."]), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("index.html", errors=["Server error. Please try again."]), 500


if __name__ == "__main__":
    app.run(debug=True)