from __future__ import annotations

import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from proxy import _call_safe


class IncognitonWebdriverOptions:
    proxy: dict = dict()
    """ Format: {'connection_type': '','proxy_url': '','proxy_username': '','proxy_password': ''} """

    proxy_config_ext_path: str|None = None
    """ Path to proxy auth extension """

    adblock_extension_path: str|None = None
    """ Path to adblock extension folder """


class IncognitonWebdriverWrapper:
    __api: IncognitonApi
    __driver: webdriver.Chrome
    __profile_id: str
    __cookies: list[dict] = []

    def __init__(self, profile_id: str, options: IncognitonWebdriverOptions, attempts: int = 3) -> None:
        self.__api = IncognitonApi()
        self.__profile_id = profile_id
        self.__driver = self.__make_driver(options)
        self.__set_cookies()

    def end_session(self, attempts: int = 3):
        def callback():
            cookies = self.__driver.get_cookies()
            for idx, cookie in enumerate(cookies):
                if cookie.get('expiry'):
                    cookie['expirationDate'] = cookie['expiry']
                    cookie.pop('expiry')
                cookies[idx] = cookie
            self.__api.add_cookie(self.__profile_id, cookies)
        _call_safe(callback, attempts)

    @property
    def driver(self):
        return self.__driver

    def get(self, url: str, attempts: int = 3) -> None:
        """ Go to page in browser & set all cookies for its domain """
        def callback():
            self.__driver.get(url)
            self.__driver.delete_all_cookies()
            self.update_cookies(url, attempts=1)
            self.__driver.refresh()
        _call_safe(callback, attempts)

    def update_cookies(self, url: str, attempts: int = 3) -> None:
        """ Sets webdriver cookies for url's domain """
        def callback():
            domain = self.__get_domain(url)
            for cookie in self.__cookies:
                if domain in cookie.get('domain'):
                    self.__driver.add_cookie(cookie)
        _call_safe(callback, attempts)

    def __set_cookies(self) -> None:
        cookie_data = self.__api.get_cookie(self.__profile_id)
        for cookie_item in cookie_data:
            if cookie_item['sameSite'] not in ['Strict', 'Lax', 'None']:
                cookie_item['sameSite'] = 'None'
            self.__cookies.append(cookie_item)

    def __make_driver(self, options: IncognitonWebdriverOptions) -> webdriver.Chrome:
        chrome_options = self.__make_driver_options(options)
        return webdriver.Chrome(options=chrome_options)

    def __make_driver_options(self, options: IncognitonWebdriverOptions) -> Options:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--profile-directory=selenium")
        chrome_options.page_load_strategy = 'eager'

        if options.proxy_config_ext_path is not None:
            chrome_options.add_extension(options.proxy_config_ext_path)
        if options.proxy.get('proxy_url'):
            chrome_options.add_argument(f'--proxy-server={options.proxy["proxy_url"]}')
        # if options.adblock_extension_path is not None:
        #     chrome_options.add_extension(options.adblock_extension_path)

        profile_data = self.__api.get_profile(self.__profile_id)
        user_agent = profile_data['Navigator'].get('user_agent')
        if user_agent is not None:
            chrome_options.add_argument(f'--user-agent={user_agent}')

        return chrome_options

    def __get_domain(self, url: str) -> str:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain if '.' not in domain else domain.split('.')[-2]


class IncognitonApi:
    __BASE_URL = 'http://localhost:35000'

    PROFILE_STATUS_READY = 'Ready'
    PROFILE_GROUP_IN_WORK = 'В работе'

    def all_profiles(self) -> dict:
        def _all():
            return self.__get(f"/profile/all")
        return _call_safe(_all)

    def get_profile(self, profile_id: str) -> dict:
        def _get_profile():
            response = self.__get(f"/profile/get/{profile_id}")
            return self.__get_data_or_fail(response, 'profileData')
        return _call_safe(_get_profile)

    def is_profile_ready(self, profile_id: str) -> bool:
        return self.get_profile_status(profile_id) == self.PROFILE_STATUS_READY

    def get_profile_status(self, profile_id: str) -> str:
        def _get_profile_status():
            response = self.__get(f"/profile/status/{profile_id}")
            return self.__get_data_or_fail(response, 'status')
        return _call_safe(_get_profile_status)

    def get_cookie(self, profile_id: str) -> dict:
        def _get_cookie():
            response = self.__get(f"/profile/cookie/{profile_id}")
            return self.__get_data_or_fail(response, 'CookieData ')
        return _call_safe(_get_cookie)

    def add_cookie(self, profile_id: str, cookies: list) -> dict:
        def _add_cookie():
            return self.__post('/profile/addCookie', {
                'data': json.dumps({
                    'profile_browser_id': profile_id,
                    'format': 'json',
                    'cookie': json.dumps(cookies)
                })
            })
        return _call_safe(_add_cookie)

    def update_profile(self, profile_id: str, profile_info: dict = dict(), proxy_info: dict = dict()) -> dict:
        def _update_profile():
            request = {
                "profileData": json.dumps({
                    "profile_browser_id": profile_id,
                    "Proxy": proxy_info,
                    "general_profile_information": profile_info
                })
            }
            return self.__post("/profile/update", request)
        return _call_safe(_update_profile)

    def __get_data_or_fail(self, response: dict, key: str):
        self.__validate_response(response, key)
        return response.get(key)

    def __validate_response(self, response: dict, key: str) -> None:
        if response.get(key) is None:
            raise IncognitonApiException(f'API error: {json.dumps(response)}')

    def __get(self, url: str) -> dict:
        response = requests.get(f"{self.__BASE_URL}{url}")
        return response.json()

    def __post(self, url: str, data: dict = dict()) -> dict:
        response = requests.post(f"{self.__BASE_URL}{url}", data)
        return response.json()


class IncognitonApiException(Exception):
    def __init__(self, message):
        super().__init__(message)
