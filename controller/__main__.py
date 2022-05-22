"""Main script for launching the backend map server.

This script sets up logging, connects to the database and sets up the
event dispatching system.

For a list of command line arguments and their purpose, run this script
with the ``--help`` flag set.
"""

import argparse
import asyncio
import logging
import os

from ._db import create_pool
from ._dispatcher import EventDispatcher
from .handlers import BaseOwnershipController

log = logging.getLogger('controller')

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


async def main(
    # Census API key
    service_id: str,
    # DB connection parameters
    db_host: str,  db_port: int, db_user: str, db_pass: str, db_name: str,
    # Event handler enabled status
    base_ownership: bool = True,

) -> None:
    """Asynchronous component of the backend server script.

    This coroutine acts much like the ``if __name__ == '__main__':``
    clause below, but supports asynchronous methods.

    Args:
        service_id: The census API service ID to use.
        db_host: Host address of the database server.
        db_port: Port of the database server.
        db_user: Login user for the database server.
        db_pass: Login password for the database server.
        db_name: Name of the database to access.

    """
    # Create database connection
    log.info('Connecting to database \'%s\' at %s as user \'%s\'...',
             db_name, db_host, db_user)
    pool = create_pool(db_host, db_port, db_user,  db_pass, db_name)
    log.info('Database connection successful')
    # Set up dispatcher
    log.info('Preparing event dispatcher...')
    dispatcher = EventDispatcher(pool)

    # Register event handlers
    if base_ownership:
        dispatcher.add_handler(BaseOwnershipController(pool, service_id))

    # This try block catches any interrupts and ensures all of the components
    # are exited gracefully before the error gets thrown at the user's screen.
    try:
        await dispatcher.run()
    except BaseException:  # pylint: disable=broad-except
        log.exception('An exception has occurred; closing connections...')
    finally:
        log.info('Closing database connection...')
        await pool.close()


if __name__ == '__main__':  # pragma: no cover
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy())
    # Get default values from environment
    def_service_id = os.getenv('PS2MAP_SERVICE_ID', 's:example')
    def_db_host = os.getenv('PS2MAP_DB_HOST', DEFAULT_DB_HOST)
    def_db_port = int(os.getenv('PS2MAP_DB_PORT', str(DEFAULT_DB_PORT)))
    def_db_name = os.getenv('PS2MAP_DB_NAME', DEFAULT_DB_NAME)
    def_db_user = os.getenv('PS2MAP_DB_USER', DEFAULT_DB_USER)
    def_db_pass = os.getenv('PS2MAP_DB_PASS')
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
        '--db-port', '-T', default=def_db_port,
        help='The port of the database host')
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
