import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Hjelpere for mock-responses
# ---------------------------------------------------------------------------

def _mock_response(json_data: dict, status_code: int = 200):
    m = MagicMock()
    m.json.return_value = json_data
    m.raise_for_status.return_value = None
    m.status_code = status_code
    return m


def _oda_search_response(items: list) -> dict:
    return {"items": items}


def _oda_item(name: str, price: str, item_id: int = 1) -> dict:
    return {
        "type": "product",
        "id": item_id,
        "attributes": {
            "name": name,
            "gross_price": price,
            "gross_unit_price": "",
            "unit_price_quantity_abbreviation": "",
            "name_extra": "",
            "front_url": "/produkt/test/",
            "images": [],
        },
    }


def _meny_search_response(hits: list) -> dict:
    return {"products": {"hits": hits}}


def _meny_hit(name: str, price: float, ean: str = "1234567890") -> dict:
    return {
        "description": "",
        "contentData": {
            "_source": {
                "title": name,
                "pricePerUnit": price,
                "comparePricePerUnit": "",
                "compareUnit": "",
                "slugifiedUrl": "/test",
                "imagePath": None,
                "ean": ean,
            }
        },
    }


# ---------------------------------------------------------------------------
# Oda search
# ---------------------------------------------------------------------------

class TestOdaSearch:
    def test_returnerer_produkter(self, tmp_db):
        mock_resp = _mock_response(_oda_search_response([
            _oda_item("Tine Lettmelk", "19.90", item_id=42),
        ]))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            results = search("melk", limit=5)
        assert len(results) == 1
        assert results[0].name == "Tine Lettmelk"
        assert results[0].price == 19.90

    def test_respekterer_limit(self, tmp_db):
        items = [_oda_item(f"Produkt {i}", "10.00", item_id=i) for i in range(10)]
        mock_resp = _mock_response(_oda_search_response(items))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            results = search("test", limit=3)
        assert len(results) == 3

    def test_hopper_over_ikke_produkt_type(self, tmp_db):
        items = [
            {"type": "category", "id": 1, "attributes": {}},
            _oda_item("Smør", "30.00", item_id=2),
        ]
        mock_resp = _mock_response(_oda_search_response(items))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            results = search("smør")
        assert len(results) == 1
        assert results[0].name == "Smør"

    def test_lagrer_produkt_i_db(self, tmp_db):
        import db
        mock_resp = _mock_response(_oda_search_response([
            _oda_item("Tine Lettmelk", "19.90", item_id=99),
        ]))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            search("melk")
        products = db.get_products()
        assert any(p["product_id"] == "99" for p in products)
        assert any(p["store_name"] == "oda" for p in products)

    def test_lagrer_normal_i_db(self, tmp_db):
        import db
        mock_resp = _mock_response(_oda_search_response([
            _oda_item("Tine Lettmelk", "19.90", item_id=1),
        ]))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            search("melk")
        assert any(r["original_name"] == "Tine Lettmelk" for r in db.list_normals())

    def test_tom_respons(self, tmp_db):
        mock_resp = _mock_response(_oda_search_response([]))
        with patch("scrapers.oda.httpx.get", return_value=mock_resp):
            from scrapers.oda import search
            assert search("xyz") == []


# ---------------------------------------------------------------------------
# Meny search
# ---------------------------------------------------------------------------

class TestMenySearch:
    def test_returnerer_produkter(self, tmp_db):
        mock_resp = _mock_response(_meny_search_response([
            _meny_hit("Q Lettmelk", 21.50, ean="1111111111"),
        ]))
        with patch("scrapers.meny.httpx.get", return_value=mock_resp):
            from scrapers.meny import search
            results = search("melk", limit=5)
        assert len(results) == 1
        assert results[0].price == 21.50

    def test_lagrer_produkt_i_db(self, tmp_db):
        import db
        mock_resp = _mock_response(_meny_search_response([
            _meny_hit("Q Lettmelk", 21.50, ean="9999999999"),
        ]))
        with patch("scrapers.meny.httpx.get", return_value=mock_resp):
            from scrapers.meny import search
            search("melk")
        products = db.get_products()
        assert any(p["product_id"] == "9999999999" for p in products)
        assert any(p["store_name"] == "meny" for p in products)

    def test_tom_respons(self, tmp_db):
        mock_resp = _mock_response(_meny_search_response([]))
        with patch("scrapers.meny.httpx.get", return_value=mock_resp):
            from scrapers.meny import search
            assert search("xyz") == []


# ---------------------------------------------------------------------------
# fetch_price — Oda
# ---------------------------------------------------------------------------

class TestOdaFetchPrice:
    def test_returnerer_float(self, tmp_db):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"gross_price": "19.90"}
        mock_resp.raise_for_status.return_value = None

        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=async_client)
        async_client.__aexit__ = AsyncMock(return_value=False)
        async_client.get = AsyncMock(return_value=mock_resp)

        with patch("scrapers.oda.httpx.AsyncClient", return_value=async_client):
            from scrapers.oda import fetch_price
            price = asyncio.run(fetch_price("42"))
        assert price == 19.90

    def test_returnerer_none_ved_feil(self, tmp_db):
        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=async_client)
        async_client.__aexit__ = AsyncMock(return_value=False)
        async_client.get = AsyncMock(side_effect=Exception("Network error"))

        with patch("scrapers.oda.httpx.AsyncClient", return_value=async_client):
            from scrapers.oda import fetch_price
            assert asyncio.run(fetch_price("42")) is None

    def test_returnerer_none_når_ingen_pris(self, tmp_db):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "Tine Lettmelk"}
        mock_resp.raise_for_status.return_value = None

        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=async_client)
        async_client.__aexit__ = AsyncMock(return_value=False)
        async_client.get = AsyncMock(return_value=mock_resp)

        with patch("scrapers.oda.httpx.AsyncClient", return_value=async_client):
            from scrapers.oda import fetch_price
            assert asyncio.run(fetch_price("42")) is None


# ---------------------------------------------------------------------------
# fetch_price — Meny
# ---------------------------------------------------------------------------

class TestMenyFetchPrice:
    def test_returnerer_float(self, tmp_db):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"pricePerUnit": 21.50}
        mock_resp.raise_for_status.return_value = None

        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=async_client)
        async_client.__aexit__ = AsyncMock(return_value=False)
        async_client.get = AsyncMock(return_value=mock_resp)

        with patch("scrapers.meny.httpx.AsyncClient", return_value=async_client):
            from scrapers.meny import fetch_price
            price = asyncio.run(fetch_price("1234567890"))
        assert price == 21.50

    def test_returnerer_none_ved_feil(self, tmp_db):
        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=async_client)
        async_client.__aexit__ = AsyncMock(return_value=False)
        async_client.get = AsyncMock(side_effect=Exception("timeout"))

        with patch("scrapers.meny.httpx.AsyncClient", return_value=async_client):
            from scrapers.meny import fetch_price
            assert asyncio.run(fetch_price("1234567890")) is None
