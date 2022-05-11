-- Retrieve all known servers from the database
SELECT (
    "id",
    "name",
    "region"
)
FROM
    "API_static"."Server"
;