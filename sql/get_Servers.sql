-- Retrieve all known servers from the database
SELECT (
    "id",
    "name",
    "region"
)
FROM
    "Public"."Server"
;