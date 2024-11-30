import json
import logging

import dns.resolver
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from urllib3.util import connection

gsb_resolver = dns.resolver.Resolver()
gsb_resolver.nameservers = ["10.0.255.130", "10.0.255.131", "10.0.255.2", "10.0.255.3"]


_orig_create_connection = connection.create_connection


def patched_create_connection(address, *args, **kwargs):
    """Wrap urllib3's create_connection to resolve the name elsewhere"""
    # resolve hostname to an ip address; use your own
    # resolver here, as otherwise the system resolver will be used.
    host, port = address
    hostname = gsb_resolver.resolve(host, "A", lifetime=5)[0]

    return _orig_create_connection((hostname, port), *args, **kwargs)


# connection.create_connection = patched_create_connection # noqa: ERA001

logger = logging.getLogger(__name__)


class ShahkarError(Exception):
    pass


class ShahkarVerificationError(ShahkarError):
    pass


HTTP_200_OK = 200
HTTP_500_SERVER_ERROR = 500


class ShahkarResponse:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    @property
    def json(self):
        return {
            "data": self.data,
            "status_code": self.status_code,
        }

    @property
    def text(self):
        return json.dumps(self.json)


class Shahkar:
    def __init__(  # noqa: PLR0913
        self,
        mock=False,  # noqa: FBT002
        pid=None,
        auth_code=None,
        client_id=None,
        client_secret=None,
        **kwargs,
    ):
        self.mock = mock
        if not self.mock:
            assert pid, "`pid` is required"
            if not auth_code:
                assert client_id and client_secret, (
                    "Either auth_code or client_id and "
                    "client_secret must be provided"
                )
            self.base_url = kwargs["base_url"]
            self.username = kwargs["username"]
            self.password = kwargs["password"]
            self.pid = pid
            self.provider_code = kwargs["provider_code"]
            self.client_id = client_id
            self.client_secret = client_secret
            self.auth_code = auth_code
            if not self.auth_code:
                # TODO: generate auth_code from client_id and client_secret
                pass

    def request_for_token(self, method, url, headers=None, **kwargs):
        headers = headers or {}
        headers["Authorization"] = f"Basic {self.auth_code}"
        headers["Content-type"] = "application/x-www-form-urlencoded"
        return requests.request(method, url, headers=headers, timeout=5, **kwargs)

    def request_for_service(self, method, url, headers=None, **kwargs):
        headers = headers or {}
        headers["pid"] = self.pid
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["basicAuthorization"] = f"Basic {self.auth_code}"
        headers["Content-type"] = "application/json"
        return requests.request(method, url, headers=headers, timeout=5, **kwargs)

    def refresh_token(self, refresh_token):
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        response = self.request_for_token("POST", url, data=data)
        return response.json()

    def get_token(self):
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }
        response = self.request_for_token("POST", url, data=data)
        return response.json()

    @property
    def access_token(self):
        access_token = cache.get("shahkar_access_token")
        if access_token:
            return access_token

        refresh_token = cache.get("shahkar_refresh_token")
        if refresh_token:
            data = self.refresh_token(refresh_token)
            access_token = data["access_token"]
            cache.set("shahkar_access_token", access_token, data["expires_in"])
            return access_token

        data = self.get_token()
        access_token = data["access_token"]
        cache.set("shahkar_access_token", access_token, data["expires_in"])
        refresh_token = data["refresh_token"]
        cache.set("shahkar_refresh_token", refresh_token, data["expires_in"])
        return access_token

    def generate_request_id(self):
        return f"{self.provider_code}{timezone.localtime(
            timezone.now()).strftime('%Y%m%d%H%M%S%f')}"

    def _verify(self, national_code, mobile):
        url = f"{self.base_url}/api/client/apim/v1/shahkar/gwsh/serviceIDmatching"
        try:
            payload = {
                "requestId": self.generate_request_id(),
                "serviceNumber": mobile,
                "serviceType": 2,
                "identificationType": 0,
                "identificationNo": national_code,
            }
            response = self.request_for_service("POST", url, data=payload)
            data = response.json()
            status_code = response.status_code
        except requests.RequestException as e:
            data = {"detail": str(e)}
            status_code = HTTP_500_SERVER_ERROR

        verified = status_code == HTTP_200_OK

        return verified, data, status_code

    def verify(self, national_code, mobile):
        if self.mock:
            return True, ShahkarResponse(
                data={"detail": "Mobile and National Code Are OK."},
                status_code=200,
            )

        verified, data, status_code = self._verify(national_code, mobile)

        return verified, ShahkarResponse(data=data, status_code=status_code)


shahkar = Shahkar(**settings.SHAHKAR_SETTINGS)
