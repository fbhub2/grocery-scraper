import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base import split_name_variant, Product


class TestSplitNameVariant:
    def test_ekstraher_liter(self):
        name, variant = split_name_variant("Tine Lettmelk 1,75 l")
        assert "1,75 l" in variant
        assert "1,75" not in name

    def test_ekstraher_gram(self):
        name, variant = split_name_variant("Norvegia 500 g")
        assert "500 g" in variant
        assert "500" not in name

    def test_beholder_prosent_i_navn(self):
        name, variant = split_name_variant("Tine Lettmelk 0,5%")
        assert "0,5%" in name
        assert variant is None

    def test_beholder_prosent_med_volum(self):
        name, variant = split_name_variant("Tine Lettmelk 0,5% 1 l")
        assert "0,5%" in name
        assert variant is not None
        assert "1 l" in variant

    def test_ingen_størrelse(self):
        name, variant = split_name_variant("Havregryn")
        assert name == "Havregryn"
        assert variant is None

    def test_flere_størrelser(self):
        name, variant = split_name_variant("Produkt 500 g 1 l")
        assert variant is not None
        assert "·" in variant

    def test_navn_uten_trailing_komma(self):
        name, _ = split_name_variant("Smør, 500g")
        assert not name.endswith(",")


class TestProduct:
    def test_to_dict(self):
        p = Product(name="Egg", price=29.90, unit_price="2,49 kr/stk", url="/egg")
        d = p.to_dict()
        assert d["name"] == "Egg"
        assert d["price"] == 29.90
        assert d["image_url"] is None

    def test_to_dict_med_image(self):
        p = Product(name="Melk", price=19.90, image_url="https://example.com/img.jpg")
        assert p.to_dict()["image_url"] == "https://example.com/img.jpg"
