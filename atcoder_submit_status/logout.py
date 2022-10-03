import os
import argparse
import getpass
from logging import getLogger
import pathlib

import atcoder_submit_status.utils as utils

logger = getLogger(__name__)

def add_subparser(subparsers: argparse.Action) -> None:
   subparsers_add_parser: Callable[..., argparse.ArgumentParser] = subparsers.add_parser  # type: ignore
   subparser = subparsers_add_parser('logout', help='logout to a service', formatter_class=argparse.RawTextHelpFormatter, epilog='''\
Supported Services:
  √ AtCoder
''')
   subparser.add_argument('service', choices=['atcoder'])
   subparser.add_argument('--check', action='store_true', help='check whether you are logged out or not')

def run(args: argparse.Namespace) -> bool:
   service = utils.service_from_url(args.service)

   if service is None:
      return False
   
   cookie_path = utils.get_cookie_path(service=service)
   if os.path.exists(cookie_path):
      os.remove(cookie_path)
      logger.info(f'delete cookie to {cookie_path}')
      logger.info(utils.SUCCESS + 'You have already signed out.')
      return True
   else:
      logger.info(utils.FAILURE + 'You are not signed in.')
      if args.check:
         return False
      return True
      