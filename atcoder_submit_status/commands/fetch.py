from curses import REPORT_MOUSE_POSITION
import colorama
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style

def rgb(r, g, b):
   return "\x1b[48;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"

def run():
   LOGIN_URL = 'https://atcoder.jp/login'
   SUBMITTIONS_URL = 'https://atcoder.jp/contests/abc251/submissions/me'

   with requests.session() as session:
      # ログイン処理
      response = session.get(LOGIN_URL)
      response.raise_for_status()
      soup = BeautifulSoup(response.text, 'lxml')
      csrf_token = soup.find(attrs={'name': 'csrf_token'}).get('value')
      password = input('[o] パスワード: ')
      login_info = { 'csrf_token': csrf_token, 'username': 'ngng628', 'password': password }

      print('ログインします')
      response = session.post(LOGIN_URL, data=login_info)
      response.raise_for_status()

      assert(response.url == 'https://atcoder.jp/home')
      print('ログイン完了')

      # 順位表を見る
      print('[o] SUBMITTION')
      response = session.get(SUBMITTIONS_URL)
      response.raise_for_status()
      soup = BeautifulSoup(response.text, 'lxml')
      
      table = soup.findAll('table', {'class': 'table' })[0]
      rows = table.findAll('tr')


      submissions = []
      keys = ['submission_time', 'task', 'user', 'language', 'score', 'code_size', 'status', 'exec_time', 'memory']
      max_lengths = { key: 0 for key in keys }
      for i in range(len(rows)):
         if i == 0:
            continue
         r = rows[i].findAll('td')
         submission = { keys[i]: r[i].get_text() for i in range(len(keys)) }
         submission['submission_time'] = submission['submission_time'][:16]
         submission['score'] = '{:,}'.format(int(submission['score']))
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
                  submission[key] = rgb(92, 184, 92) + Fore.WHITE + ' ' + submission[key] + ' ' + Style.RESET_ALL
               else:
                  submission[key] = rgb(240, 173, 78) + Fore.WHITE + ' ' + submission[key] + ' ' + Style.RESET_ALL


      for submission in submissions:
         s = ' | '.join(submission[key] for key in keys)
         print(s)

run()

