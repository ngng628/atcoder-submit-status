import argparse
import sys
from email.policy import default
import sys
import time
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
   subparser.add_argument('url', help='Contest URL')
   subparser.add_argument('--no-color', action='store_true', help='Turn off color')
   subparser.add_argument('-r', '--reverse', action='store_true', help='Reverse submissions')
   subparser.add_argument('--tasks', default=[], nargs='*', help='Select tasks.\n(e.g. a b d ex)')
   subparser.add_argument('--languages', default=[], nargs='*', help='Select languages.\n(e.g. C++ C#)')
   subparser.add_argument('--statuses', default=[], nargs='*', choices=['AC', 'CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA'], help='Select statuses.\n(e.g. WA TLE)')
   subparser.add_argument('-u', '--users', default=[], nargs='*', help='Watch users.')
   subparser.add_argument('--info-mode', default='NORMAL', choices=['MINIMAL', 'NORMAL', 'DETAILS'], help='表示の細かさを設定します')
   subparser.add_argument('-t', '--tail', default=sys.maxsize, type=int, help='Print the last $TAIL submissions')

def _fetch(args: argparse.Namespace, service: service.Service, session: Optional[requests.Session] = None):
   session = session or utils.get_default_session()
   submissions = service.fetch_submissions(args.url, no_color=args.no_color, tasks=args.tasks, languages=args.languages, statuses=args.statuses, users=args.users, session=session)
   if args.info_mode != 'DETAILS':
      submissions = service.minimize_submissions_info(submissions, args.info_mode)
   return submissions

def _draw(args: argparse.Namespace, submissions):
   print('\x1b[J', end='')
   for s in submissions[-args.tail:]:
      disp = ' │ '.join(it for it in s.values())
      print(disp)


def run(args: argparse.Namespace) -> bool:
   logger.debug('called watch')
   logger.debug(f'users: {args.users}')
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
      if args.reverse:
         old_submissions.reverse()
      _draw(args, old_submissions)
      try:
         while True:
            time.sleep(1)

            submissions = _fetch(args, service=service, session=session)
            if args.reverse:
               submissions.reverse()

            # TODO: データが増えることを前提としている
            if old_submissions != submissions:
               n = len(old_submissions)
               print('\x1b[' + str(n) + 'F', end='')
               _draw(args, submissions=submissions)
               old_submissions = submissions
      except KeyboardInterrupt:
         sys.exit(0)
