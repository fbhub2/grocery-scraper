import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from normalize import normalize_search_term, parse_product_name, auto_normalize, check_threshold


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

    def test_lett_melk_og_lettmelk_gir_samme_resultat(self):
        assert normalize_search_term("Lett melk 0,5%") == normalize_search_term("Lettmelk 0,5%")

    def test_hel_melk_og_helmelk_gir_samme_resultat(self):
        assert normalize_search_term("Hel melk") == normalize_search_term("Helmelk")

    def test_havre_gryn_og_havregryn_gir_samme_resultat(self):
        assert normalize_search_term("Havre gryn") == normalize_search_term("Havregryn")

    def test_split_compound_slaaes_sammen(self):
        assert normalize_search_term("Lett melk") == "lettmelk"

    def test_lett_melk_med_prosent_beholder_prosent(self):
        result = normalize_search_term("Lett melk 0,5%")
        assert "0,5%" in result
        assert "lettmelk" in result


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
        assert parse_product_name(raw)["raw"] == raw


class TestAutoNormalize:
    def test_compound_split_lettmelk(self):
        assert auto_normalize("lettmelk") == "lett melk"

    def test_compound_split_helmelk(self):
        assert auto_normalize("helmelk") == "hel melk"

    def test_compound_split_uppercase(self):
        assert auto_normalize("LETTMELK") == "lett melk"

    def test_compound_split_havregryn(self):
        assert auto_normalize("havregryn") == "havre gryn"

    def test_compound_split_knekkebrød(self):
        assert auto_normalize("knekkebrød") == "knekke brød"

    def test_volum_stor_L(self):
        assert auto_normalize("Tine 1L") == "tine 1l"

    def test_volum_liter_tekst(self):
        assert auto_normalize("Tine 1 liter") == "tine 1l"

    def test_volum_1000g_til_kg(self):
        assert auto_normalize("Tine 1000g") == "tine 1kg"

    def test_volum_500g_beholdes(self):
        assert auto_normalize("Havre 500g") == "havre 500g"

    def test_camelcase_split(self):
        result = auto_normalize("TineLettmelk")
        assert "tine" in result
        assert "lett" in result
        assert "melk" in result

    def test_lowercase(self):
        assert auto_normalize("SMØR") == "smør"

    def test_ingen_endring_ved_normalt_navn(self):
        assert auto_normalize("smør") == "smør"

    def test_compound_i_lengre_navn(self):
        result = auto_normalize("Tine lettmelk 1L")
        assert result == "tine lett melk 1l"

    def test_volum_med_mellomrom(self):
        assert auto_normalize("Q melk 1,5 l") == "q melk 1,5l"


class TestCheckThreshold:
    def test_absolutt_under(self):
        item = {"threshold_type": "absolute", "threshold_value": 20.0}
        assert check_threshold(item, 19.90, 25.0) is True

    def test_absolutt_over(self):
        item = {"threshold_type": "absolute", "threshold_value": 20.0}
        assert check_threshold(item, 20.10, 25.0) is False

    def test_sale_truffet(self):
        item = {"threshold_type": "sale", "threshold_value": None}
        assert check_threshold(item, 20.0, 25.0) is True   # 80% av snitt

    def test_sale_ikke_truffet(self):
        item = {"threshold_type": "sale", "threshold_value": None}
        assert check_threshold(item, 23.0, 25.0) is False  # 92% av snitt

    def test_relativ_truffet(self):
        item = {"threshold_type": "relative", "threshold_value": 15.0}
        assert check_threshold(item, 21.0, 25.0) is True   # 16% under snitt

    def test_relativ_ikke_truffet(self):
        item = {"threshold_type": "relative", "threshold_value": 15.0}
        assert check_threshold(item, 22.0, 25.0) is False  # 12% under snitt

    def test_ukjent_type_returnerer_false(self):
        item = {"threshold_type": "ukjent", "threshold_value": None}
        assert check_threshold(item, 10.0, 25.0) is False
