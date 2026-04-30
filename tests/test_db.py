import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import db


class TestHandleliste:
    def test_add_og_get(self, tmp_db):
        db.add_item("default", "Melk", store="Oda", price=19.90)
        items = db.get_list("default")
        assert len(items) == 1
        assert items[0]["product_name"] == "Melk"
        assert items[0]["store"] == "Oda"

    def test_remove_by_name(self, tmp_db):
        db.add_item("default", "Smør")
        db.remove_item("default", "Smør")
        assert db.get_list("default") == []

    def test_remove_by_id(self, tmp_db):
        db.add_item("default", "Egg")
        item = db.get_list("default")[0]
        db.remove_item("default", "Egg", item_id=item["id"])
        assert db.get_list("default") == []

    def test_lagrer_volume_og_search_term(self, tmp_db):
        db.add_item("default", "Lettmelk", volume="1,5 l", search_term="lettmelk")
        item = db.get_list("default")[0]
        assert item["volume"] == "1,5 l"
        assert item["search_term"] == "lettmelk"

    def test_flere_lister(self, tmp_db):
        db.add_item("liste1", "Melk")
        db.add_item("liste2", "Smør")
        assert len(db.get_list("liste1")) == 1
        assert len(db.get_list("liste2")) == 1
        assert db.get_list("liste1")[0]["product_name"] == "Melk"

    def test_get_all_lists(self, tmp_db):
        db.add_item("liste1", "Melk")
        db.add_item("liste2", "Smør")
        lists = db.get_all_lists()
        assert "liste1" in lists
        assert "liste2" in lists


class TestObs:
    def _sample_products(self):
        return [
            {
                "product_name": "Coca-Cola",
                "brand": "Coca-Cola",
                "volume": "1,5 l",
                "price": 24.90,
                "normal_price": 32.90,
                "valid_from": "2026-04-28",
                "valid_to": "2099-12-31",
                "source": "test",
                "image_url": None,
                "valid_week": "18",
            }
        ]

    def test_add_og_search(self, tmp_db):
        db.add_obs_products(self._sample_products())
        results = db.search_obs("coca")
        assert len(results) == 1
        assert results[0]["product_name"] == "Coca-Cola"

    def test_search_case_insensitive(self, tmp_db):
        db.add_obs_products(self._sample_products())
        assert len(db.search_obs("COCA")) == 1

    def test_get_obs_status_ingen_data(self, tmp_db):
        status = db.get_obs_status()
        assert status["has_data"] is False

    def test_get_obs_status_med_data(self, tmp_db):
        db.add_obs_products(self._sample_products())
        status = db.get_obs_status()
        assert status["has_data"] is True
        assert status["total_products"] == 1
        assert status["is_expired"] is False

    def test_clear_expired(self, tmp_db):
        expired = [{**self._sample_products()[0], "valid_to": "2020-01-01"}]
        db.add_obs_products(expired)
        removed = db.clear_expired_obs()
        assert removed == 1
        assert db.get_obs_status()["has_data"] is False


class TestPrishistorikk:
    def test_record_og_trend_ingen_data(self, tmp_db):
        assert db.get_price_trend("Melk", "Oda") is None

    def test_record_og_trend_ett_punkt(self, tmp_db):
        db.record_price("Melk", "Oda", 19.90)
        assert db.get_price_trend("Melk", "Oda") is None

    def test_trend_prisfall(self, tmp_db):
        db.record_price("Melk", "Oda", 22.90)
        db.record_price("Melk", "Oda", 19.90)
        trend = db.get_price_trend("Melk", "Oda")
        assert trend is not None
        assert trend["delta"] < 0
        assert trend["current"] == 19.90
        assert trend["previous"] == 22.90

    def test_trend_prisøkning(self, tmp_db):
        db.record_price("Smør", "Meny", 30.00)
        db.record_price("Smør", "Meny", 35.00)
        trend = db.get_price_trend("Smør", "Meny")
        assert trend["delta"] > 0

    def test_trend_isolert_per_butikk(self, tmp_db):
        db.record_price("Egg", "Oda", 40.00)
        db.record_price("Egg", "Oda", 38.00)
        db.record_price("Egg", "Meny", 42.00)
        oda_trend = db.get_price_trend("Egg", "Oda")
        meny_trend = db.get_price_trend("Egg", "Meny")
        assert oda_trend["delta"] < 0
        assert meny_trend is None
