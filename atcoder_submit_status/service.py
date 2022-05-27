from abc import ABCMeta, abstractmethod
from datetime import datetime
import sys
import time
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
   def fetch_submissions(self, url, no_color, users, session):
      pass

   @abstractmethod
   def minimize_submissions_info(self, submissions, mode):
      pass

   @abstractmethod
   def get_tasks(self, tasks_url, session: Optional[requests.Session] = None):
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

   def is_logged_in(self, session: Optional[requests.Session] = None) -> bool:
      session = session or utils.get_default_session()
      url = 'https://atcoder.jp/contests/dummydummydummy/submit'
      response = session.get(url)
      if response.status_code == 404:
         return True
      else:
         return False
   
   def fetch_submissions(self, url: str, no_color: bool = False, users: List[str] = [], session: Optional[requests.Session] = None):
      session = session or utils.get_default_session()

      contest_round = self.get_round(url)
      submissions_url = self.get_url() + '/contests/' + contest_round + '/submissions'
      if not users:
         name = self._get_user_name()
         if name:
            users.append(name)
         else:
            logger.info(utils.FAILURE_ICON + 'users not found.')
            sys.exit(0)

      # TODO
      if len(users) > 0:
         pass

      submissions = []
      keys = self._get_all_headers()
      max_lengths = { key: 0 for key in keys }
      for user in users:
         page = 1
         while True:  # page がなくなるまで
            payload = { 'f.User': user, 'page': page }
            response = session.get(submissions_url, params=payload)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            tables = soup.findAll('table', { 'class': 'table' }) 
            if not tables:
               break
            rows = tables[0].findAll('tr')

            for i in range(len(rows)):
               if i == 0:
                  continue

               # HTMLの内容をパース
               r = rows[i].findAll('td')
               submission = {}
               for i in range(len(keys)):
                  if i < len(r) - 1:  # "Detail" の分、1個引く
                     submission[keys[i]] = r[i].get_text().strip()
                  else:
                     submission[keys[i]] = ''

               # データを整形する
               submission['submission_time'] = utils.convert_timestamp_with_time_zone_to_date(submission['submission_time'])
               ## もし、WJ 5/12 や WA 5/12 の状態であれば、便宜上分けてパースしてしまったものをくっつける
               if submission['status'] not in self._get_statuses():
                  submission['status'] = submission['status'] + submission['exec_time']
               st = submission['status'][-3:].lstrip()
               ## `status` には色を付ける
               if not no_color:
                  color = self._get_status_color(st)
                  submission['status'] = Style.RESET_ALL + color + Fore.WHITE + ' ' + submission['status'] + ' ' + Style.RESET_ALL

               submissions.append(submission)
               for key in keys:
                  max_lengths[key] = max(max_lengths[key], len(submission[key]))
            time.sleep(0.5)
            page += 1

      submissions = sorted(submissions, key=lambda x: datetime.strptime(x['submission_time'], '%Y-%m-%d %H:%M:%S'), reverse=True)
      # 問題名の一覧を取得して十分な幅を確保する
      tasks_url = self.get_url() + '/contests/' + contest_round + '/tasks'
      task_names = self.get_task_names(tasks_url=tasks_url, session=session)
      for name in task_names:
         max_lengths['task'] = max(max_lengths['task'], len(name))

      for submission in submissions:
         for key in keys:
            if key in ['score', 'code_size', 'exec_time', 'memory']:
               submission[key] = submission[key].rjust(max_lengths[key])
            elif key in ['status']:
               submission[key] = submission[key].center(max_lengths[key])
            else:
               submission[key] = submission[key].ljust(max_lengths[key])
            
      submissions.reverse()
      return submissions

   def minimize_submissions_info(self, submissions, mode):
      res = deepcopy(submissions)
      for i in range(len(res)):
         if 'submission_time' in res[i]:
            if mode == 'MINIMAL':
               res[i].pop('submission_time')
         if 'task' in res[i]:
            tmp = res[i]['task']
            tmp = tmp[:tmp.find(' ')]
            res[i]['task'] = tmp
         if 'language' in res[i]:
            if mode == 'MINIMAL':
               res[i].pop('language')
            elif mode == 'NORMAL':
               res[i]['language'] = res[i]['language'][:res[i]['language'].find(' ')]
         if 'code_size' in res[i]:
            res[i].pop('code_size')
         if 'exec_time' in res[i]:
            res[i].pop('exec_time')
         if 'memory' in res[i]:
            res[i].pop('memory')

      keys = [key for key in res[0].keys()] if len(res) > 0 else []
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

   def get_task_names(self, tasks_url, session: Optional[requests.Session] = None) -> List[str]:
      session = session or utils.get_default_session()
      response = session.get(tasks_url)
      response.raise_for_status()
      soup = BeautifulSoup(response.text, 'lxml')
      rows = soup.findAll('table', {'class': 'table' })[0].findAll('tr')
      
      task_names = []
      for i in range(len(rows)):
         if i == 0:
            continue
         r = rows[i].findAll('td')
         task_name = f'{r[0].get_text()} - {r[1].get_text()}'
         task_names.append(task_name)

      return task_names

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
   
# private
   def _get_user_name(self) -> str:
      with open(utils.get_cookie_path(self)) as f:
         res = re.search(r'UserName%3A(.*?)%00', f.read())
         if res:
            s = res.group(1)
            return s
         else:
            return None

   def _get_all_headers(self) -> List[str]:
      return ['submission_time', 'task', 'user', 'language', 'score', 'code_size', 'status', 'exec_time', 'memory']

   def _get_statuses(self) -> List[str]:
      return ['AC', 'CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA']

   def _get_status_color(self, status: str):
      green = ['AC']
      yellow = ['CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA']
      gray_status = ['WJ']
      if status in green:
         return utils.backRGB(92, 184, 92)
      elif status in yellow:
         return utils.backRGB(240, 173, 78)
      else:
         return utils.backRGB(153, 153, 153)
