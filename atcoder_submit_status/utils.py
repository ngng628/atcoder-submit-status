import pathlib
import contextlib
import sys
import appdirs
import requests
import datetime
from logging import getLogger
from typing import *
import http
import atcoder_submit_status.__about__ as version
import atcoder_submit_status.service as service
import atcoder_submit_status.utils as utils
from colorama import Fore, Back, Style

logger = getLogger(__name__)

USER_DATA_PATH = pathlib.Path(appdirs.user_data_dir('atcoder-submit-status'))
DEFAULT_COOKIE_PATH = USER_DATA_PATH / 'cookie.jar'
def get_cookie_path(service: service.Service):
   return USER_DATA_PATH / service.get_name() / 'cookie.jar'

CHECK = 'CHECK: '
ADD = 'ADD: '
NETWORK = 'NETWORK: '
DISPLAY = 'DISPLAY: '
FAILURE = 'FAILURE: '
HINT = 'HINT: '
INPUT = 'INPUT: '
SUCCESS = 'SUCCESS: '
INPUT_ICON = '[' + Fore.YELLOW + '>' + Style.RESET_ALL + '] '

def foreRGB(r: int, g: int, b: int) -> str:
   r = '{:03}'.format(r)
   g = '{:03}'.format(g)
   b = '{:03}'.format(b)
   return "\x1b[38;2;" + r + ";" + g + ";" + b + "m"

def backRGB(r: int, g: int, b: int) -> str:
   r = '{:03}'.format(r)
   g = '{:03}'.format(g)
   b = '{:03}'.format(b)
   return "\x1b[48;2;" + r + ";" + g + ";" + b + "m"

def convert_timestamp_with_time_zone_to_date(timestamp: str) -> str:
   date = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S%z')
   return date.strftime('%Y-%m-%d %H:%M:%S')

def convert_language_with_version_to_language(lang: str) -> str:
   return lang[:lang.find(' ')]

@contextlib.contextmanager
def new_session_with_our_user_agent(cookie_path: pathlib.Path, service: service.Service=None) -> Iterator[requests.Session]:
   if service is not None:
      cookie_path = get_cookie_path(service)
   session = requests.Session()
   session.headers['User-Agent'] = f'{version.__package_name__}/{version.__version__} (+{version.__url__})'
   logger.debug(f'User-Agent: {session.headers["User-Agent"]}')
   try:
      with utils.with_cookiejar(session, path=cookie_path) as session:
         yield session
   except Exception as e:
      logger.info(utils.HINT + f'You can delete the broken cookie.jar file: {str(cookie_path)}')
      raise

def service_from_url(url: str) -> service.Service:
   """コンテストURLからサービスを取得
   """
   if 'atcoder' in url:
      return service.AtCoderService()
   else:
      logger.info('service name could not be found.')
      return None

_DEFAULT_SESSION = None
def get_default_session() -> requests.Session:
    global _DEFAULT_SESSION
    if _DEFAULT_SESSION is None:
        _DEFAULT_SESSION = requests.session()
    return _DEFAULT_SESSION

@contextlib.contextmanager
def with_cookiejar(session: requests.Session, *, path: pathlib.Path=DEFAULT_COOKIE_PATH) -> Iterator[requests.Session]:
   """Cookieを利用したセッション
   """
   session.cookies = http.cookiejar.LWPCookieJar(str(path))  # type: ignore
   if path.exists():
      logger.info('load cookie from: %s', path)
      session.cookies.load(ignore_discard=True)  # type: ignore
   yield session
   logger.info('save cookie to: %s', path)
   path.parent.mkdir(parents=True, exist_ok=True)
   session.cookies.save(ignore_discard=True)  # type: ignore
   path.chmod(0o600)  # NOTE: to make secure a little bit
