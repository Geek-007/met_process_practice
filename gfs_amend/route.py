from flask import Flask
from flask import request
from GFSCorrect import CorrectGrid
from werkzeug.contrib.fixers import ProxyFix
app = Flask(__name__)

@app.route("/test_route")
def hello():
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    day = request.args.get('day')
    var = request.args.get('var')
    grid = CorrectGrid(lat, lon, day, var)
	results = grid.out_json()
    return str(results);

if __name__ == "__main__":
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0')