import argparse
import getpass
from logging import getLogger
import pathlib

import atcoder_submit_status.utils as utils

logger = getLogger(__name__)

def add_subparser(subparsers: argparse.Action) -> None:
   subparsers_add_parser: Callable[..., argparse.ArgumentParser] = subparsers.add_parser  # type: ignore
   subparser = subparsers_add_parser('login', aliases=['l'], help='login to a service', formatter_class=argparse.RawTextHelpFormatter, epilog='''\
Supported Services:
  √ AtCoder
''')
   subparser.add_argument('url')
   subparser.add_argument('-u', '--username')
   subparser.add_argument('-p', '--password')
   subparser.add_argument('--check', action='store_true', help='check whether you are logged in or not')

def run(args: argparse.Namespace) -> bool:
   service = utils.service_from_url(args.url)

   if service is None:
      return False

   with utils.new_session_with_our_user_agent(args.cookie, service=service) as session:
      if service.is_logged_in(session):
         logger.info(utils.SUCCESS_ICON + ' You have already signed in.')
         return True
      else:
         logger.info(utils.FAILURE_ICON + ' are not signed in.')
         if args.check:
            return False

      username = args.username
      if username is None:
         username = input(utils.INPUT_ICON + ' Username: ')
      password = args.password
      if password is None:
         password = getpass.getpass(prompt=f'{utils.INPUT_ICON} Password: ')

      service.login(username, password, session)