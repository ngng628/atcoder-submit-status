import argparse
import time
from concurrent.futures import ThreadPoolExecutor
import getpass
from typing import Optional
import requests
from logging import getLogger
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style

import atcoder_submit_status.utils as utils
import atcoder_submit_status.service as service

logger = getLogger(__name__)

def add_subparser(subparsers: argparse.Action) -> None:
   subparsers_add_parser: Callable[..., argparse.ArgumentParser] = subparsers.add_parser  # type: ignore
   subparser = subparsers_add_parser('watch', aliases=['w'], help='watch the contest submissions', formatter_class=  argparse.RawTextHelpFormatter, epilog='''\
Supported Services:
  √ AtCoder
''')
   subparser.add_argument('url')
   subparser.add_argument('--minimal', '-m', action='store_true', help='show minimal data')

def _fetch(args: argparse.Namespace, service: service.Service, session: Optional[requests.Session] = None):
   session = session or utils.get_default_session()
   submissions = service.fetch_submissions(args.url, users=[], session=session)
   if args.minimal:
      logger.debug('Minimal')
      submissions = service.minimize_submissions_info(submissions)
   return submissions

def _draw(submissions):
   print('\x1b[J', end='')
   for s in submissions:
      disp = ' │ '.join(it for it in s.values())
      print(disp)


def run(args: argparse.Namespace) -> bool:
   logger.debug('called watch')
   service = utils.service_from_url(args.url)

   if service is None:
      return False

   with utils.new_session_with_our_user_agent(args.cookie, service=service) as session:
      logger.debug('start session')
      if not service.is_logged_in(session):
         logger.info(utils.FAILURE_ICON + ' You are not signed in.')
         logger.info(utils.HINT_ICON + ' You can try to enter this command: `acss login URL`')
         return False

      old_submissions = _fetch(args, service=service, session=session)
      _draw(old_submissions)
      while True:
         time.sleep(1)

         submissions = _fetch(args, service=service, session=session)

         # TODO: データが増えることを前提としている
         if old_submissions != submissions:
            n = len(old_submissions)
            print('\x1b[' + str(n) + 'F', end='')
            _draw(submissions=submissions)
            old_submissions = submissions