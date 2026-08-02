SELECT v.version AS version,
       CAST(SUBSTRING_INDEX(v.clean, '.', 1) AS UNSIGNED) * 10000
       + CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(v.clean, '.', 2), '.', -1) AS UNSIGNED) * 100
       + CAST(SUBSTRING_INDEX(v.clean, '.', -1) AS UNSIGNED) AS version_number,
       CONCAT(v.version, ' ', @@version_comment) AS full_version
FROM (SELECT VERSION() AS version,
             REGEXP_REPLACE(VERSION(), '[^0-9.].*$', '') AS clean) AS v;
