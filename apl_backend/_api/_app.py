"""Main API application.

This module defines all REST and WebSocket endpoints available via the
API and is called by the uvicorn server hosted in a standalone thread.

This module is **not** imported by the main thread; it is therefore
safe to import utilities and names from elsewhere without needing to
worry about circular dependencies - by the time this module's code is
executed, everything else will already be initialised.
"""

import logging

import fastapi
from fastapi.responses import JSONResponse

from ._logging import ForwardHandler

# Forward the uvicorn log events to the APL handlers instead
log = logging.getLogger('api.server')
logging.getLogger('uvicorn').handlers = [ForwardHandler(log)]

app = fastapi.FastAPI()


@app.get('/')  # type: ignore
async def root() -> JSONResponse:
    """Default endpoint for empty query."""
    return JSONResponse({'Welcome': 'Nothing to be seen here'})
