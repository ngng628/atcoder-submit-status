import argparse
from email.errors import HeaderParseError
import sys
from typing import *
from logging import DEBUG, INFO, StreamHandler, basicConfig, getLogger
import pathlib
import atcoder_submit_status.__about__ as version
import atcoder_submit_status.utils as utils
import atcoder_submit_status.login as subcommands_login
import atcoder_submit_status.logout as subcommands_logout
import atcoder_submit_status.watch as subcommands_watch
import atcoder_submit_status.log_formatter as log_formatter

logger = getLogger(__name__)

def get_parser() -> argparse.ArgumentParser:
   """パーサを生成します。
   """

   parser = argparse.ArgumentParser(
      description='Tools for AtCoder Submissions',
      formatter_class=argparse.RawTextHelpFormatter,
      epilog='''\
Tips:
  README: https://github.com/ngng628/atcoder-submit-status/blob/main/README.md
'''
   )

   parser.add_argument('-v', '--verbose', action='store_true')
   parser.add_argument('-c', '--cookie', type=pathlib.Path, default=utils.DEFAULT_COOKIE_PATH, help=f'path to cookie. (default: {utils.DEFAULT_COOKIE_PATH})')
   parser.add_argument('--version', action='store_true', help='print the atcoder-submit-status version number.')

   subparsers = parser.add_subparsers(dest='subcommand', help=f'for details, see "{sys.argv[0]} COMMAND --help"')
   subcommands_login.add_subparser(subparsers)
   subcommands_logout.add_subparser(subparsers)
   subcommands_watch.add_subparser(subparsers)

   return parser

def run_program(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
   if args.version:
      print('atcoder-submit-status {}'.format(version.__version__))
      return 0
   logger.debug(f'args: {str(args)}')

   logger.info('atcoder-submit-status %s', version.__version__)

   if args.subcommand in ['login', 'l']:
      if not subcommands_login.run(args):
         return 1
   elif args.subcommand in ['logout']:
      if not subcommands_logout.run(args):
         return 1
   elif args.subcommand in ['watch', 'w']:
      if not subcommands_watch.run(args):
         return 1
   else:
      parser.print_help(file=sys.stderr)
      return 1
   return 0

def main(args: Optional[List[str]] = None) -> 'NoReturn':
   parser = get_parser()
   parsed = parser.parse_args(args=args)

   level = INFO
   if parsed.verbose:
      level = DEBUG
   handler = StreamHandler(sys.stdout)
   handler.setFormatter(log_formatter.LogFormatter())
   basicConfig(level=level, handlers=[handler])

   # is_updated = update_checking.run()

   try:
      sys.exit(run_program(parsed, parser=parser))
   except NotImplementedError as e:
      logger.error('NotImplementedError')
      sys.exit(1)
   except Exception as e:
      logger.exception(str(e))
      sys.exit(1)