import hashlib
import hmac
import time
from collections import OrderedDict
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import hummingbot.connector.exchange.bing_x.bing_x_constants as CONSTANTS
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class BingXAuth(AuthBase):

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    @staticmethod
    def keysort(dictionary: Dict[str, str]) -> Dict[str, str]:
        return OrderedDict(sorted(dictionary.items(), key=lambda t: t[0]))

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        request.params = self.add_auth_to_params(params=request.params)
        headers = self.header_for_authentication()
        if request.headers is not None:
            headers.update(request.headers)
        request.headers = headers
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        This method is intended to configure a websocket request to be authenticated. BingX does not use this
        functionality
        """
        return request  # pass-through

    def get_referral_code_headers(self):
        """
        Generates authentication headers required by BingX
        :return: a dictionary of auth headers
        """
        headers = {
            "referer": CONSTANTS.HBOT_BROKER_ID
        }
        return headers

    def add_auth_to_params(self,
                           params: Optional[Dict[str, Any]]):
        timestamp = str(int(time.time() * 1000))
        request_params = params or {}
        request_params["timestamp"] = timestamp
        # request_params["api_key"] = self.api_key
        request_params = self.keysort(request_params)
        signature = self._generate_signature(params=request_params)
        request_params["signature"] = signature
        return request_params

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        encoded_params_str = urlencode(params)
        digest = hmac.new(self.secret_key.encode("utf8"), encoded_params_str.encode("utf8"), hashlib.sha256).hexdigest()
        return digest

    def generate_ws_authentication_message(self):
        """
        Generates the authentication message to start receiving messages from
        the 3 private ws channels
        """
        expires = int((self.time_provider.time() + 10) * 1e3)
        _val = f'GET/realtime{expires}'
        signature = hmac.new(self.secret_key.encode("utf8"),
                             _val.encode("utf8"), hashlib.sha256).hexdigest()
        auth_message = {
            "op": "auth",
            "args": [self.api_key, expires, signature]
        }
        return auth_message

    def _time(self):
        return time.time()

    def header_for_authentication(self) -> Dict[str, str]:
        return {
            "X-BX-APIKEY": self.api_key,
            "X-SOURCE-KEY": CONSTANTS.SOURCE_KEY
        }
