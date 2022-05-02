-- Retrieve all tracked servers from the database
SELECT (
    "id",
    "name",
    "region"
)
FROM
    "Public"."Server"
WHERE
    "tracking_enabled" = TRUE
;