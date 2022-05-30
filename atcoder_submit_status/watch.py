import argparse
import sys
import sys
import time
from typing import Optional
import requests
from logging import getLogger
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
   subparser.add_argument('--tasks', metavar='<task-name>', default=[], nargs='*', help='Select tasks.\n(e.g. a b d ex)')
   subparser.add_argument('--languages', metavar='<lang>', default=[], nargs='*', help='Select languages.\n(e.g. C++ C#)')
   subparser.add_argument('--statuses', default=[], nargs='*', choices=['AC', 'CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA', 'WR'], help='Select statuses.\n(e.g. WA TLE)')
   subparser.add_argument('-u', '--users', metavar='<user-name>', default=[], nargs='*', help='Select users.')
   subparser.add_argument('--info-level', default='NORMAL', choices=['MINIMAL', 'NORMAL', 'DETAILS'], help='Select output information level.')
   subparser.add_argument('-r', '--reverse', action='store_true', help='Reverse submissions')
   subparser.add_argument('-t', '--tail', metavar='<n-lines>', default=sys.maxsize, type=int, help='Print the last <n-lines> submissions.')

def _fetch(args: argparse.Namespace, service: service.Service, session: Optional[requests.Session] = None):
   session = session or utils.get_default_session()
   submissions = service.fetch_submissions(args.url, tasks=args.tasks, languages=args.languages, statuses=args.statuses, users=args.users, session=session)
   if args.info_level != 'DETAILS':
      submissions = service.minimize_submissions_info(submissions, args.info_level)
   return submissions

def _draw(args: argparse.Namespace, drawableSubmissions):
   print('\x1b[J', end='')
   for s in drawableSubmissions:
      print(s)

def run(args: argparse.Namespace) -> bool:
   logger.debug(f'users: {args.users}')
   service = utils.service_from_url(args.url)

   if service is None:
      return False

   with utils.new_session_with_our_user_agent(args.cookie, service=service) as session:
      logger.debug('start session')
      if not service.is_logged_in(session):
         logger.info(utils.FAILURE + 'You are not signed in.')
         logger.info(utils.HINT + 'You can try to enter this command: `acss login URL`')
         return False

      old_submissions = service.make_drawable_submissions(_fetch(args, service=service, session=session)[-args.tail:], args.no_color)
      if args.reverse:
         old_submissions.reverse()
      _draw(args, drawableSubmissions=old_submissions)
      try:
         while True:
            time.sleep(1)

            submissions = service.make_drawable_submissions(_fetch(args, service=service, session=session)[-args.tail:], args.no_color)
            if args.reverse:
               submissions.reverse()

            # TODO: カーソル移動のところをいい感じに書く
            if old_submissions != submissions:
               n = len(old_submissions)
               print('\x1b[' + str(n) + 'F', end='')
               _draw(args, drawableSubmissions=submissions)
               old_submissions = submissions
      except KeyboardInterrupt:
         sys.exit(0)
