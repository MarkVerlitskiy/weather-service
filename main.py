import requests
from flask import Flask, request, render_template_string
app = Flask(__name__)
API_KEY = "eJr9RIUNPgsPrTRCsd9U4kAAttlSq0TI"


def get_weather_data(latitude, longitude):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    location_params = {
        "apikey": API_KEY,
        "q": f"{latitude},{longitude}"
    }

    try:
        location_response = requests.get(location_url, params=location_params, timeout=5)
        location_response.raise_for_status()
        location_data = location_response.json()
        location_key = location_data.get("Key")

        if not location_key:
            return {"error": "Не удалось получить ключ местоположения. Проверьте координаты."}
        weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
        weather_params = {
            "apikey": API_KEY,
            "details": "true"
        }
        weather_response = requests.get(weather_url, params=weather_params, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        if weather_data:
            weather = weather_data[0]
            return {
                "temperature": weather["Temperature"]["Metric"]["Value"],
                "humidity": weather["RelativeHumidity"],
                "wind_speed": weather["Wind"]["Speed"]["Metric"]["Value"],
                "has_precipitation": weather["HasPrecipitation"]
            }
        else:
            return {"error": "Не удалось получить данные о погоде. Проверьте API или координаты."}

    except requests.Timeout:
        return {"error": "Ошибка: превышено время ожидания ответа от API."}
    except requests.RequestException as e:
        return {"error": f"Ошибка при запросе API: {e}"}


def check_bad_weather(temperature, wind_speed, has_precipitation):
    if temperature < 0 or temperature > 35:
        return True
    if wind_speed > 50:
        return True
    if has_precipitation:
        return True
    return False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Погодный сервис</title>
</head>
<body>
    <h1>Погодный сервис</h1>
    <form method="POST" action="/">
        <label for="start_lat">Широта начальной точки:</label>
        <input type="text" id="start_lat" name="start_lat" required><br><br>

        <label for="start_lon">Долгота начальной точки:</label>
        <input type="text" id="start_lon" name="start_lon" required><br><br>

        <label for="end_lat">Широта конечной точки:</label>
        <input type="text" id="end_lat" name="end_lat" required><br><br>

        <label for="end_lon">Долгота конечной точки:</label>
        <input type="text" id="end_lon" name="end_lon" required><br><br>

        <button type="submit">Проверить погоду</button>
    </form>
    {% if weather_result %}
        <h2>Результаты погоды:</h2>
        <p><strong>Начальная точка:</strong> {{ weather_start }}</p>
        <p><strong>Конечная точка:</strong> {{ weather_end }}</p>
        <h3>Погодные условия:</h3>
        <p>{{ weather_result }}</p>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def weather_service():
    if request.method == "POST":
        try:
            start_lat = float(request.form["start_lat"])
            start_lon = float(request.form["start_lon"])
            end_lat = float(request.form["end_lat"])
            end_lon = float(request.form["end_lon"])
            weather_start = get_weather_data(start_lat, start_lon)
            if "error" in weather_start:
                return render_template_string(HTML_TEMPLATE, weather_result=weather_start["error"])
            weather_end = get_weather_data(end_lat, end_lon)
            if "error" in weather_end:
                return render_template_string(HTML_TEMPLATE, weather_result=weather_end["error"])
            is_bad_start = check_bad_weather(
                temperature=weather_start["temperature"],
                wind_speed=weather_start["wind_speed"],
                has_precipitation=weather_start["has_precipitation"]
            )
            is_bad_end = check_bad_weather(
                temperature=weather_end["temperature"],
                wind_speed=weather_end["wind_speed"],
                has_precipitation=weather_end["has_precipitation"]
            )
            weather_result = (
                "Погода неблагоприятная" if is_bad_start or is_bad_end else "Погода благоприятная"
            )
            return render_template_string(
                HTML_TEMPLATE,
                weather_result=weather_result,
                weather_start=weather_start,
                weather_end=weather_end
            )
        except ValueError:
            return render_template_string(HTML_TEMPLATE, weather_result="Ошибка: Неверный формат координат.")

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)