-- Retrieve all tracked servers from the database
SELECT (
    "id"
)
FROM
    "API_static"."Server"
WHERE
    "tracking_enabled" = TRUE
;