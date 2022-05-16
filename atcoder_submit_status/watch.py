import argparse
import getpass
import requests
from logging import getLogger
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style

import atcoder_submit_status.utils as utils

logger = getLogger(__name__)

def add_subparser(subparsers: argparse.Action) -> None:
   subparsers_add_parser: Callable[..., argparse.ArgumentParser] = subparsers.add_parser  # type: ignore
   subparser = subparsers_add_parser('watch', aliases=['w'], help='watch the contest submissions', formatter_class=  argparse.RawTextHelpFormatter, epilog='''\
Supported Services:
  √ AtCoder
''')
   subparser.add_argument('url')
   subparser.add_argument('--minimal', '-m', action='store_true', help='show minimal data')

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

      submissions = service.fetch_submissions(args.url, users=[], session=session)
      if args.minimal:
         logger.debug('Minimal')
         submissions = service.minimize_submissions_info(submissions)

      for s in submissions:
         disp = ' │ '.join(it for it in s.values())
         print(disp)