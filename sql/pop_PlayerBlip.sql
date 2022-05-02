-- Deletes and returns all PlayerBlips from the database
DELETE FROM
    "Blip"."PlayerBlip"
WHERE
    "timestamp" < $1
RETURNING (
    "timestamp",
    "server_id",
    "continent_id",
    "player_id",
    "base_id"
);