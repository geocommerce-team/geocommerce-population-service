from flask import Flask, request, jsonify
import rasterio
from rasterio.windows import from_bounds
import numpy as np
import os

app = Flask(__name__)

POPULATION_TIFF = os.path.join(os.path.dirname(__file__), 'data', 'population.tif')

if not os.path.exists(POPULATION_TIFF):
    raise FileNotFoundError(f"Файл {POPULATION_TIFF} не найден!")

@app.route('/geocommerce/api/population', methods=['GET'])
def get_population():
    try:
        lat_min = float(request.args.get('lat_min'))
        lon_min = float(request.args.get('lon_min'))
        lat_max = float(request.args.get('lat_max'))
        lon_max = float(request.args.get('lon_max'))
    except (TypeError, ValueError):
        return jsonify({"error": "Укажите корректные координаты: lat_min, lon_min, lat_max, lon_max"}), 400

    if not (-90 <= lat_min < lat_max <= 90 and -180 <= lon_min < lon_max <= 180):
        return jsonify({"error": "Некорректные координаты"}), 400

    try:
        with rasterio.open(POPULATION_TIFF) as src:
            if src.crs.to_string() != 'EPSG:4326':
                return jsonify({"error": "Файл должен быть в проекции EPSG:4326"}), 400

            window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)

            data = src.read(1, window=window, boundless=True, fill_value=0)

            data = np.where(np.isnan(data), 0, data)
            total_population = float(np.sum(np.maximum(data, 0)))

        return jsonify({
            "population": round(total_population),
            "bounds": {
                "lat_min": lat_min,
                "lon_min": lon_min,
                "lat_max": lat_max,
                "lon_max": lon_max
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True)