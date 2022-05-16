from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from copy import deepcopy
import re
import pathlib
from sys import prefix
from typing import *
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import atcoder_submit_status.__about__ as version
import atcoder_submit_status.utils as utils
from logging import getLogger
logger = getLogger(__name__)


class Service:
   @abstractmethod
   def get_login_page_url(self) -> str:
      pass

   @abstractmethod
   def login(self, username, password, session):
      pass

   @abstractmethod
   def logout(self):
      pass
   
   @abstractmethod
   def is_logged_in(self) -> bool:
      pass

   @abstractmethod
   def fetch_submissions(self, url, users, session):
      pass

   @abstractmethod
   def minimize_submissions_info(self, submissions):
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
   
   def fetch_submissions(self, url, users = [], session: Optional[requests.Session] = None):
      session = session or utils.get_default_session()

      contest_round = self.get_round(url)
      submissions_url = self.get_url() + '/contests/' + contest_round + '/submissions/me' 

      # TODO
      if len(users) > 0:
         pass

      response = session.get(submissions_url)
      response.raise_for_status()
      soup = BeautifulSoup(response.text, 'lxml')
      
      rows = soup.findAll('table', {'class': 'table' })[0].findAll('tr')

      submissions = []
      keys = ['submission_time', 'task', 'user', 'language', 'score', 'code_size', 'status', 'exec_time', 'memory']
      max_lengths = { key: 0 for key in keys }
      for i in range(len(rows)):
         if i == 0:
            continue
         r = rows[i].findAll('td')
         submission = { keys[i]: r[i].get_text() for i in range(len(keys)) }
         submission['submission_time'] = submission['submission_time'][:16]
         submission['user'] = submission['user'].rstrip(' ')  # 謎の空白
         submissions.append(submission)
         for key in keys:
            max_lengths[key] = max(max_lengths[key], len(submission[key]))

      for submission in submissions:
         for key in keys:
            if key in ['score', 'code_size', 'exec_time', 'memory']:
               submission[key] = submission[key].rjust(max_lengths[key])
            else:
               submission[key] = submission[key].ljust(max_lengths[key])
            
            if key == 'status':
               if submission[key] == 'AC':
                  submission[key] = utils.backRGB(92, 184, 92) + Fore.WHITE + ' ' + submission[key] + ' ' + Style.RESET_ALL
               else:
                  submission[key] = utils.backRGB(240, 173, 78) + Fore.WHITE + ' ' + submission[key] + ' ' + Style.RESET_ALL

      return submissions

   def minimize_submissions_info(self, submissions):
      res = deepcopy(submissions)
      for i in range(len(res)):
         if 'submission_time' in res[i]:
            res[i].pop('submission_time')
         if 'task' in res[i]:
            tmp = res[i]['task']
            tmp = tmp[:tmp.find(' ')]
            res[i]['task'] = tmp
         if 'language' in res[i]:
            res[i].pop('language')
         if 'code_size' in res[i]:
            res[i].pop('code_size')
         if 'exec_time' in res[i]:
            res[i].pop('exec_time')
         if 'memory' in res[i]:
            res[i].pop('memory')

      keys = ['task', 'user', 'score', 'status']
      max_lengths = { key: 0 for key in keys }
      for i in range(len(res)):
         for key in keys:
            max_lengths[key] = max(max_lengths[key], len(res[i][key]))
      for i in range(len(res)):
         for key in keys:
            if key in ['score']:
               res[i][key] = res[i][key].rjust(max_lengths[key])
            else:
               res[i][key] = res[i][key].ljust(max_lengths[key])

      return res

   def get_url(self):
      return 'https://atcoder.jp'
   
   def get_name(self):
      return 'AtCoder'

   # TODO: きれいに書く
   def get_round(self, url: str) -> str:
      prefix_len = len('https://atcoder.jp/contests/')
      if url[-1] != '/':
         url = url + '/'
      res = url[prefix_len:url.find('/', prefix_len)]
      return res