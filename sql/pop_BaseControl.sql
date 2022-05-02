-- Deletes and returns all BaseControl Blips from the database
DELETE FROM
    "Blip"."BaseControl"
WHERE
    "timestamp" < $1
RETURNING (
    "timestamp",
    "server_id",
    "continent_id",
    "base_id",
    "old_faction_id",
    "new_faction_id"
);