import zipfile

from incogniton import IncognitonWebdriverWrapper, IncognitonApi, IncognitonWebdriverOptions
from proxy import MobileproxyApi, ProxyService, ProxySaleApi


PROFILE_ID = '12377ce4-c110-4cb3-be5f-f20e4d59484d'
ADBLOCK_PATH = 'C:\\Users\\ant\AppData\Local\Google\Chrome\\User Data\Default\Extensions\gighmmpiobklfepjocnamgkkbiglidom\\5.19.0_0\ext.crx'
""" See: https://www.crx4chrome.com/crx/31927/ """
PROXY_AUTH_EXT_PATH = 'proxy_auth_plugin.zip'

PROXY_ID = 231297
PROXY_API_KEY = '521ff8a72ce348ea31a8b172546cc8d2'
PROXY_KEY = 'f6e5b670837a85bc9644719b07e686ff'
RYAZAN_CITY_ID = 1736
MEGAFON_OPERATOR = 'megafone'


def make_proxy_config(proxy_host: str, proxy_port: int, proxy_user: str, proxy_password: str) -> None:
    """ Creates proxy auth config file - for auto auth in proxy. Run once and then just use generated file """

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_host, proxy_port, proxy_user, proxy_password)

    with zipfile.ZipFile(PROXY_AUTH_EXT_PATH, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)


def test_selenium_wrapper():
    api = IncognitonApi()
    cookies = api.get_cookie(PROFILE_ID)
    for cookie in cookies:
        print(cookie)

    options = IncognitonWebdriverOptions()
    """
        With options you can specify target proxy, proxy path, adblock ext path (path to crx chrome extension path)
        see: https://www.crx4chrome.com/crx/31927/
    """

    options.adblock_extension_path = ADBLOCK_PATH
    options.proxy_config_ext_path = PROXY_AUTH_EXT_PATH
    options.proxy = {
        "connection_type": "HTTP proxy",
        "proxy_url": "wproxy.site:13878",
        "proxy_username": "YdsYN6",
        "proxy_password": "Et7uscuPyg2M"
    }

    wrapper = IncognitonWebdriverWrapper(PROFILE_ID, options)
    """
        Wrapper does all profile set up in __init__ method: loads cookies, set up proxy, adds chrome extensions
        Then when you finish your work method __die__ sends new cookies back to incogniton (but api method now dont work)
        You can use wrapper.driver to get access to selenium webdriver directly
    """

    wrapper.get('https://www.avito.ru/')


def test_proxy_api():
    service = ProxyService(PROXY_API_KEY, PROXY_KEY, PROXY_ID)
    print(service.prepare_proxy(MEGAFON_OPERATOR, RYAZAN_CITY_ID))


def test_service():
    from services import IncognitonWebdriverService, ProxyOptions, IncognitonWebdriverOptions

    webdriver_options = IncognitonWebdriverOptions()
    webdriver_options.adblock_extension_path = ADBLOCK_PATH
    webdriver_options.proxy_config_ext_path = PROXY_AUTH_EXT_PATH
    webdriver_options.proxy = {
        "connection_type": "HTTP proxy",
        "proxy_url": "wproxy.site:13878",
        "proxy_username": "YdsYN6",
        "proxy_password": "Et7uscuPyg2M"
    }
    proxy_options = ProxyOptions(PROXY_API_KEY, PROXY_KEY, PROXY_ID, MEGAFON_OPERATOR, RYAZAN_CITY_ID)
    service = IncognitonWebdriverService(PROFILE_ID, webdriver_options, proxy_options)
    webdriver_wrapper = service.start_session()  # Do any selenium staff via webdriver_wrapper
    webdriver_wrapper.get('https://avito.ru')
    service.end_session(webdriver_wrapper)


def main():
    test_service()
    # make_proxy_config("wproxy.site", 13878, "YdsYN6", "Et7uscuPyg2M")


if __name__ == '__main__':
    main()
