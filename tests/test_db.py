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
        return [{"product_name": "Coca-Cola", "brand": "Coca-Cola", "volume": "1,5 l",
                 "price": 24.90, "normal_price": 32.90, "valid_from": "2026-04-28",
                 "valid_to": "2099-12-31", "source": "test", "image_url": None, "valid_week": "18"}]

    def test_add_og_search(self, tmp_db):
        db.add_obs_products(self._sample_products())
        assert len(db.search_obs("coca")) == 1

    def test_get_obs_status_ingen_data(self, tmp_db):
        assert db.get_obs_status()["has_data"] is False

    def test_get_obs_status_med_data(self, tmp_db):
        db.add_obs_products(self._sample_products())
        status = db.get_obs_status()
        assert status["has_data"] is True
        assert status["is_expired"] is False

    def test_clear_expired(self, tmp_db):
        expired = [{**self._sample_products()[0], "valid_to": "2020-01-01"}]
        db.add_obs_products(expired)
        assert db.clear_expired_obs() == 1


class TestPrishistorikk:
    def test_trend_ingen_data(self, tmp_db):
        assert db.get_price_trend("Melk", "Oda") is None

    def test_trend_prisfall(self, tmp_db):
        db.record_price("Melk", "Oda", 22.90)
        db.record_price("Melk", "Oda", 19.90)
        trend = db.get_price_trend("Melk", "Oda")
        assert trend["delta"] < 0
        assert trend["current"] == 19.90

    def test_trend_isolert_per_butikk(self, tmp_db):
        db.record_price("Egg", "Oda", 40.00)
        db.record_price("Egg", "Oda", 38.00)
        db.record_price("Egg", "Meny", 42.00)
        assert db.get_price_trend("Egg", "Oda")["delta"] < 0
        assert db.get_price_trend("Egg", "Meny") is None


class TestEnsureStore:
    def test_idempotent(self, tmp_db):
        sid1 = db.ensure_store("oda")
        sid2 = db.ensure_store("oda")
        assert sid1 == sid2
        assert isinstance(sid1, int)

    def test_ulike_butikker(self, tmp_db):
        assert db.ensure_store("oda") != db.ensure_store("meny")


class TestUpsertProduct:
    def test_idempotent(self, tmp_db):
        sid = db.ensure_store("oda")
        pid1 = db.upsert_product("ext-123", "Tine Lettmelk", sid)
        pid2 = db.upsert_product("ext-123", "Tine Lettmelk", sid)
        assert pid1 == pid2

    def test_get_products(self, tmp_db):
        sid = db.ensure_store("oda")
        db.upsert_product("ext-1", "Tine Lettmelk", sid)
        db.upsert_product("ext-2", "Q Melk", sid)
        products = db.get_products(store_id=sid)
        assert len(products) == 2


class TestNormalisering:
    def test_upsert_normal(self, tmp_db):
        db.upsert_normal("Tine Lettmelk")
        rows = db.list_normals()
        assert any(r["original_name"] == "Tine Lettmelk" for r in rows)

    def test_upsert_normal_idempotent(self, tmp_db):
        db.upsert_normal("Tine Lettmelk")
        db.upsert_normal("Tine Lettmelk")
        assert len(db.list_normals()) == 1

    def test_get_display_name_original(self, tmp_db):
        assert db.get_display_name("Ukjent produkt") == "Ukjent produkt"

    def test_get_display_name_auto(self, tmp_db):
        db.upsert_normal("Tine Lettmelk", auto_name="lett melk")
        assert db.get_display_name("Tine Lettmelk") == "lett melk"

    def test_get_display_name_custom_prioritet(self, tmp_db):
        uid = db.ensure_user("sub-1", "test@example.com", "Test")
        db.upsert_normal("Tine Lettmelk", auto_name="lett melk")
        nid = db.get_normal_id("Tine Lettmelk")
        db.set_custom_name_by_id(nid, "Lettmelk (min)", uid)
        assert db.get_display_name("Tine Lettmelk", user_id=uid) == "Lettmelk (min)"

    def test_list_normals_filter(self, tmp_db):
        db.upsert_normal("Tine Lettmelk")
        db.upsert_normal("Q Helmelk")
        assert len(db.list_normals(filter="melk")) == 2
        assert len(db.list_normals(filter="lett")) == 1


class TestBrukere:
    def test_ensure_user_idempotent(self, tmp_db):
        uid1 = db.ensure_user("sub-1", "a@b.com", "Ola")
        uid2 = db.ensure_user("sub-1", "a@b.com", "Ola")
        assert uid1 == uid2

    def test_get_user_id(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        assert db.get_user_id("sub-1") == uid
        assert db.get_user_id("finnes-ikke") is None


class TestProductPriceHistory:
    def test_save_og_hent(self, tmp_db):
        sid = db.ensure_store("oda")
        pid = db.upsert_product("ext-1", "Tine Lettmelk", sid)
        db.save_price(pid, sid, "2026-05-01", 19.90)
        rows = db.get_price_history_v2(pid)
        assert len(rows) == 1
        assert rows[0]["price"] == 19.90
        assert rows[0]["store"] == "oda"

    def test_ingen_duplikater(self, tmp_db):
        sid = db.ensure_store("oda")
        pid = db.upsert_product("ext-1", "Tine Lettmelk", sid)
        db.save_price(pid, sid, "2026-05-01", 19.90)
        db.save_price(pid, sid, "2026-05-01", 20.00)
        assert len(db.get_price_history_v2(pid)) == 1


class TestShoppingList:
    def test_create_og_list(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        lid = db.create_shopping_list(uid, "Ukeshandel")
        lists = db.get_shopping_lists(uid)
        assert len(lists) == 1
        assert lists[0]["name"] == "Ukeshandel"

    def test_add_og_toggle(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        lid = db.create_shopping_list(uid, "Test")
        iid = db.add_to_shopping_list(lid, "Tine Lettmelk", quantity=2)
        items = db.get_shopping_list_items(lid)
        assert len(items) == 1
        assert items[0]["quantity"] == 2
        assert items[0]["checked"] == 0
        db.toggle_item_checked(iid)
        assert db.get_shopping_list_items(lid)[0]["checked"] == 1

    def test_delete(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        lid = db.create_shopping_list(uid, "Slett meg")
        db.add_to_shopping_list(lid, "Melk")
        db.delete_shopping_list(lid)
        assert db.get_shopping_lists(uid) == []

    def test_archive(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        lid = db.create_shopping_list(uid, "Gammel")
        db.archive_shopping_list(lid)
        assert db.get_shopping_lists(uid) == []


class TestWatchlist:
    def test_add_og_get(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "absolute", 18.0)
        items = db.get_watchlist(uid)
        assert len(items) == 1
        assert items[0]["status"] == "waiting"
        assert items[0]["threshold_value"] == 18.0

    def test_trigger(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "absolute", 18.0)
        wid = db.get_watchlist(uid)[0]["id"]
        db.mark_watchlist_triggered(wid, 17.50, "oda")
        item = db.get_watchlist(uid)[0]
        assert item["status"] == "triggered"
        assert item["triggered_price"] == 17.50

    def test_reset(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "sale")
        wid = db.get_watchlist(uid)[0]["id"]
        db.mark_watchlist_triggered(wid, 17.50, "oda")
        db.reset_watchlist_item(wid)
        assert db.get_watchlist(uid)[0]["status"] == "waiting"

    def test_is_on_watchlist(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        assert db.is_on_watchlist(uid, "Tine Lettmelk") is False
        db.add_to_watchlist(uid, "Tine Lettmelk", "sale")
        assert db.is_on_watchlist(uid, "Tine Lettmelk") is True

    def test_remove(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "sale")
        db.remove_from_watchlist(uid, "Tine Lettmelk")
        assert db.get_watchlist(uid) == []

    def test_upsert_oppdaterer_terskel(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "absolute", 20.0)
        db.add_to_watchlist(uid, "Tine Lettmelk", "absolute", 18.0)
        items = db.get_watchlist(uid)
        assert len(items) == 1
        assert items[0]["threshold_value"] == 18.0


class TestUserSettings:
    def test_standard_verdi_naar_ikke_satt(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        assert db.get_user_setting(uid, "postnummer", "default") == "default"

    def test_set_og_get(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.set_user_setting(uid, "postnummer", "0179")
        assert db.get_user_setting(uid, "postnummer") == "0179"

    def test_oppdatering_overskriver(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.set_user_setting(uid, "postnummer", "0179")
        db.set_user_setting(uid, "postnummer", "5003")
        assert db.get_user_setting(uid, "postnummer") == "5003"

    def test_isolert_per_bruker(self, tmp_db):
        uid1 = db.ensure_user("sub-1", "a@b.com", "Ola")
        uid2 = db.ensure_user("sub-2", "b@b.com", "Kari")
        db.set_user_setting(uid1, "postnummer", "0179")
        assert db.get_user_setting(uid2, "postnummer", "") == ""

    def test_vis_fysiske_toggle(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.set_user_setting(uid, "vis_fysiske_butikker", "1")
        assert db.get_user_setting(uid, "vis_fysiske_butikker", "0") == "1"

    def test_gps_koordinater(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.set_user_setting(uid, "user_lat", "59.9139")
        db.set_user_setting(uid, "user_lon", "10.7522")
        assert db.get_user_setting(uid, "user_lat") == "59.9139"
        assert db.get_user_setting(uid, "user_lon") == "10.7522"

    def test_tom_streng_er_gyldig_verdi(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.set_user_setting(uid, "postnummer", "0179")
        db.set_user_setting(uid, "postnummer", "")
        assert db.get_user_setting(uid, "postnummer") == ""
