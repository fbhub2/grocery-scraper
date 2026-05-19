import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.kassal_stores import haversine, nearest_stores, postnummer_to_coords


class TestHaversine:
    def test_samme_punkt_gir_null(self):
        assert haversine(59.9, 10.7, 59.9, 10.7) == 0.0

    def test_oslo_til_bergen_ca_300km(self):
        # Oslo (59.91, 10.75) → Bergen (60.39, 5.32) ≈ 307 km luftlinje
        dist = haversine(59.91, 10.75, 60.39, 5.32)
        assert 290 < dist < 330

    def test_symmetrisk(self):
        d1 = haversine(59.9, 10.7, 60.4, 5.3)
        d2 = haversine(60.4, 5.3, 59.9, 10.7)
        assert abs(d1 - d2) < 0.001

    def test_positiv_avstand(self):
        assert haversine(0, 0, 1, 1) > 0


class TestNearestStores:
    def _store(self, name, lat, lon, group="REMA"):
        return {"name": name, "group": group, "position": {"lat": lat, "lng": lon}}

    def test_returnerer_naermest_forst(self):
        stores = [
            self._store("Langt borte", 70.0, 10.0),
            self._store("Nær", 59.92, 10.76),
        ]
        result = nearest_stores(59.91, 10.75, stores, limit=5)
        assert result[0]["name"] == "Nær"

    def test_limit_respekteres(self):
        stores = [self._store(f"Butikk{i}", 59.91 + i * 0.01, 10.75) for i in range(10)]
        result = nearest_stores(59.91, 10.75, stores, limit=3)
        assert len(result) == 3

    def test_dist_km_felt_legges_til(self):
        stores = [self._store("Test", 59.92, 10.76)]
        result = nearest_stores(59.91, 10.75, stores)
        assert "_dist_km" in result[0]
        assert isinstance(result[0]["_dist_km"], float)

    def test_hopper_over_uten_koordinater(self):
        stores = [{"name": "Uten pos", "position": {}}]
        result = nearest_stores(59.91, 10.75, stores)
        assert result == []

    def test_hopper_over_null_koordinater(self):
        stores = [{"name": "Null pos", "position": {"lat": 0, "lng": 0}}]
        result = nearest_stores(59.91, 10.75, stores)
        assert result == []

    def test_group_filter(self):
        stores = [
            self._store("Rema-butikk", 59.92, 10.76, group="REMA"),
            self._store("Kiwi-butikk", 59.93, 10.77, group="KIWI"),
        ]
        result = nearest_stores(59.91, 10.75, stores, group_filter="REMA")
        assert len(result) == 1
        assert result[0]["name"] == "Rema-butikk"

    def test_sortert_pa_avstand(self):
        stores = [
            self._store("Langt", 62.0, 10.75),
            self._store("Nært", 59.92, 10.75),
            self._store("Midt", 60.5, 10.75),
        ]
        result = nearest_stores(59.91, 10.75, stores, limit=3)
        dists = [r["_dist_km"] for r in result]
        assert dists == sorted(dists)

    def test_tom_liste(self):
        assert nearest_stores(59.91, 10.75, []) == []


class TestPostnummerToCoords:
    def test_gyldig_postnummer_returnerer_tuple(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "adresser": [{"representasjonspunkt": {"lat": 59.91, "lon": 10.75}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapers.kassal_stores.httpx.get", return_value=mock_resp):
            coords = postnummer_to_coords("0179")

        assert coords == (59.91, 10.75)

    def test_ukjent_postnummer_returnerer_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"adresser": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapers.kassal_stores.httpx.get", return_value=mock_resp):
            assert postnummer_to_coords("9999") is None

    def test_nettverksfeil_returnerer_none(self):
        with patch("scrapers.kassal_stores.httpx.get", side_effect=Exception("timeout")):
            assert postnummer_to_coords("0179") is None

    def test_manglende_koordinater_returnerer_none(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "adresser": [{"representasjonspunkt": {}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("scrapers.kassal_stores.httpx.get", return_value=mock_resp):
            assert postnummer_to_coords("0179") is None
