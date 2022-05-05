"""Main script for launching the map controller component.

This script sets up logging, checks for database availability and
creates the backend server. This includes the database scraper, the map
state handlers and the population tracker.

For a list of command line arguments and their purpose, run this script
with the ``--help`` flag set.
"""

import argparse
import asyncio
import logging
import os

import auraxium

from ._db import DatabaseHandler
from ._map import MapHandler
from ._server import BackendServer

log = logging.getLogger('backend')

# Default database configuration
DEFAULT_DB_HOST = '127.0.0.1'
DEFAULT_DB_PORT = 5432
DEFAULT_DB_NAME = 'PS2Map'
DEFAULT_DB_USER = 'postgres'

# Logging configuration
fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
fh_ = logging.FileHandler(filename='debug.log', encoding='utf-8', mode='w+')
sh_ = logging.StreamHandler()
fh_.setFormatter(fmt)
sh_.setFormatter(fmt)


async def main(service_id: str, db_host: str, db_port: int, db_user: str,
               db_pass: str, db_name: str) -> None:
    """Asynchronous component of the main listener script.

    This coroutine acts much like the ``if __name__ == '__main___':``
    clause below, but supports asynchronous methods.

    Any keyword arguments are forwarded to the :class:`Server` class's
    initialiser.

    """
    log.info('Setting up Auraxium API client...')
    arx_client = auraxium.Client(service_id=service_id)
    log.info('Starting database handler...')
    db_handler = DatabaseHandler(db_host, db_port, db_user, db_pass, db_name)
    log.info('Initialising backend server...')
    server = BackendServer(arx_client, db_handler, {})
    await server.async_init()
    log.info('Retrieving static tables...')
    servers = [s[0] for s in await db_handler.get_servers()]
    continents = [i[0] for i in await db_handler.get_continents()]
    log.info('Spawning map handlers (monitoring %d servers)', len(servers))
    server.map_handlers = {i: MapHandler(i, continents) for i in servers}


if __name__ == '__main__':
    # Get default values from environment
    def_service_id = os.getenv('SERVICE_ID', 's:example')
    def_db_host = os.getenv('DB_HOST', DEFAULT_DB_HOST)
    def_db_port = int(os.getenv('DB_PORT', str(DEFAULT_DB_PORT)))
    def_db_name = os.getenv('DB_NAME', DEFAULT_DB_NAME)
    def_db_user = os.getenv('DB_USER', DEFAULT_DB_USER)
    def_db_pass = os.getenv('DB_PASS')
    # Define command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--service-id', '-S', default=def_service_id,
        help='The service ID used to access the PS2 API')
    parser.add_argument(
        '--db-user', '-U', default=def_db_user,
        help='The user account to use when connecting to the database')
    parser.add_argument(
        '--db-pass', '-P', required=def_db_pass is None, default=def_db_pass,
        help='The password to use when connecting to the database')
    parser.add_argument(
        '--db-host', '-H', default=def_db_host,
        help='The address of the database host')
    parser.add_argument(
        '--db-name', '-N', default=def_db_name,
        help='The name of the database to access')
    parser.add_argument(
        '--log-level', '-L', default='INFO',
        choices=['DISABLE', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='The log level to use; for levels greater than "DEBUG", '
             'the logging input from Auraxium will also be included')
    # Parse arguments from sys.argv
    kwargs = vars(parser.parse_args())
    # Optionally set up logging
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
    loop = asyncio.get_event_loop()
    loop.create_task(main(**kwargs))
    try:
        loop.run_forever()
    except InterruptedError:
        log.info('The application has been shut down by an external signal')
    except KeyboardInterrupt:
        log.info('The application has been shut down by the user')
    except BaseException as err:
        log.exception('An unhandled exception occurred:')
        raise err from err
