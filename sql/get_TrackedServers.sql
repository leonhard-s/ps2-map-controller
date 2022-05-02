-- Retrieve all tracked servers from the database
SELECT (
    "id",
    "name",
    "region"
)
FROM
    "API"."Server"
WHERE
    "tracking_enabled" = TRUE
;