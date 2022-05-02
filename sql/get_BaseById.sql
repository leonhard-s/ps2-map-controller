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
    "Public"."Base"
WHERE
    "id" = $1
;