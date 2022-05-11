-- Retrieve a base by its unique ID
SELECT (
    "id",
    "name",
    "continent_id",
    "type"::text,
    "map_pos_x",
    "map_pos_y"
)
FROM
    "API_static"."Base"
WHERE
    "id" = $1
;