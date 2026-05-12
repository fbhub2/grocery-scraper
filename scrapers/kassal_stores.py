import math
import httpx
import os


def _headers() -> dict:
    return {"Authorization": f"Bearer {os.environ.get('KASSAL_API_KEY', '')}"}


def fetch_physical_stores() -> list[dict]:
    """Hent alle fysiske butikker fra Kassal med navn, adresse og GPS-posisjon."""
    stores = []
    page = 1
    try:
        while True:
            r = httpx.get(
                "https://kassal.app/api/v1/physical-stores",
                params={"page": page, "size": 100},
                headers=_headers(),
                timeout=15,
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            if not data:
                break
            stores.extend(data)
            if len(data) < 100:
                break
            page += 1
    except Exception:
        pass
    return stores


def postnummer_to_coords(pnr: str) -> tuple[float, float] | None:
    """Slå opp lat/lon for et norsk postnummer via GeoNorge-API."""
    try:
        r = httpx.get(
            "https://ws.geonorge.no/adresser/v1/sok",
            params={"postnummer": pnr, "treffPerSide": 1, "sokemodus": "OR"},
            timeout=8,
        )
        r.raise_for_status()
        addresses = r.json().get("adresser", [])
        if addresses:
            pt = addresses[0].get("representasjonspunkt", {})
            lat = pt.get("lat")
            lon = pt.get("lon")
            if lat and lon:
                return float(lat), float(lon)
    except Exception:
        pass
    return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Beregn avstand i km mellom to GPS-koordinater (haversine)."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_stores(
    user_lat: float,
    user_lon: float,
    stores: list[dict],
    limit: int = 5,
    group_filter: str | None = None,
) -> list[dict]:
    """Returner nærmeste butikker sortert på avstand, med km-felt lagt til."""
    result = []
    for s in stores:
        pos = s.get("position") or {}
        try:
            slat = float(pos.get("lat", 0))
            slon = float(pos.get("lng", 0))
        except (TypeError, ValueError):
            continue
        if slat == 0 and slon == 0:
            continue
        if group_filter and group_filter.upper() not in (s.get("group") or "").upper():
            continue
        dist = haversine(user_lat, user_lon, slat, slon)
        result.append({**s, "_dist_km": round(dist, 1)})
    result.sort(key=lambda x: x["_dist_km"])
    return result[:limit]
