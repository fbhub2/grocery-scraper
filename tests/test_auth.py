import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import auth


class TestExchangeCodeForUser:
    def _mock_httpx(self, token_json: dict, user_json: dict):
        mock_client = MagicMock()
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = token_json
        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = user_json
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_token_resp
        mock_client.get.return_value = mock_user_resp
        return mock_client

    def test_returnerer_bruker_dict(self):
        user_json = {"sub": "123", "email": "a@b.com", "name": "Test", "picture": "http://img"}
        mock_client = self._mock_httpx({"access_token": "tok"}, user_json)

        with patch("auth.httpx.Client", return_value=mock_client):
            result = auth.exchange_code_for_user("fake-code")

        assert result["sub"] == "123"
        assert result["email"] == "a@b.com"

    def test_kaller_token_endepunkt_med_code(self):
        mock_client = self._mock_httpx({"access_token": "tok"}, {"sub": "1", "email": "", "name": "", "picture": ""})

        with patch("auth.httpx.Client", return_value=mock_client):
            auth.exchange_code_for_user("my-code-123")

        call_kwargs = mock_client.post.call_args
        assert "my-code-123" in str(call_kwargs)

    def test_kaller_userinfo_endepunkt(self):
        mock_client = self._mock_httpx({"access_token": "tok"}, {"sub": "1", "email": "", "name": "", "picture": ""})

        with patch("auth.httpx.Client", return_value=mock_client):
            auth.exchange_code_for_user("code")

        mock_client.get.assert_called_once_with(
            auth._USERINFO_URL,
            headers={"Authorization": "Bearer tok"},
        )
