-- Set the base control info in the database.
UPDATE "API_dynamic"."BaseOwnership"
SET
    "owning_faction_id" = %s,
    "owned_since" = %s
WHERE
    "base_id" = %s
AND
    "server_id" = %s
;
