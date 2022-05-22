"""Loads SQL commands from disk and stores them for later access."""

import os

__all__ = [
    'SQL_POP_BASE_CONTROL',
    'SQL_GET_CONTINENTS',
    'SQL_GET_TRACKED_SERVERS',
    'SQL_UPDATE_BASE_OWNERSHIP',
]

# Relative directory to the SQL files
_PROJECT_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
_SQL_DIR = os.path.join(_PROJECT_DIR, 'sql')


def _get_sql(filename: str) -> str:
    """Loads a file from disk and returns its contents."""
    with open(os.path.join(_SQL_DIR, filename), encoding='utf-8') as sql_file:
        return sql_file.read()


SQL_POP_BASE_CONTROL = _get_sql('pop_BaseControl.sql')
SQL_GET_CONTINENTS = _get_sql('get_Continents.sql')
SQL_GET_TRACKED_SERVERS = _get_sql('get_TrackedServers.sql')
SQL_UPDATE_BASE_OWNERSHIP = _get_sql('update_BaseOwnership.sql')
