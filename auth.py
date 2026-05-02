import os
import secrets
import streamlit as st
from dotenv import load_dotenv
from authlib.integrations.httpx_client import OAuth2Client

load_dotenv()

_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth/callback")

_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_auth_url() -> str:
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state
    client = OAuth2Client(client_id=_CLIENT_ID, redirect_uri=_REDIRECT_URI)
    url, _ = client.create_authorization_url(
        _AUTHORIZATION_URL,
        scope="openid email profile",
        state=state,
    )
    return url


def exchange_code_for_user(code: str) -> dict:
    client = OAuth2Client(
        client_id=_CLIENT_ID,
        client_secret=_CLIENT_SECRET,
        redirect_uri=_REDIRECT_URI,
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

    st.title("🛒 Prissammenligning")
    st.info("Logg inn med Google for å bruke appen.")
    st.link_button("Logg inn med Google", get_auth_url())
    st.stop()
