import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import auth


class TestExchangeCodeForUser:
    def test_returnerer_bruker_dict(self):
        mock_userinfo = {
            "sub": "123",
            "email": "a@b.com",
            "name": "Test Bruker",
            "picture": "http://img.example.com/photo.jpg",
        }
        with patch("auth.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.return_value = {"access_token": "tok"}
            instance.get.return_value.json.return_value = mock_userinfo

            result = auth.exchange_code_for_user("fake-code")

        assert result["sub"] == "123"
        assert result["email"] == "a@b.com"
        assert result["name"] == "Test Bruker"

    def test_kaller_fetch_token_med_code(self):
        mock_userinfo = {"sub": "999", "email": "x@y.com", "name": "X", "picture": ""}
        with patch("auth.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.return_value = {"access_token": "tok"}
            instance.get.return_value.json.return_value = mock_userinfo

            auth.exchange_code_for_user("my-code-123")

            instance.fetch_token.assert_called_once()
            call_kwargs = instance.fetch_token.call_args
            assert "my-code-123" in str(call_kwargs)

    def test_kaller_userinfo_endepunkt(self):
        mock_userinfo = {"sub": "1", "email": "e@e.com", "name": "E", "picture": ""}
        with patch("auth.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.return_value = {"access_token": "tok"}
            instance.get.return_value.json.return_value = mock_userinfo

            auth.exchange_code_for_user("code")

            instance.get.assert_called_once_with(auth._USERINFO_URL)
