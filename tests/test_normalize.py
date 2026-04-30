import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalize import normalize_search_term, parse_product_name


class TestNormalizeSearchTerm:
    def test_fjerner_liter(self):
        assert normalize_search_term("Tine Lettmelk 1,5 l") == "tine lettmelk"

    def test_fjerner_gram(self):
        assert normalize_search_term("Norvegia Ost 500g") == "norvegia ost"

    def test_fjerner_milliliter(self):
        assert normalize_search_term("Solo 330 ml") == "solo"

    def test_fjerner_kilogram(self):
        assert normalize_search_term("Kjøttdeig 400g") == "kjøttdeig"

    def test_beholder_prosent(self):
        assert "0,5%" in normalize_search_term("Tine Lettmelk 0,5% 1 l")

    def test_lowercase(self):
        assert normalize_search_term("HAVREGRYN") == "havregryn"

    def test_ingen_volum(self):
        assert normalize_search_term("Smør") == "smør"

    def test_trimmer_whitespace(self):
        result = normalize_search_term("  Egg  12 stk  ")
        assert result == result.strip()
        assert "12 stk" not in result


class TestParseProductName:
    def test_ekstraher_liter(self):
        result = parse_product_name("Tine Lettmelk 1,5 l")
        assert result["volume"] == "1,5 l"
        assert result["unit"] == "l"

    def test_ekstraher_gram(self):
        result = parse_product_name("Norvegia 500g")
        assert result["volume"] == "500g"
        assert result["unit"] == "g"

    def test_ingen_volum(self):
        result = parse_product_name("Smør")
        assert result["volume"] is None
        assert result["unit"] is None

    def test_raw_bevares(self):
        raw = "Tine Lettmelk 1,5 l"
        result = parse_product_name(raw)
        assert result["raw"] == raw
