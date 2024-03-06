from __future__ import annotations

import json
import random
from typing import Callable
import time
import requests


class ProxyService:
    def __init__(self, api_key: str, proxy_key: str, proxy_id: int):
        self.__api_key = api_key
        self.__proxy_key = proxy_key
        self.__proxy_id = proxy_id
        self.__proxy_api = MobileproxyApi(api_key)
        self.__proxy_speedtest_api = ProxySaleApi()

    def prepare_proxy(self, operator: str, city_id: int, min_proxy_speed: int = 10_000) -> bool:
        """
        Checks the speed of the internet connection and changes proxy if it's too slow
        :param min_proxy_speed: minimal speed of proxy to be used, in KB/S.
        :param operator: operator for change_geo
        :param city_id: city for change_geo
        """

        proxy_speedtest_info = self.__get_proxy_speedtest_info()
        speed = self.__proxy_speedtest_api.proxy_speedtest(proxy_speedtest_info)

        if speed is None or speed < min_proxy_speed:
            self.change_geo(operator, city_id)

        return self.change_proxy()

    def change_geo(self, operator: str, city_id: int):
        """ Changes proxy's geolocation """
        return self.__proxy_api.change_geo(
            self.__proxy_id,
            MobileproxyApi.COUNTRY_ID_RU,
            city_id,
            operator
        )

    def change_proxy(self) -> bool:
        """ Changes proxy and verifies that IP real changed """

        def _change_proxy():
            current_ip: str = self.__proxy_api.get_proxy_ip(self.__proxy_id)

            new_proxy_data = self.__proxy_api.change_proxy_ip(self.__proxy_key)
            if new_proxy_data.get('new_ip') is None:
                raise Exception(f'Invalid change proxy response: {new_proxy_data}')

            if current_ip == new_proxy_data['new_ip']:
                raise Exception(f"IP not changed")

            return True

        return bool(_call_safe(_change_proxy))

    def __get_proxy_speedtest_info(self) -> str:
        proxy_info = self.__proxy_api.get_proxy_info(self.__proxy_id)
        return (f"{proxy_info['proxy_independent_http_host_ip']}:{proxy_info['proxy_independent_port']}"
                f":{proxy_info['proxy_login']}:{proxy_info['proxy_pass']}")


class MobileproxyApi:
    __BASE_URL = 'https://mobileproxy.space'
    __DEFAULT_USER_AGENT = ('Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10'
                            '(KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.102011-10-16 20:23:10')

    COUNTRY_ID_RU = 1

    def __init__(self, api_key: str):
        self.__api_key = api_key

    def get_proxy_ip(self, proxy_id: int) -> str:
        """ Get current proxy's IP-address """

        url = f'/api.html?command=proxy_ip&proxy_id={proxy_id}'

        def get_ip():
            return self.__get(url)['ip']

        return _call_safe(get_ip)

    def get_proxy_info(self, proxy_id: int) -> dict:
        url = f'/api.html?command=get_my_proxy&proxy_id={proxy_id}'

        def get_info():
            return self.__get(url)[0]

        return _call_safe(get_info)

    def change_proxy_ip(self, proxy_key: str, user_agent: str = __DEFAULT_USER_AGENT) -> dict:
        """ Changes current proxy. Returns new proxy data """

        url = f'/reload.html?proxy_key={proxy_key}&format=json'
        headers = {'User-Agent': user_agent}

        def change_proxy():
            return self.__get(url, headers=headers)

        return _call_safe(change_proxy)

    def get_cities(self, lang: str = 'ru') -> list:
        url = f"/api.html?command=get_id_country&lang={lang}"

        def _get_cities():
            response = self.__get(url)
            if response.get('id_country') is None:
                raise ProxyApiException(f"Illegal get countries response: {response}")
            return response['id_country']

        return list(_call_safe(_get_cities).values())

    def get_geo(self, proxy_id: int) -> list:
        url = f"/api.html?command=get_geo_list&proxy_id={proxy_id}"

        def _get_geo():
            return self.__get(url)

        return _call_safe(_get_geo)

    def change_geo(self, proxy_id: int, country_id: int, city_id: int, operator: str) -> bool:
        url = f'/api.html?command=change_equipment&proxy_id={proxy_id}&id_country={country_id}&id_city={city_id}&operator={operator}'

        def _change_geo():
            response = self.__get(url)
            return response.get('error') is None and response.get('status') == 'ok'
        return _call_safe(_change_geo)

    def get_geo_operator_proxy(self) -> dict:
        url = '/api.html?command=get_geo_operator_list'

        def _get_geo_operator_proxy():
            return self.__get(url)
        return _call_safe(_get_geo_operator_proxy)

    def __get(self, url: str, params: dict = dict(), headers: dict = dict()):
        headers['Authorization'] = f'Bearer {self.__api_key}'

        response = requests.get(f"{self.__BASE_URL}{url}", params, headers=headers)
        response_data = response.json()
        if type(response_data) is dict and response_data.get('status', 'err') == 'err':
            raise ProxyApiException(f"Request failed. Url: {url}, response: {response.content}")
        return response_data


class ProxySaleApi:
    __BASE_URL = 'https://free.proxy-sale.com/api/client'

    def proxy_speedtest(self, proxy_info: str, proxy_type: str = "HTTP", timeout: int = 5) -> int | None:
        """
        :param proxy_info: proxy info in format: "IP:PORT:USERNAME:PASSWORD"
        :param proxy_type: type of proxy: HTTP/HTTPS/SOCKS
        :param timeout: timeout of speedtest
        :return: speed in kb/s (kilobytes per second)
        """

        url = f'{self.__BASE_URL}/speedtest'
        data = {
            "access": "true",
            "proxyIp": proxy_info,
            "proxyType": proxy_type,
            "timeout": str(timeout),
            "url": "https://www.google.ru"
        }

        def get_average_speed():
            response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            response_data = response.json()
            if response_data.get('averageSpeed') is None:
                raise ProxyApiException(f"Invalid Proxy speedtest response: {response}")
            return response_data['averageSpeed']

        return _call_safe(get_average_speed, timeout=5)


class ProxyApiException(Exception):
    def __init__(self, message):
        super().__init__(message)


def _call_safe(callback: Callable, attempts: int = 3, timeout: int = 2):
    """ Executes func with many attempts """
    for _ in range(attempts):
        try:
            return callback()
        except Exception as e:
            print(str(e))
            time.sleep(timeout)
    raise Exception("Execution failed")