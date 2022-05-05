"""Loads SQL commands from disk and stores them for later access."""

import os

__all__ = [
    'GET_BASE_BY_ID_SQL',
    'GET_CONTINENTS_SQL',
    'GET_SERVERS_SQL',
    'GET_TRACKED_SERVERS_SQL',
    'POP_BASE_CONTROL_SQL',
    'POP_PLAYER_BLIP_SQL',
]

# Relative directory to the SQL files
_PROJECT_DIR = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
_SQL_DIR = os.path.join(_PROJECT_DIR, 'sql')


def _get_sql(filename: str) -> str:
    """Loads a file from disk and returns its contents."""
    with open(os.path.join(_SQL_DIR, filename), encoding='utf-8') as sql_file:
        return sql_file.read()


GET_BASE_BY_ID_SQL = _get_sql('get_BaseById.sql')
GET_CONTINENTS_SQL = _get_sql('get_Continents.sql')
GET_SERVERS_SQL = _get_sql('get_Servers.sql')
GET_TRACKED_SERVERS_SQL = _get_sql('get_TrackedServers.sql')
POP_BASE_CONTROL_SQL = _get_sql('pop_BaseControl.sql')
POP_PLAYER_BLIP_SQL = _get_sql('pop_PlayerBlip.sql')
