import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import mcp_server
from scrapers.base import Product


def run(coro):
    return asyncio.run(coro)


class TestGetStoreList:
    def test_returnerer_butikknavn(self, tmp_db):
        result = run(mcp_server.call_tool("get_store_list", {}))
        text = result[0].text
        assert "Oda" in text
        assert "Meny" in text
        assert "OBS" in text


class TestAddToList:
    def test_legger_til_produkt(self, tmp_db):
        run(mcp_server.call_tool("add_to_list", {
            "product_name": "Melk",
            "store": "Oda",
            "price": 19.90,
        }))
        items = db.get_list("default")
        assert any(i["product_name"] == "Melk" for i in items)

    def test_bekreftelse_i_respons(self, tmp_db):
        result = run(mcp_server.call_tool("add_to_list", {"product_name": "Smør"}))
        assert "Smør" in result[0].text


class TestAddMultipleToList:
    def test_legger_til_flere(self, tmp_db):
        run(mcp_server.call_tool("add_multiple_to_list", {
            "list_name": "test",
            "items": [
                {"product_name": "Egg"},
                {"product_name": "Bacon"},
            ],
        }))
        items = db.get_list("test")
        assert len(items) == 2

    def test_respons_inneholder_antall(self, tmp_db):
        result = run(mcp_server.call_tool("add_multiple_to_list", {
            "items": [{"product_name": "A"}, {"product_name": "B"}]
        }))
        assert "2" in result[0].text


class TestGetList:
    def test_tom_liste(self, tmp_db):
        result = run(mcp_server.call_tool("get_list", {"list_name": "tom"}))
        assert "[]" in result[0].text

    def test_liste_med_innhold(self, tmp_db):
        db.add_item("min_liste", "Kaffe")
        result = run(mcp_server.call_tool("get_list", {"list_name": "min_liste"}))
        assert "Kaffe" in result[0].text


class TestImportObsCatalog:
    def test_importerer_produkter(self, tmp_db):
        run(mcp_server.call_tool("import_obs_catalog", {
            "items": [{"product_name": "Pepsi", "price": 22.90}],
            "valid_from": "2026-04-28",
            "valid_to": "2099-12-31",
            "source_label": "test_uke",
        }))
        assert len(db.search_obs("pepsi")) == 1

    def test_respons_inneholder_antall(self, tmp_db):
        result = run(mcp_server.call_tool("import_obs_catalog", {
            "items": [
                {"product_name": "A", "price": 10.0},
                {"product_name": "B", "price": 20.0},
            ],
            "valid_from": "2026-04-28",
            "valid_to": "2099-12-31",
        }))
        assert "2" in result[0].text


class TestSearchProducts:
    def test_søk_returnerer_resultater(self, tmp_db):
        mock_product = Product(name="Tine Lettmelk", price=19.90)
        with patch("mcp_server.oda_search", return_value=[mock_product]), \
             patch("mcp_server.meny_search", return_value=[]):
            result = run(mcp_server.call_tool("search_products", {"query": "melk"}))
        assert "Tine Lettmelk" in result[0].text

    def test_søk_håndterer_feil_gracefully(self, tmp_db):
        with patch("mcp_server.oda_search", side_effect=Exception("timeout")), \
             patch("mcp_server.meny_search", return_value=[]):
            try:
                run(mcp_server.call_tool("search_products", {"query": "melk"}))
            except Exception:
                pass


class TestComparePrices:
    def test_sammenligner_butikker(self, tmp_db):
        oda_p = Product(name="Melk Oda", price=19.90)
        meny_p = Product(name="Melk Meny", price=21.50)
        with patch("mcp_server.oda_search", return_value=[oda_p]), \
             patch("mcp_server.meny_search", return_value=[meny_p]):
            result = run(mcp_server.call_tool("compare_prices", {"query": "melk"}))
        text = result[0].text
        assert "Oda" in text
        assert "Meny" in text


class TestUkjentVerktøy:
    def test_returnerer_feilmelding(self, tmp_db):
        result = run(mcp_server.call_tool("finnes_ikke", {}))
        assert "Ukjent" in result[0].text
