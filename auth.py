import os
import secrets
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from authlib.integrations.httpx_client import OAuth2Client

_DOTENV_PATH = Path(__file__).parent / ".env"

_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _load_config() -> dict:
    load_dotenv(dotenv_path=_DOTENV_PATH, override=True)
    return {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501/"),
    }


def get_auth_url() -> str:
    cfg = _load_config()
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state
    client = OAuth2Client(client_id=cfg["client_id"], redirect_uri=cfg["redirect_uri"])
    url, _ = client.create_authorization_url(
        _AUTHORIZATION_URL,
        scope="openid email profile",
        state=state,
    )
    return url


def exchange_code_for_user(code: str) -> dict:
    cfg = _load_config()
    client = OAuth2Client(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=cfg["redirect_uri"],
    )
    client.fetch_token(_TOKEN_URL, code=code)
    resp = client.get(_USERINFO_URL)
    return resp.json()


def get_current_user() -> dict | None:
    return st.session_state.get("user")


def require_login() -> dict:
    """
    Kall øverst i app.py (etter st.set_page_config).
    - Håndterer ?code= callback fra Google
    - Viser login-knapp hvis ikke innlogget → st.stop()
    - Returnerer bruker-dict hvis innlogget
    """
    params = st.query_params

    if "code" in params:
        try:
            user = exchange_code_for_user(params["code"])
            st.session_state["user"] = user
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Innlogging feilet: {e}")
            st.stop()

    user = get_current_user()
    if user:
        return user

    from urllib.parse import urlparse, parse_qs
    cfg = _load_config()
    auth_url = get_auth_url()
    parsed_params = parse_qs(urlparse(auth_url).query)
    uri_in_request = parsed_params.get("redirect_uri", ["ikke funnet"])[0]

    st.title("🛒 Prissammenligning")
    st.info("Logg inn med Google for å bruke appen.")
    st.link_button("Logg inn med Google", auth_url)
    with st.expander("🔍 Debug OAuth"):
        st.write(f"**redirect_uri i .env:** `{repr(cfg['redirect_uri'])}`")
        st.write(f"**redirect_uri sendt til Google:** `{repr(uri_in_request)}`")
        st.write(f"**client_id brukt:** `{cfg['client_id']}`")
        st.write("**Komplett authorization URL:**")
        st.code(auth_url)
        st.caption("Kopier URLen og lim inn i nettleseren for å se hva Google mottar.")
    st.stop()
