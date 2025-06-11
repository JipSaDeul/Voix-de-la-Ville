import sqlite3
from pathlib import Path
from typing import Final, List, Dict, Optional

DB_PATH: Final = Path(__file__).resolve().parent / "cities.sqlite"


def get_zipcode_by_location(lat: float, lon: float, max_km: float = 120.0) -> Optional[int]:
    """
    Find the nearest zipcode to a given latitude and longitude.
    """
    query = """
    SELECT
        zipcode,
        ROUND(6371 * 2 * ASIN(SQRT(
            POWER(SIN(RADIANS((? - latitude / 10000.0) / 2)), 2) +
            COS(RADIANS(?)) * COS(RADIANS(latitude / 10000.0)) *
            POWER(SIN(RADIANS((? - longitude / 10000.0) / 2)), 2)
        )), 2) AS distanceKm
    FROM Cities
    WHERE 6371 * 2 * ASIN(SQRT(
            POWER(SIN(RADIANS((? - latitude / 10000.0) / 2)), 2) +
            COS(RADIANS(?)) * COS(RADIANS(latitude / 10000.0)) *
            POWER(SIN(RADIANS((? - longitude / 10000.0) / 2)), 2)
        )) <= ?
    ORDER BY distanceKm
    LIMIT 1;
    """
    params = [lat, lat, lon, lat, lat, lon, max_km]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()

    return int(row[0]) if row else None


def get_city_info_by_zipcodes(zipcode_list: List[int]) -> List[Dict[str, str]]:
    """
    Get full city information (zipcode, place, province) for a list of zipcodes.
    """
    if not zipcode_list:
        return []

    placeholders = ','.join(['?'] * len(zipcode_list))
    query = f"""
    SELECT zipcode, place, province
    FROM Cities
    WHERE zipcode IN ({placeholders});
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, zipcode_list)
        rows = cursor.fetchall()

    return [
        {"zipcode": str(row[0]), "place": row[1], "province": row[2]}
        for row in rows
    ]
