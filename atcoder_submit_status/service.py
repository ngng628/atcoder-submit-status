from abc import ABCMeta, abstractmethod
import pathlib
from typing import *
import requests
from bs4 import BeautifulSoup
import atcoder_submit_status.__about__ as version
import atcoder_submit_status.utils as utils
from logging import getLogger
logger = getLogger(__name__)


class Service:
   @abstractmethod
   def get_login_page_url(self) -> str:
      pass

   @abstractmethod
   def login(self):
      pass

   @abstractmethod
   def logout(self):
      pass
   
   @abstractmethod
   def is_logged_in(self) -> bool:
      pass

   @abstractmethod
   def get_url(self) -> str:
      pass

   @abstractmethod
   def get_name(self) -> str:
      pass

class AtCoderService(Service):
   def get_login_page_url(self) -> str:
      return 'https://atcoder.jp/login'

   def login(self, username: str, password: str, session: Optional[requests.Session] = None):
      session = session or utils.get_default_session()
      if self.is_logged_in(session=session):
         return
      url = self.get_login_page_url()
      response = session.get(url)
      soup = BeautifulSoup(response.text, 'lxml')
      csrf_token = soup.find(attrs={'name': 'csrf_token'}).get('value')
      login_info = { 'csrf_token': csrf_token, 'username': username, 'password': password }
      response = session.post(url, data=login_info)
      response.raise_for_status()

   def logout(self):
      pass
      # os.remove()

   def is_logged_in(self, session: Optional[requests.Session] = None) -> bool:
      session = session or utils.get_default_session()
      url = 'https://atcoder.jp/contests/dummydummydummy/submit'
      response = session.get(url)
      if response.status_code == 404:
         return True
      else:
         return False

   def get_url(self):
      return 'https://atcoder.jp'
   
   def get_name(self):
      return 'AtCoder'
