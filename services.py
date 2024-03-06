from incogniton import *
from proxy import *


class ProxyOptions:
    api_key: str
    proxy_key: str
    proxy_id: int
    operator: str = ''
    city_id: int = 0

    def __init__(self, api_key: str, proxy_key: str, proxy_id: int, operator: str, city_id: int) -> None:
        """
        :param api_key:
        :param proxy_key:
        :param proxy_id:
        :param operator: operator to be set if proxy speed is too low
        :param city_id: city to be set if proxy speed is too low
        """

        self.api_key = api_key
        self.proxy_key = proxy_key
        self.proxy_id = proxy_id
        self.operator = operator
        self.city_id = city_id


class IncognitonWebdriverService:
    __profile_id: str
    __webdriver_options: IncognitonWebdriverOptions
    __proxy_options: ProxyOptions

    def __init__(self, profile_id: str, webdriver_options: IncognitonWebdriverOptions, proxy_options: ProxyOptions) -> None:
        self.__profile_id = profile_id
        self.__webdriver_options = webdriver_options
        self.__proxy_options = proxy_options

    def start_session(self) -> IncognitonWebdriverWrapper:
        self.__check_profile_status()

        return IncognitonWebdriverWrapper(self.__profile_id, self.__webdriver_options)

    def end_session(self, webdriver_wrapper: IncognitonWebdriverWrapper) -> None:
        pass

    def __check_profile_status(self) -> None:
        pass
