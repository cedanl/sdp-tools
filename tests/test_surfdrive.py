"""Tests for surfdrive.surfdrive_download without network access."""

from types import SimpleNamespace

import pandas as pd
import pytest
from requests.auth import HTTPBasicAuth

import surfdrive.surfdrive_download as sd


def _mock_get(monkeypatch, status_code=200, text="a,b\n1,2\n"):
    calls = []

    def fake_get(url, auth=None, **kwargs):
        calls.append({"url": url, "auth": auth})
        return SimpleNamespace(status_code=status_code, text=text)

    monkeypatch.setattr(sd.requests, "get", fake_get)
    return calls


def test_credentials_read_at_call_time(monkeypatch, tmp_path):
    """Env vars set after import are used for authentication."""
    monkeypatch.setenv("SURFDRIVE_SHARE_TOKEN", "late-token")
    monkeypatch.setenv("SURFDRIVE_PASSWORD", "late-password")
    calls = _mock_get(monkeypatch)

    sd.download_surfdrive_csv(tmp_path / "out.csv")

    assert len(calls) == 1
    auth = calls[0]["auth"]
    assert isinstance(auth, HTTPBasicAuth)
    assert auth.username == "late-token"
    assert auth.password == "late-password"


def test_no_module_level_credentials():
    """The module no longer caches credentials at import time."""
    assert not hasattr(sd, "share_token")
    assert not hasattr(sd, "password")


def test_success_returns_dataframe_and_writes_csv(monkeypatch, tmp_path):
    """A 200 response returns a DataFrame and writes a ';'-separated CSV."""
    monkeypatch.setenv("SURFDRIVE_SHARE_TOKEN", "t")
    monkeypatch.setenv("SURFDRIVE_PASSWORD", "p")
    _mock_get(monkeypatch)
    out = tmp_path / "out.csv"

    df = sd.download_surfdrive_csv(out)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["a", "b"]
    assert df.shape == (1, 2)
    assert out.read_text().splitlines() == ["a;b", "1;2"]


def test_non_200_raises(monkeypatch, tmp_path):
    """A non-200 response raises and writes no file."""
    monkeypatch.setenv("SURFDRIVE_SHARE_TOKEN", "t")
    monkeypatch.setenv("SURFDRIVE_PASSWORD", "p")
    _mock_get(monkeypatch, status_code=401, text="Unauthorized")
    out = tmp_path / "out.csv"

    with pytest.raises(Exception, match="Can not download"):
        sd.download_surfdrive_csv(out)
    assert not out.exists()
