"""Custom uvicorn-based server for hosting the API.

Uvicorn, the underlying server used for hosting the FastAPI app, does
not support programmatical shutoff or restart. Additionally, it expects
to be run in the main thread and will raise exceptions otherwise.

This module defines the ``ApiHost`` wrapper class which provides hooks
for starting and stopping the API server, as well as comunicating
between threads.
"""

# NOTE: This implementation was inspired by the following comment by
# @florimondmanca on GitHub:
# <https://github.com/encode/uvicorn/issues/742#issuecomment-674411676>

import asyncio
import logging
import threading

import uvicorn

from ._types import Server

log = logging.getLogger('api.host')


class ApiHost:

    def __init__(self) -> None:
        config = uvicorn.Config('apl_backend._api._app:app', host='127.0.0.1',
                                port=5000, log_level='info', loop='asyncio')
        self._server: Server = uvicorn.Server(config=config)  # type: ignore
        self._thread = threading.Thread(target=self._server.run)
        # Daemon threads are stopped once all non-Daemon threads have exited.
        self._thread.setDaemon(True)

    async def restart(self) -> None:
        """Restart the underlying API server.

        This first creates a new API host before shutting down the old
        thread, resulting in minimal downtime between instances.
        """
        log.info('Restarting API host...')
        await self.stop()
        await self.start()

    async def start(self) -> None:
        """Start the API server.

        Due to uvicorn ideosyncracies, the underlying API server must
        reside in its own standalone thread. This method creates and
        starts this thread and returns once the server reports being
        ready.

        This method returns once the threaded server reports as ready.
        Use ``asyncio.AbstractEventLoop.create_task()`` if you do not
        want to await the thread spawning delay.
        """
        log.debug('Starting API server')
        try:
            self._thread.start()
        except RuntimeError as err:
            raise RuntimeError('Thread already running, await ApiHost.stop() '
                               'before scheduling a new thread') from err
        log.debug('Waiting for API server startup to complete...')
        # Wait for the server to finish its start-up sequence before returning
        while not self._server.started:
            await asyncio.sleep(1e-3)

    async def stop(self) -> None:
        """Shut down the underlying API server and destroy its thread.

        This method will return once the thread is destroyed and all
        clean-up has been performed.
        """
        log.debug('Requesting API server shutdown')
        self._server.should_exit = True
        log.info('Awaiting termination of API server...')
        self._thread.join()
