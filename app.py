from flask import Flask, request, render_template

# ✅ CREATE app FIRST
app = Flask(__name__)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Search route
@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    date = request.form['date']

    result = f"Flights from {source} to {destination} on {date}"
    return result

# Run app
if __name__ == '__main__':
    app.run(debug=True)