import os
import secrets
from pathlib import Path
from urllib.parse import urlencode
import httpx
import streamlit as st
from dotenv import load_dotenv

_DOTENV_PATH = Path(__file__).parent / ".env"

_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


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
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{_AUTHORIZATION_URL}?{urlencode(params)}"


def exchange_code_for_user(code: str) -> dict:
    cfg = _load_config()
    with httpx.Client() as client:
        token_resp = client.post(
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": cfg["redirect_uri"],
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        user_resp = client.get(
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        return user_resp.json()


def get_current_user() -> dict | None:
    return st.session_state.get("user")


def require_login() -> dict:
    """
    Kall øverst i app.py (etter st.set_page_config).
    Håndterer ?code= callback, viser login-knapp, returnerer bruker-dict.
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

    cfg = _load_config()
    auth_url = get_auth_url()

    st.title("🛒 Prissammenligning")
    st.info("Logg inn med Google for å bruke appen.")
    st.link_button("Logg inn med Google", auth_url)
    with st.expander("🔍 Debug"):
        st.write(f"**client_id:** `{cfg['client_id']}`")
        st.write(f"**redirect_uri:** `{repr(cfg['redirect_uri'])}`")
        st.code(auth_url)
    st.stop()
