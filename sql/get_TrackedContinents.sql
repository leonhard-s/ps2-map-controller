-- Retrieve all tracked continents from the database
SELECT (
    "id"
)
FROM
    "API_static"."Continent"
WHERE
    "tracking_enabled" = TRUE
;