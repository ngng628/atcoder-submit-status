from abc import abstractmethod
from datetime import datetime
import sys
import time
from copy import deepcopy
import re
from typing import *
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import atcoder_submit_status.__about__ as version
import atcoder_submit_status.utils as utils
from rich.table import Table
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
   def is_logged_in(self) -> bool:
      pass


   @abstractmethod
   def fetch_submissions(self, url, tasks, languages, statuses, users, session):
      pass


   @abstractmethod
   def minimize_submissions_info(self, submissions, mode):
      pass


   @abstractmethod
   def make_drawable_submissions(self, submissions, no_color):
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
      logger.info(utils.NETWORK + f'GET: {url}')
      response = session.get(url)
      soup = BeautifulSoup(response.text, 'lxml')
      csrf_token = soup.find(attrs={'name': 'csrf_token'}).get('value')
      login_info = { 'csrf_token': csrf_token, 'username': username, 'password': password }
      try:
         response = session.post(url, data=login_info)
         response.raise_for_status()
      except requests.exceptions.HTTPError as e:
         logger.error(e)
         exit()



   def is_logged_in(self, session: Optional[requests.Session] = None) -> bool:
      session = session or utils.get_default_session()
      url = 'https://atcoder.jp/contests/dummydummydummy/submit'
      logger.debug(utils.NETWORK + f'GET: {url}')
      response = session.get(url)
      if response.status_code == 404:
         return True
      else:
         return False


   def fetch_submissions(self, url: str, tasks: List[str] = [], languages: List[str] = [], statuses: List[str] = [], users: List[str] = [], session: Optional[requests.Session] = None):
      session = session or utils.get_default_session()

      contest_round = self.get_round(url)
      submissions_url = self.get_url() + '/contests/' + contest_round + '/submissions'

      # 全体の提出を見る権限があるかを確認
      response = session.get(submissions_url)
      logger.debug(f'status_code = {response.status_code}')
      logger.debug(f'type(status_code) = {type(response.status_code)}')
      if response.status_code == 404:
         submissions_url += '/me'

      # フィルタ用データの調整
      if not users:
         name = self._get_user_name()
         if name:
            users.append(name)
         else:
            logger.info(utils.FAILURE + 'users not found.')
            sys.exit(0)

      submissions = []
      keys = self._get_all_headers()
      for user in users:
         page = 0
         while True:  # page がなくなるまで
            page += 1
            time.sleep(0.25)

            payload = { 'page': page }
            if user:
               payload['f.User'] = user

            try:
               response = session.get(submissions_url, params=payload)
               response.raise_for_status()
            except requests.exceptions.HTTPError as e:
               logger.error(e)
               exit()

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

               # フィルター
               if not tasks or utils.get_task_id(submission['task']).lower() in [t.lower() for t in tasks]:
                  if not statuses or submission['status'] in statuses or sum(int(submission['status'] not in self._get_statuses() and s == 'WJ') for s in statuses) != 0:
                     if not languages or utils.convert_language_with_version_to_language(submission['language']) in languages:
                        submissions.append(submission)

      submissions = sorted(submissions, key=lambda x: datetime.strptime(x['submission_time'], '%Y-%m-%d %H:%M:%S'))

      return submissions

   def minimize_submissions_info(self, submissions, mode):
      res = deepcopy(submissions)
      for i in range(len(res)):
         if 'submission_time' in res[i]:
            if mode == 'MINIMAL':
               res[i].pop('submission_time')
         if 'task' in res[i]:
            res[i]['task'] = utils.get_task_id(res[i]['task'])
         if 'language' in res[i]:
            if mode == 'MINIMAL':
               res[i].pop('language')
            elif mode == 'NORMAL':
               res[i]['language'] = utils.convert_language_with_version_to_language(res[i]['language'])
         if 'code_size' in res[i]:
            res[i].pop('code_size')
         if 'exec_time' in res[i]:
            res[i].pop('exec_time')
         if 'memory' in res[i]:
            res[i].pop('memory')

      return res


   def make_drawable_submissions(self, submissions, no_color: bool):
      submits = deepcopy(submissions)

      # Statusには色をつけておく
      from rich.padding import Padding
      for i in range(len(submits)):
         status = submits[i]['status'][-3:].strip()
         if not no_color:
            color = self._get_status_color(status)
            submits[i]['status'] = Padding(submits[i]['status'], (0, 1), style=color)

      # Tableを構築する
      table = Table()

      if len(submits) == 0:
         return table

      ## カラムの定義
      for key in submits[0].keys():
         if key in ['score', 'code_size', 'exec_time', 'memory']:
            table.add_column(key, justify='right')
         elif key in ['status']:
            table.add_column(key, justify='center')
         else:
            table.add_column(key, justify='left')

      ## ラインの定義
      for submit in submits:
         row = [val for val in submit.values()]
         table.add_row(*row)

      return table


   def get_task_names(self, tasks_url, session: Optional[requests.Session] = None) -> List[str]:
      session = session or utils.get_default_session()

      try:
         response = session.get(tasks_url)
         response.raise_for_status()
      except requests.exceptions.HTTPError as e:
         logger.error(e)
         exit()

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


   def get_round(self, url: str) -> str:
      """
      コンテスト名を取得します。

      url が 'https://atcoder.jp/contests/' で始まらないとき、url が round 名そのものであると解釈します。
      """
      prefix = 'https://atcoder.jp/contests/'

      if url.startswith(prefix):
         if url[-1] != '/':
            url = url + '/'
         return url[len(prefix):url.find('/', len(prefix))]
      else:
         return url


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
      return ['AC', 'CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA', 'WJ', 'WR']


   def _get_status_color(self, status: str):
      green = ['AC']
      yellow = ['CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA']
      gray_status = ['WJ', 'WR']
      if status in green:
         return 'rgb(255,255,255) on rgb(92,184,92)'
      elif status in yellow:
         return 'rgb(255,255,255) on rgb(240,173,78)'
      else:
         return 'rgb(255,255,255) on rgb(153,153,153)'
