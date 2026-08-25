#!/usr/bin/env python3
"""
infrastructure/google_gmail/client.py テスト
============================================

実際の Gmail API は呼ばず、GoogleGmailClient の _build_service をモック差し替え。
"""

import base64
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from domain.exceptions import GmailApiError, MessageNotFoundError
from domain.types.credentials import OAuthCredentials
from domain.types.service_account import ServiceAccountCredentials
from infrastructure.google_gmail.client import GoogleGmailClient


def _fake_credentials() -> OAuthCredentials:
    return {
        "access_token": "tok",
        "refresh_token": "rt",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "cid",
        "client_secret": "secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expires_at": datetime(2099, 12, 31, tzinfo=timezone.utc),
    }


def _build_fake_service(
    list_pages: list[dict],
    get_responses: dict | None = None,
    labels: list[dict] | None = None,
) -> MagicMock:
    """
    Gmail API service のモック。
    list_pages: [{messages: [{id:...}], nextPageToken: str | None}, ...] のページ列
    get_responses: {message_id: {id, raw, ...}}
    labels: [{id, name, type}, ...]
    """
    service = MagicMock()

    # users().messages().list().execute() がページを順次返す
    list_mock = MagicMock()
    list_mock.execute.side_effect = list_pages
    service.users.return_value.messages.return_value.list.return_value = list_mock

    # users().messages().get(...).execute()
    def get_side_effect(userId: str, id: str, format: str) -> MagicMock:
        get_mock = MagicMock()
        if get_responses and id in get_responses:
            get_mock.execute.return_value = get_responses[id]
        else:
            from googleapiclient.errors import HttpError

            get_mock.execute.side_effect = HttpError(
                resp=MagicMock(status=404, reason="Not Found"),
                content=b'{"error": {"code": 404}}',
            )
        return get_mock

    service.users.return_value.messages.return_value.get.side_effect = get_side_effect

    # users().labels().list().execute()
    labels_mock = MagicMock()
    labels_mock.execute.return_value = {"labels": labels or []}
    service.users.return_value.labels.return_value.list.return_value = labels_mock

    return service


def _make_client(service: MagicMock) -> GoogleGmailClient:
    """GoogleGmailClient を作り、_service をモックに差し替え"""
    client = GoogleGmailClient.__new__(GoogleGmailClient)
    client._credentials = _fake_credentials()
    client._service_account_credentials = None
    client._user_id = "me"
    client._page_size = 100
    client._scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    client._service = service
    return client


# =============================================================================
# list_message_ids
# =============================================================================


class TestListMessageIds:
    @pytest.mark.unit
    def test_empty_page_returns_nothing(self) -> None:
        service = _build_fake_service(list_pages=[{"messages": []}])
        client = _make_client(service)
        ids = list(client.list_message_ids("query"))
        assert ids == []

    @pytest.mark.unit
    def test_single_page_returns_all_ids(self) -> None:
        service = _build_fake_service(
            list_pages=[{"messages": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}]
        )
        client = _make_client(service)
        ids = list(client.list_message_ids("query"))
        assert ids == ["a", "b", "c"]

    @pytest.mark.unit
    def test_multiple_pages_traversed(self) -> None:
        service = _build_fake_service(
            list_pages=[
                {
                    "messages": [{"id": "a"}, {"id": "b"}],
                    "nextPageToken": "tok1",
                },
                {
                    "messages": [{"id": "c"}, {"id": "d"}],
                },
            ]
        )
        client = _make_client(service)
        ids = list(client.list_message_ids("query"))
        assert ids == ["a", "b", "c", "d"]

    @pytest.mark.unit
    def test_max_results_limits_output(self) -> None:
        service = _build_fake_service(
            list_pages=[{"messages": [{"id": str(i)} for i in range(10)]}]
        )
        client = _make_client(service)
        ids = list(client.list_message_ids("query", max_results=3))
        assert ids == ["0", "1", "2"]

    @pytest.mark.unit
    def test_api_failure_raises_gmail_api_error(self) -> None:
        service = MagicMock()
        service.users.return_value.messages.return_value.list.return_value.execute.side_effect = RuntimeError(
            "network down"
        )
        client = _make_client(service)
        with pytest.raises(GmailApiError, match="network down"):
            list(client.list_message_ids("q"))


# =============================================================================
# fetch_message
# =============================================================================


class TestFetchMessage:
    @pytest.mark.unit
    def test_fetch_decodes_raw_mime(self) -> None:
        raw = b"From: test@example.com\r\nSubject: hello\r\n\r\nbody"
        raw_b64 = base64.urlsafe_b64encode(raw).decode("ascii")
        service = _build_fake_service(
            list_pages=[],
            get_responses={
                "id1": {
                    "id": "id1",
                    "threadId": "thr1",
                    "labelIds": ["INBOX"],
                    "snippet": "body",
                    "internalDate": "1744000000000",  # ms
                    "raw": raw_b64,
                    "sizeEstimate": len(raw),
                }
            },
        )
        client = _make_client(service)
        msg = client.fetch_message("id1")
        assert msg["gmail_id"] == "id1"
        assert msg["thread_id"] == "thr1"
        assert msg["label_ids"] == ["INBOX"]
        assert msg["raw_mime"] == raw
        assert msg["size_estimate"] == len(raw)
        # internalDate の復号
        assert msg["internal_date"].tzinfo is not None

    @pytest.mark.unit
    def test_missing_message_raises_not_found(self) -> None:
        service = _build_fake_service(list_pages=[], get_responses={})
        client = _make_client(service)
        with pytest.raises(MessageNotFoundError):
            client.fetch_message("nonexistent")


# =============================================================================
# list_labels
# =============================================================================


class TestListLabels:
    @pytest.mark.unit
    def test_returns_labels(self) -> None:
        labels = [
            {"id": "INBOX", "name": "Inbox", "type": "system"},
            {"id": "Label_1", "name": "Work", "type": "user"},
        ]
        service = _build_fake_service(list_pages=[], labels=labels)
        client = _make_client(service)
        assert client.list_labels() == labels

    @pytest.mark.unit
    def test_empty_labels(self) -> None:
        service = _build_fake_service(list_pages=[], labels=[])
        client = _make_client(service)
        assert client.list_labels() == []


# =============================================================================
# estimate_count
# =============================================================================


class TestEstimateCount:
    @pytest.mark.unit
    def test_returns_result_size_estimate(self) -> None:
        service = MagicMock()
        service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "resultSizeEstimate": 42,
        }
        client = _make_client(service)
        assert client.estimate_count("q") == 42


# =============================================================================
# v0.2.0: Service Account initialization
# =============================================================================


def _fake_sa_credentials() -> ServiceAccountCredentials:
    return {
        "type": "service_account",
        "project_id": "p",
        "private_key_id": "kid",
        "private_key": "key",
        "client_email": "sa@p.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "",
        "token_uri": "",
        "auth_provider_x509_cert_url": "",
        "client_x509_cert_url": "",
        "subject": "user@example.com",
    }


class TestConstructorValidation:
    @pytest.mark.unit
    def test_both_none_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="required"):
            GoogleGmailClient()  # type: ignore[call-arg]

    @pytest.mark.unit
    def test_both_specified_raises_value_error(self) -> None:
        from domain.types.service_account import ServiceAccountCredentials

        creds = _fake_credentials()
        sa_creds: ServiceAccountCredentials = _fake_sa_credentials()
        with pytest.raises(ValueError, match="mutually exclusive"):
            GoogleGmailClient(
                credentials=creds,
                service_account_credentials=sa_creds,
            )


class TestServiceAccountBuild:
    @pytest.mark.unit
    def test_build_service_uses_sa_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        SA credentials 指定時、_build_service が
        _to_google_service_account_credentials を呼ぶ。
        """
        from infrastructure.google_gmail import client as client_module

        captured_sa: list = []

        def fake_to_sa(creds: Any, scopes: Any) -> MagicMock:
            captured_sa.append((creds, scopes))
            return MagicMock(name="SA-Creds")

        def fake_to_oauth(creds: Any) -> MagicMock:
            raise AssertionError("OAuth path must not be taken")

        def fake_build(*args: Any, **kwargs: Any) -> MagicMock:
            return MagicMock(name="Service")

        monkeypatch.setattr(
            client_module, "_to_google_service_account_credentials", fake_to_sa
        )
        monkeypatch.setattr(client_module, "_to_google_credentials", fake_to_oauth)

        # googleapiclient.discovery.build をモック
        import googleapiclient.discovery

        monkeypatch.setattr(googleapiclient.discovery, "build", fake_build)

        client = GoogleGmailClient(
            service_account_credentials=_fake_sa_credentials(),
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )

        assert len(captured_sa) == 1
        assert captured_sa[0][0]["subject"] == "user@example.com"
        assert client._service_account_credentials is not None

    @pytest.mark.unit
    def test_build_service_uses_oauth_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OAuth credentials 指定時、_to_google_credentials が呼ばれる。"""
        from infrastructure.google_gmail import client as client_module

        captured_oauth: list = []

        def fake_to_sa(creds: Any, scopes: Any) -> MagicMock:
            raise AssertionError("SA path must not be taken")

        def fake_to_oauth(creds: Any) -> MagicMock:
            captured_oauth.append(creds)
            return MagicMock(name="OAuth-Creds")

        def fake_build(*args: Any, **kwargs: Any) -> MagicMock:
            return MagicMock(name="Service")

        monkeypatch.setattr(
            client_module, "_to_google_service_account_credentials", fake_to_sa
        )
        monkeypatch.setattr(client_module, "_to_google_credentials", fake_to_oauth)

        import googleapiclient.discovery

        monkeypatch.setattr(googleapiclient.discovery, "build", fake_build)

        GoogleGmailClient(credentials=_fake_credentials())

        assert len(captured_oauth) == 1
