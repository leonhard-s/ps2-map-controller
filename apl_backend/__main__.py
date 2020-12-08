"""Main script for launching the APL backend component.

This script sets up logging, checks for database availability and
creates the stack. This includes the database scraper, the map state
handlers and the REST API accessed by the frontend.

For a list of command line arguments and their purpose, run this script
with the ``--help`` flag set.

"""

import argparse
import asyncio
import logging

log = logging.getLogger('listener')

# Default database configuration
DEFAULT_DB_HOST = '127.0.0.1'
DEFAULT_DB_NAME = 'apl'
DEFAULT_DB_USER = 'postgres'

# Logging configuration
fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
fh_ = logging.FileHandler(filename='debug.log', encoding='utf-8', mode='w+')
sh_ = logging.StreamHandler()
fh_.setFormatter(fmt)
sh_.setFormatter(fmt)


async def main(service_id: str, db_host: str, db_user: str,
               db_pass: str, db_name: str) -> None:
    """Asynchronous component of the main listener script.

    This coroutine acts much like the ``if __name__ == '__main___':``
    clause below, but supports asynchronous methods.

    :param service_id: The Census API service ID to use.
    :param db_host: The host address of the PostgreSQL server.
    :param db_user: The database username to log in as.
    :param db_pass: The database password to use when logging in.
    :param db_name: The name of the database to acces.

    """
    # TODO: Implement backend server stack
    raise NotImplementedError

if __name__ == '__main__':
    # Define command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--service-id', '-S', default='s:example',
        help='The service ID used to access the PS2 API')
    parser.add_argument(
        '--db-user', '-U', default=DEFAULT_DB_USER,
        help='The user account to use when connecting to the database')
    parser.add_argument(
        '--db-pass', '-P', required=True,
        help='The password to use when connecting to the database')
    parser.add_argument(
        '--db-host', '-H', default=DEFAULT_DB_HOST,
        help='The address of the database host')
    parser.add_argument(
        '--db-name', '-N', default=DEFAULT_DB_NAME,
        help='The name of the database to access')
    parser.add_argument(
        '--log-level', '-L', default='INFO',
        choices=['DISABLE', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='The log level to use; for levels greater than "DEBUG", '
             'the logging input from Auraxium will also be included')
    # Parse arguments from sys.argv
    kwargs = vars(parser.parse_args())
    # Optioanlly set up logging
    if kwargs['log_level'] != 'DISABLE':
        log_level = getattr(logging, kwargs.pop('log_level'))
        log.setLevel(log_level)
        log.addHandler(fh_)
        log.addHandler(sh_)
        # Add another logger for auraxium
        arx_log = logging.getLogger('auraxium')
        # The following will exclude auraxium's DEBUG spam from this logger
        arx_log.setLevel(max(log_level, logging.INFO))
        arx_log.addHandler(fh_)
        arx_log.addHandler(sh_)
    # Run utility
    try:
        asyncio.run(main(**kwargs))
    except InterruptedError:
        log.info('The application has been shut down by an external signal')
    except KeyboardInterrupt:
        log.info('The application has been shut down by the user')
    except BaseException as err:
        log.exception('An unhandled exception occurred:')
        raise err from err
