import asyncio
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import grocery_scraper_mcp as mcp_mod
from scrapers.base import Product


def run(coro):
    return asyncio.run(coro)


class TestGetStoreList:
    def test_returnerer_butikknavn(self, tmp_db):
        result = mcp_mod.get_store_list()
        assert "Oda" in result
        assert "Meny" in result
        assert "OBS" in result


class TestAddToList:
    def test_legger_til_produkt(self, tmp_db):
        mcp_mod.add_to_list("Melk", store="Oda", price=19.90)
        items = db.get_list("default")
        assert any(i["product_name"] == "Melk" for i in items)

    def test_bekreftelse_i_respons(self, tmp_db):
        result = mcp_mod.add_to_list("Smør")
        assert "Smør" in result


class TestAddMultipleToList:
    def test_legger_til_flere(self, tmp_db):
        mcp_mod.add_multiple_to_list(
            items=[{"product_name": "Egg"}, {"product_name": "Bacon"}],
            list_name="test",
        )
        assert len(db.get_list("test")) == 2

    def test_respons_inneholder_antall(self, tmp_db):
        result = mcp_mod.add_multiple_to_list(
            items=[{"product_name": "A"}, {"product_name": "B"}]
        )
        assert "2" in result


class TestGetList:
    def test_tom_liste(self, tmp_db):
        result = mcp_mod.get_list("tom")
        assert "[]" in result

    def test_liste_med_innhold(self, tmp_db):
        db.add_item("min_liste", "Kaffe")
        result = mcp_mod.get_list("min_liste")
        assert "Kaffe" in result


class TestImportObsCatalog:
    def test_importerer_produkter(self, tmp_db):
        mcp_mod.import_obs_catalog(
            items=[{"product_name": "Pepsi", "price": 22.90}],
            valid_from="2026-04-28",
            valid_to="2099-12-31",
            source_label="test_uke",
        )
        assert len(db.search_obs("pepsi")) == 1

    def test_respons_inneholder_antall(self, tmp_db):
        result = mcp_mod.import_obs_catalog(
            items=[{"product_name": "A", "price": 10.0}, {"product_name": "B", "price": 20.0}],
            valid_from="2026-04-28",
            valid_to="2099-12-31",
        )
        assert "2" in result


class TestSearchProducts:
    def test_søk_returnerer_resultater(self, tmp_db):
        mock_product = Product(name="Tine Lettmelk", price=19.90)
        with patch("grocery_scraper_mcp.oda_search", return_value=[mock_product]), \
             patch("grocery_scraper_mcp.meny_search", return_value=[]):
            result = run(mcp_mod.search_products("melk"))
        assert "Tine Lettmelk" in result

    def test_søk_håndterer_tom_respons(self, tmp_db):
        with patch("grocery_scraper_mcp.oda_search", return_value=[]), \
             patch("grocery_scraper_mcp.meny_search", return_value=[]):
            result = run(mcp_mod.search_products("xyz_finnes_ikke"))
        assert isinstance(result, str)


class TestComparePrices:
    def test_sammenligner_butikker(self, tmp_db):
        oda_p = Product(name="Melk Oda", price=19.90)
        meny_p = Product(name="Melk Meny", price=21.50)
        with patch("grocery_scraper_mcp.oda_search", return_value=[oda_p]), \
             patch("grocery_scraper_mcp.meny_search", return_value=[meny_p]):
            result = run(mcp_mod.compare_prices("melk"))
        assert "Oda" in result
        assert "Meny" in result
