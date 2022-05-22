-- Delete all "BaseControl" events and return them
DELETE FROM "EventBuffer"."BaseControl"
WHERE
    "timestamp" < %s
RETURNING (
    "timestamp",
    "server_id",
    "continent_id",
    "base_id",
    "old_faction_id",
    "new_faction_id"
);
