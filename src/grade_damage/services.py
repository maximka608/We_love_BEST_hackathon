import json

import pyproj
import requests
import shapely.geometry
from shapely.geometry import mapping


def get_city_data(center_lat, center_lon, radii):
    # Fetch OSM data
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      way["building"](around:{radii[-1]}, {center_lat}, {center_lon});
      relation["building"](around:{radii[-1]}, {center_lat}, {center_lon});
    );
    out body;
    >;
    out skel qt;
    """
    response = requests.get(overpass_url, params={'data': query})
    data = response.json()

    # Prepare nodes
    nodes = {element['id']: (element['lon'], element['lat'])
             for element in data['elements'] if element['type'] == 'node'}

    # Zone mapping
    zone_mapping = {
        "0": 'hard',
        "1": 'medium',
        "2": 'small'
    }

    # Projections
    wgs84_to_mercator = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    mercator_to_wgs84 = pyproj.Transformer.from_crs("epsg:3857", "epsg:4326", always_xy=True)

    # Project center
    center_x, center_y = wgs84_to_mercator.transform(center_lon, center_lat)

    # Create zone polygons
    zone_polygons = []
    last_radius = 0
    for radius in radii:
        outer = shapely.geometry.Point(center_x, center_y).buffer(radius)
        inner = shapely.geometry.Point(center_x, center_y).buffer(last_radius)
        ring = outer.difference(inner)
        zone_polygons.append(ring)
        last_radius = radius

    # Process buildings
    buildings = []

    for element in data['elements']:
        if element['type'] == 'way' and 'nodes' in element:
            coords = [nodes[node_id] for node_id in element['nodes'] if node_id in nodes]
            if len(coords) < 3:
                continue

            # Project coordinates
            projected_coords = [wgs84_to_mercator.transform(lon, lat) for lon, lat in coords]
            projected_polygon = shapely.geometry.Polygon(projected_coords)

            if projected_polygon.is_valid and projected_polygon.area > 0:
                # Find zone
                assigned_zone = None
                for idx, zone in enumerate(zone_polygons):
                    if projected_polygon.intersects(zone):
                        assigned_zone = zone_mapping[str(idx)]
                        break

                if assigned_zone is not None:
                    # Convert polygon back to lat/lon
                    latlon_coords = [mercator_to_wgs84.transform(x, y)[::-1] for x, y in
                                     projected_polygon.exterior.coords]
                    latlon_polygon = shapely.geometry.Polygon(latlon_coords)

                    area_m2 = projected_polygon.area
                    buildings.append({
                        'area_m2': area_m2,
                        'zone': assigned_zone,
                        'polygon': latlon_polygon,
                        'tags': element.get('tags', {})
                    })

    buildings = sorted(buildings, key=lambda b: b['area_m2'], reverse=True)

    keep = []
    for b in buildings:
        polygon = b['polygon']
        contained = False
        for kept in keep:
            if polygon.within(kept['polygon']):
                contained = True
                break
        if not contained:
            keep.append(b)

    buildings = keep

    print(f"Processed {len(buildings)} buildings.")

    for b in buildings[:5]:
        print(b)

    zone_colors = {
        'hard': 'red',
        'medium': 'orange',
        'small': 'green'
    }

    buildings_payload = []

    for b in buildings:
        building_data = {
            "area_m2": b["area_m2"],
            "zone": b["zone"],
            "polygon": mapping(b["polygon"]),
            "tags": b['tags']
        }
        buildings_payload.append(building_data)

    payload_json_str = json.dumps(buildings_payload, ensure_ascii=False)
    payload_json = json.loads(payload_json_str)

    return payload_json


def get_destruction_radius(trotil_equivalent):
    k1 = 10  # сильне ураження
    k2 = 20  # середнє ураження
    k3 = 40  # слабке ураження

    r1 = k1 * trotil_equivalent ** (1 / 3)
    r2 = k2 * trotil_equivalent ** (1 / 3)
    r3 = k3 * trotil_equivalent ** (1 / 3)

    return [r1, r2, r3]
