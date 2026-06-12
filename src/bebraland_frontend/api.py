from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests


class ApiClient:
    def __init__(self, server_url: str, token: str | None = None) -> None:
        self.server_url = server_url.rstrip("/")
        self.token = token

    def api_url(self, path: str) -> str:
        return f"{self.server_url}/api/v1/{path.lstrip('/')}"

    def headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def get_profiles(self) -> list[dict[str, Any]]:
        response = requests.get(self.api_url("profiles"), headers=self.headers(), timeout=15)
        response.raise_for_status()
        return response.json()["profiles"]

    def latest_manifest(self, slug: str) -> dict[str, Any]:
        response = requests.get(self.api_url(f"profiles/{slug}/latest"), headers=self.headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def azuriom_login(self, email: str, password: str, code: str | None = None) -> dict[str, Any]:
        body = {"email": email, "password": password}
        if code:
            body["code"] = code
        response = requests.post(self.api_url("auth/azuriom/login"), json=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("access_token"):
            self.token = payload["access_token"]
        return payload

    def azuriom_verify(self, access_token: str) -> dict[str, Any]:
        response = requests.post(
            self.api_url("auth/azuriom/verify"),
            json={"access_token": access_token},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def check_update(self, current_version: str, platform: str = "windows") -> dict[str, Any]:
        response = requests.get(
            self.api_url("launcher/update"),
            params={"current_version": current_version, "platform": platform},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()


def absolute_url(server_url: str, value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return urljoin(f"{server_url.rstrip('/')}/", value.lstrip("/"))
