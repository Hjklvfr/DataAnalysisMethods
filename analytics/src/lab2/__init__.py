import json
from shapely.geometry import shape, Point

BOROUGH_DATA = {}

with open('../data/raw/Borough Boundaries.geojson') as f:
    js = json.load(f)
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        boro_name = feature['properties']['boro_name'].upper()
        BOROUGH_DATA[boro_name] = polygon


def borough_by_coords(point: Point) -> str | None:
    for borough in BOROUGH_DATA:
        if BOROUGH_DATA[borough].contains(point):
            return borough


if __name__ == "__main__":
    print(borough_by_coords('40.667202', '-73.866500'))
    print(borough_by_coords('40.683304', '-73.917274'))
