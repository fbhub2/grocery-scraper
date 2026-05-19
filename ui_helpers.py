import html as _html_lib
from urllib.parse import quote as _url_quote


def _market_badge(price: float, all_prices: list[float]) -> str | None:
    """Returner badge-tekst hvis prisen avviker >5% fra gjennomsnittet."""
    if len(all_prices) < 2:
        return None
    avg = sum(all_prices) / len(all_prices)
    if avg == 0:
        return None
    pct = (price - avg) / avg * 100
    if pct < -10:
        return f"🟢 {abs(pct):.0f}% under snitt"
    if pct < -5:
        return f"🟢 {abs(pct):.0f}% under snitt"
    if pct > 10:
        return f"🔴 {pct:.0f}% over snitt"
    return None


def _card_html(
    name: str,
    variant: str | None,
    price: float | None,
    unit_price: str | None,
    image_url: str | None,
    url: str | None,
    market_badge: str | None,
    on_wl: bool,
    on_list: bool,
    store: str,
    store_color: str,
    query: str = "",
    obs_status: str | None = None,
) -> str:
    ne = _html_lib.escape(name or "")
    ve = _html_lib.escape(variant or "")
    ie = _html_lib.escape(image_url or "")
    ue = _html_lib.escape(url or "")
    nq = _url_quote(name or "")
    vq = _url_quote(variant or "")
    qq = _url_quote(query or "")
    wl_href = f"?card_action=wl&card_name={nq}&card_var={vq}&card_q={qq}"
    li_href = f"?card_action=li&card_name={nq}&card_q={qq}"

    wl_color = "#ef4444" if on_wl else "#c4c4c4"
    wl_icon = "♥" if on_wl else "♡"
    li_color = "#22c55e" if on_list else "#c4c4c4"
    li_icon = "✓" if on_list else "+"

    ibtn = (
        "display:inline-flex;align-items:center;justify-content:center;"
        "width:32px;height:32px;border-radius:50%;"
        "background:rgba(255,255,255,0.96);"
        "box-shadow:0 1px 5px rgba(0,0,0,0.18);"
        "text-decoration:none;line-height:1;"
    )

    if image_url and isinstance(image_url, str):
        img = f'<img src="{ie}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;" loading="lazy">'
    else:
        img = '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#d1d5db;font-size:3rem;">🛒</div>'

    price_s = (
        f'<span style="font-size:1.3rem;font-weight:700;color:#111827;">kr {price:.2f}</span>'
        if price is not None
        else '<span style="font-size:12px;color:#9ca3af;font-style:italic;">Ingen prisdata</span>'
    )
    up_s = f' <span style="font-size:11px;color:#3b82f6;font-weight:500;">{_html_lib.escape(unit_price)}</span>' if unit_price else ""

    badge_s = ""
    if market_badge:
        bc = "#16a34a" if "under" in market_badge else "#dc2626"
        badge_s = f'<div style="font-size:11px;color:{bc};margin-top:3px;">{_html_lib.escape(market_badge)}</div>'
    if obs_status:
        badge_s += f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">{_html_lib.escape(obs_status)}</div>'

    view_s = f'<a href="{ue}" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;">Vis i butikk ↗</a>' if url else ""

    store_pill = (
        f'<span style="position:absolute;bottom:8px;left:8px;background:{store_color};'
        f'color:white;font-size:9px;font-weight:700;padding:2px 7px;border-radius:9999px;'
        f'letter-spacing:0.04em;opacity:0.88;">{_html_lib.escape(store)}</span>'
    )

    return (
        '<div style="background:white;border-radius:12px;'
        'box-shadow:0 2px 10px rgba(0,0,0,0.08);overflow:hidden;margin-bottom:10px;'
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\">"

        '<div style="position:relative;width:100%;padding-top:100%;background:#f8f9fa;">'
        + img
        + '<div style="position:absolute;top:8px;right:8px;display:flex;flex-direction:column;gap:6px;z-index:2;">'
        + f'<a href="{wl_href}" style="{ibtn}font-size:17px;color:{wl_color};" title="{"Fjern varsel" if on_wl else "Varsle meg"}">{wl_icon}</a>'
        + f'<a href="{li_href}" style="{ibtn}font-size:20px;color:{li_color};font-weight:600;" title="{"Fjern fra liste" if on_list else "Legg i liste"}">{li_icon}</a>'
        + "</div>"
        + store_pill
        + "</div>"

        + '<div style="padding:10px 12px 12px;">'
        + f'<div style="font-size:13px;font-weight:600;color:#111827;line-height:1.35;margin-bottom:2px;">{ne}</div>'
        + f'<div style="font-size:11px;color:#9ca3af;margin-bottom:7px;">{ve}</div>'
        + f'<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:4px;">{price_s}{up_s}</div>'
        + badge_s
        + (f'<div style="margin-top:7px;">{view_s}</div>' if view_s else "")
        + "</div>"
        + "</div>"
    )
