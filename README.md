# PS2 Map Controller

This component is responsible for processing events received from the [Event Listener](https://github.com/leonhard-s/ps2-map-listener), validating them, and updating the map state accordingly. This then gets mirrored to the database, which is used to feed the [API Host](https://github.com/leonhard-s/ps2-map-api).

## What it does

The controller consists of a primary loop which runs in the background, scraping any new events from the event buffer tables and processing them.

Depending on the event type, the controller will then forward these batches of events to the appropriate handler. These handlers are each responsible for a single independent aspect of the map, such as population tracking, base ownership updates, or alert states, and are free to handle any events they require to complete that task.

## Status

The controller is currently being completely rewritten and is not yet functional.
