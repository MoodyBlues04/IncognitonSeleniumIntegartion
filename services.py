from incogniton import *
from proxy import *


class ProxyOptions:
    api_key: str
    proxy_key: str
    proxy_id: int
    operators: list[str]
    city_id: int

    def __init__(
            self, api_key: str,
            proxy_key: str,
            proxy_id: int,
            operators: list[str],
            city_id: int = MobileproxyApi.CITY_ID_MOSCOW) -> None:
        """
        :param api_key:
        :param proxy_key:
        :param proxy_id:
        :param operators: operators to be set if proxy speed is too low
        :param city_id: city to be set if proxy speed is too low
        """

        self.api_key = api_key
        self.proxy_key = proxy_key
        self.proxy_id = proxy_id
        self.operators = operators
        self.city_id = city_id


class IncognitonWebdriverService:
    __profile_id: str
    __webdriver_options: IncognitonWebdriverOptions
    __proxy_options: ProxyOptions
    __proxy_service: ProxyService
    __incogniton_api: IncognitonApi

    __profile_data_backup: dict = dict()

    def __init__(self, profile_id: str, webdriver_options: IncognitonWebdriverOptions, proxy_options: ProxyOptions) -> None:
        self.__profile_id = profile_id
        self.__webdriver_options = webdriver_options
        self.__proxy_options = proxy_options

        self.__proxy_service = ProxyService(
            proxy_options.api_key,
            proxy_options.proxy_key,
            proxy_options.proxy_id
        )
        self.__incogniton_api = IncognitonApi()

    def start_session(self) -> IncognitonWebdriverWrapper:
        self.__check_profile_status()
        print('Profile status: ready')
        self.__prepare_proxy()
        print('Proxy prepared')

        self.__backup_profile_data()
        print('Profile data saved')

        wrapper = IncognitonWebdriverWrapper(self.__profile_id, self.__webdriver_options)
        print('Webdriver configured')

        self.__set_profile_in_work_status()
        print('Status "in work" set for profile')

        return wrapper

    def end_session(self, webdriver_wrapper: IncognitonWebdriverWrapper) -> None:
        if self.__profile_data_backup.get('general_profile_information') is None:
            raise Exception("Session was incorrectly started. No profile data backup")

        self.__incogniton_api.update_profile(
            self.__profile_id,
            self.__profile_data_backup['general_profile_information'],
            self.__profile_data_backup['Proxy']
        )
        print('Profile data set back')

    def __check_profile_status(self) -> None:
        if not self.__is_profile_ready_to_work():
            raise Exception("Profile already in use")

    def __is_profile_ready_to_work(self) -> bool:
        profile_info = self.__incogniton_api.get_profile(self.__profile_id)
        profile_group = profile_info['general_profile_information']['profile_group']

        return (self.__incogniton_api.is_profile_ready(self.__profile_id) and
                IncognitonApi.PROFILE_GROUP_IN_WORK not in profile_group)

    def __prepare_proxy(self) -> None:
        is_prepared = self.__proxy_service.prepare_proxy(
            self.__webdriver_options.proxy['proxy_username'],
            self.__webdriver_options.proxy['proxy_password'],
            self.__proxy_options.operators,
            self.__proxy_options.city_id
        )
        if not is_prepared:
            raise Exception("Cannot prepare proxy for session")

    def __backup_profile_data(self) -> None:
        self.__profile_data_backup = self.__incogniton_api.get_profile(self.__profile_id)

    def __set_profile_in_work_status(self) -> None:
        profile_info = {
            "profile_group": IncognitonApi.PROFILE_GROUP_IN_WORK
        }
        proxy_info = {
            "connection_type": 'Without proxy',
            "proxy_url": '',
            "proxy_rotation_api_url": '',
            "proxy_rotating": 0,
            "proxy_provider": "main",
            "proxy_username": '',
            "proxy_password": ''
        }
        self.__incogniton_api.update_profile(self.__profile_id, profile_info, proxy_info)
