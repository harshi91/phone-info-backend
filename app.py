from flask import Flask, request, jsonify
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim

app = Flask(__name__)
geolocator = Nominatim(user_agent="phone_identifier")

def get_exif_data(image):
    try:
        exif_data = {}
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
        return exif_data
    except Exception as e:
        return {}

def get_lat_lon(exif_data):
    try:
        gps_info = exif_data.get("GPSInfo")
        if not gps_info:
            return None, None

        def to_degrees(val):
            d = val[0][0] / val[0][1]
            m = val[1][0] / val[1][1]
            s = val[2][0] / val[2][1]
            return d + (m / 60.0) + (s / 3600.0)

        lat = to_degrees(gps_info[2])
        if gps_info[1] == 'S': lat = -lat
        lon = to_degrees(gps_info[4])
        if gps_info[3] == 'W': lon = -lon

        return lat, lon
    except:
        return None, None

def get_location(lat, lon):
    try:
        location = geolocator.reverse((lat, lon))
        return location.address
    except:
        return "Location not found"

@app.route("/upload", methods=["POST"])
def upload():
    if "photo" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["photo"]
    image = Image.open(file.stream)
    exif = get_exif_data(image)

    brand = exif.get("Make", "Unknown")
    model = exif.get("Model", "Unknown")
    owner = exif.get("Artist", "Unknown")
    lat, lon = get_lat_lon(exif)
    location = get_location(lat, lon) if lat and lon else "GPS not available"

    return jsonify({
        "Phone Brand": brand,
        "Phone Model": model,
        "Owner": owner,
        "Current Location": location
    })

if __name__ == "__main__":
    app.run(debug=True)
