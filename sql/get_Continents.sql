-- Retrieve all supported continents from the database
SELECT (
    "id"
)
FROM
    "API_static"."Continent"
WHERE
    "hidden" = false
;