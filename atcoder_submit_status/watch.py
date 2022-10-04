import argparse
from copy import deepcopy
import sys
import sys
import time
from typing import Optional
import requests
from logging import getLogger
from colorama import Fore, Back, Style, Cursor
from rich.console import Console
from rich.live import Live

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
   subparser.add_argument('--statuses', default=[], nargs='*', choices=['AC', 'CE', 'MLE', 'TLE', 'RE', 'OLE', 'IE', 'WA', 'WJ', 'WR'], help='Select statuses.\n(e.g. WA TLE)')
   subparser.add_argument('-u', '--users', metavar='<user-name>', default=[], nargs='*', help='Select users.')
   subparser.add_argument('--info-level', default='NORMAL', choices=['MINIMAL', 'NORMAL', 'DETAILS'], help='Select output information level.')
   subparser.add_argument('-r', '--reverse', action='store_true', help='Reverse submissions')
   subparser.add_argument('-t', '--tail', metavar='<n-lines>', default=sys.maxsize, type=int, help='Print the last <n-lines> submissions.')


def _fetch(args: argparse.Namespace, srv: service.Service, session: Optional[requests.Session] = None):
   session = session or utils.get_default_session()
   submissions = srv.fetch_submissions(args.url, tasks=args.tasks, languages=args.languages, statuses=args.statuses, users=args.users, session=session)
   if args.info_level != 'DETAILS':
      submissions = srv.minimize_submissions_info(submissions, args.info_level)
   return submissions


def run(args: argparse.Namespace) -> bool:
   logger.debug(f'users: {args.users}')
   srv = utils.service_from_url(args.url)

   if srv is None:
      logger.info('we predict that the service you use is AtCoder.')
      srv = service.AtCoderService()

   with utils.new_session_with_our_user_agent(args.cookie, service=srv) as session:
      logger.debug('start session')
      if not srv.is_logged_in(session):
         logger.info(utils.FAILURE + 'You are not signed in.')
         logger.info(utils.HINT + 'You can try to enter this command: `acss login URL`')
         return False

      submissions = []
      try:
         with Live(refresh_per_second=1) as live:
            while True:
               submissions = srv.make_drawable_submissions(_fetch(args, srv=srv, session=session)[-args.tail:], args.no_color)
               if args.reverse:
                  submissions.reverse()
               live.update(submissions)
               time.sleep(1)
      except KeyboardInterrupt:
         sys.exit(0)
