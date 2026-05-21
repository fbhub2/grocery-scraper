import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ui_helpers import _card_html, _market_badge, CARD_HEIGHT


class TestMarketBadge:
    def test_ingen_badge_for_enkelt_pris(self):
        assert _market_badge(20.0, [20.0]) is None

    def test_ingen_badge_innen_terskel(self):
        # 5% avvik gir ingen badge
        avg = 20.0
        assert _market_badge(avg * 1.05, [avg, avg]) is None
        assert _market_badge(avg * 0.95, [avg, avg]) is None

    def test_gron_badge_mer_enn_10_prosent_under(self):
        badge = _market_badge(18.0, [20.0, 20.0])
        assert badge is not None
        assert "under snitt" in badge
        assert "🟢" in badge

    def test_rod_badge_mer_enn_10_prosent_over(self):
        badge = _market_badge(23.0, [20.0, 20.0])
        assert badge is not None
        assert "over snitt" in badge
        assert "🔴" in badge

    def test_ingen_badge_ved_snittpris_null(self):
        assert _market_badge(0.0, [0.0, 0.0]) is None

    def test_gron_badge_mellom_5_og_10_prosent_under(self):
        # 7% under snitt → badge
        badge = _market_badge(18.6, [20.0, 20.0])
        assert badge is not None
        assert "🟢" in badge


class TestCardHtml:
    def _basic(self, **overrides):
        defaults = dict(
            name="Tine Lettmelk",
            variant="1,75 l",
            price=29.90,
            unit_price="17.09 kr/l",
            image_url="https://example.com/img.jpg",
            url="https://oda.com/no/products/1/",
            market_badge=None,
            on_wl=False,
            on_list=False,
            store="Oda",
            store_color="#e84142",
            query="melk",
            session_token="testtoken",
        )
        return _card_html(**{**defaults, **overrides})

    def test_returnerer_streng(self):
        assert isinstance(self._basic(), str)

    def test_inneholder_produktnavn(self):
        html = self._basic()
        assert "Tine Lettmelk" in html

    def test_inneholder_pris(self):
        html = self._basic()
        assert "kr 29.90" in html

    def test_inneholder_enhetspris(self):
        html = self._basic()
        assert "17.09 kr/l" in html

    def test_inneholder_butikknavn(self):
        html = self._basic()
        assert "Oda" in html

    def test_on_wl_false_aksepteres(self):
        html = self._basic(on_wl=False)
        assert isinstance(html, str)

    def test_on_wl_true_aksepteres(self):
        html = self._basic(on_wl=True)
        assert isinstance(html, str)

    def test_on_list_false_aksepteres(self):
        html = self._basic(on_list=False)
        assert isinstance(html, str)

    def test_on_list_true_aksepteres(self):
        html = self._basic(on_list=True)
        assert isinstance(html, str)

    def test_ingen_card_action_lenker_i_html(self):
        # Ikon-handlinger er native Streamlit-knapper, ikke HTML-lenker
        html = self._basic()
        assert "card_action=wl" not in html
        assert "card_action=li" not in html

    def test_ingen_navigasjonslenker_i_html(self):
        # Ingen href med session-token for korthandlinger
        html = self._basic(session_token="abc123")
        assert "?s=abc123" not in html

    def test_query_param_aksepteres(self):
        html = self._basic(query="lettmelk")
        assert isinstance(html, str)

    def test_session_token_param_aksepteres(self):
        html = self._basic(session_token="abc123")
        assert isinstance(html, str)

    def test_uten_session_token_fungerer(self):
        html = self._basic(session_token="")
        assert isinstance(html, str)
        assert "Tine Lettmelk" in html

    def test_card_har_ikke_inline_ikoner(self):
        # Ikoner (♡ ♥ + ✓) er native Streamlit-knapper, ikke i card-HTML
        html = self._basic()
        assert "♡" not in html
        assert "♥" not in html

    def test_card_height_konstant_definert(self):
        assert isinstance(CARD_HEIGHT, int)
        assert CARD_HEIGHT >= 300

    def test_vis_i_butikk_lenke_vises(self):
        html = self._basic(url="https://oda.com/no/products/1/")
        assert "Vis i butikk" in html
        assert "https://oda.com/no/products/1/" in html

    def test_ingen_lenke_uten_url(self):
        html = self._basic(url=None)
        assert "Vis i butikk" not in html

    def test_fallback_bilde_uten_image_url(self):
        html = self._basic(image_url=None)
        assert "🛒" in html
        assert "<img" not in html

    def test_bilde_med_image_url(self):
        html = self._basic(image_url="https://example.com/img.jpg")
        assert "<img" in html
        assert "https://example.com/img.jpg" in html

    def test_ingen_prisdata_naar_pris_er_none(self):
        html = self._basic(price=None)
        assert "Ingen prisdata" in html

    def test_market_badge_vises(self):
        html = self._basic(market_badge="🟢 11% under snitt")
        assert "under snitt" in html

    def test_obs_status_vises(self):
        html = self._basic(obs_status="OBS tilbud")
        assert "OBS tilbud" in html

    def test_html_escape_i_navn(self):
        html = self._basic(name='<script>alert("xss")</script>')
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_escape_i_url(self):
        html = self._basic(url='https://example.com/?a=1&b=2')
        # URL-escaped i href-attributt
        assert "https://example.com/?a=1&amp;b=2" in html
