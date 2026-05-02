import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import tasks


# ---------------------------------------------------------------------------
# Hjelper: sett opp ett overvåket produkt
# ---------------------------------------------------------------------------

def _setup_watched_product(store_name="oda", original_name="Tine Lettmelk",
                            ext_id="ext-1", user_sub="sub-1"):
    uid = db.ensure_user(user_sub, "a@b.com", "Ola")
    sid = db.ensure_store(store_name)
    pid = db.upsert_product(ext_id, original_name, sid)
    db.upsert_normal(original_name)
    db.add_to_price_fetch(pid, uid)
    return {"uid": uid, "sid": sid, "pid": pid, "original_name": original_name}


# ---------------------------------------------------------------------------
# TestRunAutoNormalize
# ---------------------------------------------------------------------------

class TestRunAutoNormalize:
    def test_oppdaterer_auto_name(self, tmp_db):
        db.upsert_normal("lettmelk")
        tasks.run_auto_normalize()
        row = next(r for r in db.list_normals() if r["original_name"] == "lettmelk")
        assert row["auto_name"] == "lett melk"

    def test_hopper_over_eksisterende(self, tmp_db):
        db.upsert_normal("lettmelk", auto_name="eksisterende")
        tasks.run_auto_normalize()
        row = next(r for r in db.list_normals() if r["original_name"] == "lettmelk")
        assert row["auto_name"] == "eksisterende"

    def test_returnerer_antall(self, tmp_db):
        db.upsert_normal("lettmelk")
        db.upsert_normal("helmelk")
        db.upsert_normal("smør", auto_name="allerede satt")
        assert tasks.run_auto_normalize() == 2

    def test_tom_tabell(self, tmp_db):
        assert tasks.run_auto_normalize() == 0

    def test_normaliserer_flere(self, tmp_db):
        db.upsert_normal("havregryn")
        db.upsert_normal("knekkebrød")
        tasks.run_auto_normalize()
        normals = {r["original_name"]: r["auto_name"] for r in db.list_normals()}
        assert normals["havregryn"] == "havre gryn"
        assert normals["knekkebrød"] == "knekke brød"


# ---------------------------------------------------------------------------
# TestGetAllPriceFetchProducts
# ---------------------------------------------------------------------------

class TestGetAllPriceFetchProducts:
    def test_tom_tabell(self, tmp_db):
        assert db.get_all_price_fetch_products() == []

    def test_returnerer_produkt(self, tmp_db):
        _setup_watched_product()
        products = db.get_all_price_fetch_products()
        assert len(products) == 1
        assert products[0]["original_name"] == "Tine Lettmelk"
        assert products[0]["store_name"] == "oda"

    def test_unike_produkter_på_tvers_av_brukere(self, tmp_db):
        sid = db.ensure_store("oda")
        pid = db.upsert_product("ext-1", "Tine Lettmelk", sid)
        uid1 = db.ensure_user("sub-1", "a@b.com", "A")
        uid2 = db.ensure_user("sub-2", "b@b.com", "B")
        db.add_to_price_fetch(pid, uid1)
        db.add_to_price_fetch(pid, uid2)
        assert len(db.get_all_price_fetch_products()) == 1

    def test_flere_produkter(self, tmp_db):
        _setup_watched_product(store_name="oda", ext_id="ext-1", user_sub="sub-1")
        _setup_watched_product(store_name="meny", ext_id="ext-2", user_sub="sub-2",
                               original_name="Q Melk")
        assert len(db.get_all_price_fetch_products()) == 2


# ---------------------------------------------------------------------------
# TestGetWatchlistByName
# ---------------------------------------------------------------------------

class TestGetWatchlistByName:
    def test_ingen_treff(self, tmp_db):
        assert db.get_watchlist_by_name("Finnes ikke") == []

    def test_finner_waiting(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "sale")
        items = db.get_watchlist_by_name("Tine Lettmelk")
        assert len(items) == 1

    def test_ekskluderer_triggered(self, tmp_db):
        uid = db.ensure_user("sub-1", "a@b.com", "Ola")
        db.add_to_watchlist(uid, "Tine Lettmelk", "sale")
        wid = db.get_watchlist(uid)[0]["id"]
        db.mark_watchlist_triggered(wid, 17.0, "oda")
        assert db.get_watchlist_by_name("Tine Lettmelk") == []


# ---------------------------------------------------------------------------
# TestRunPriceFetch
# ---------------------------------------------------------------------------

class TestRunPriceFetch:
    def test_ingen_produkter(self, tmp_db):
        result = tasks.run_price_fetch()
        assert result == {"fetched": 0, "errors": 0, "triggered": 0}

    def test_henter_og_lagrer_pris(self, tmp_db):
        info = _setup_watched_product(store_name="oda", ext_id="ext-1")

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=19.90)):
            result = tasks.run_price_fetch()

        assert result["fetched"] == 1
        assert result["errors"] == 0
        rows = db.get_price_history_v2(info["pid"])
        assert len(rows) == 1
        assert rows[0]["price"] == 19.90

    def test_teller_feil_når_ingen_pris(self, tmp_db):
        _setup_watched_product(store_name="oda", ext_id="ext-1")

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=None)):
            result = tasks.run_price_fetch()

        assert result["fetched"] == 0
        assert result["errors"] == 1

    def test_ingen_duplikater_samme_dag(self, tmp_db):
        info = _setup_watched_product(store_name="oda", ext_id="ext-1")

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=19.90)):
            tasks.run_price_fetch()
            tasks.run_price_fetch()

        assert len(db.get_price_history_v2(info["pid"])) == 1

    def test_trigger_watchlist_ved_absolutt_terskel(self, tmp_db):
        info = _setup_watched_product(store_name="oda", ext_id="ext-1")
        # Legg inn historikk for snitt-beregning
        db.save_price(info["pid"], info["sid"], "2026-04-01", 25.0)
        db.save_price(info["pid"], info["sid"], "2026-04-15", 25.0)
        # Watchlist: varsle hvis < 20 kr
        db.add_to_watchlist(info["uid"], info["original_name"], "absolute", 20.0)

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=18.0)):
            result = tasks.run_price_fetch()

        assert result["triggered"] == 1
        wl = db.get_watchlist(info["uid"])
        assert wl[0]["status"] == "triggered"
        assert wl[0]["triggered_price"] == 18.0

    def test_trigger_ikke_ved_for_høy_pris(self, tmp_db):
        info = _setup_watched_product(store_name="oda", ext_id="ext-1")
        db.save_price(info["pid"], info["sid"], "2026-04-01", 25.0)
        db.add_to_watchlist(info["uid"], info["original_name"], "absolute", 15.0)

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=22.0)):
            result = tasks.run_price_fetch()

        assert result["triggered"] == 0
        assert db.get_watchlist(info["uid"])[0]["status"] == "waiting"

    def test_trigger_sale_terskel(self, tmp_db):
        info = _setup_watched_product(store_name="oda", ext_id="ext-1")
        # Snitt: 25 kr — 20 kr er 80% av snitt → treffer sale (< 90%)
        db.save_price(info["pid"], info["sid"], "2026-04-01", 25.0)
        db.save_price(info["pid"], info["sid"], "2026-04-15", 25.0)
        db.add_to_watchlist(info["uid"], info["original_name"], "sale")

        with patch("scrapers.oda.fetch_price", new=AsyncMock(return_value=20.0)):
            result = tasks.run_price_fetch()

        assert result["triggered"] == 1

    def test_meny_produkt_bruker_meny_scraper(self, tmp_db):
        info = _setup_watched_product(store_name="meny", ext_id="ean-999",
                                       original_name="Q Melk")

        with patch("scrapers.meny.fetch_price", new=AsyncMock(return_value=21.50)):
            result = tasks.run_price_fetch()

        assert result["fetched"] == 1
        rows = db.get_price_history_v2(info["pid"])
        assert rows[0]["price"] == 21.50
