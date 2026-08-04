SELECT version,
       version_number,
       full_version
FROM (SELECT REGEXP_SUBSTR(banner, '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?') AS version,
             CAST(REGEXP_REPLACE(
                 REGEXP_SUBSTR(banner, '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?'),
                 '[^0-9]', '') AS NUMBER) AS version_number,
             banner AS full_version
      FROM v$version
      WHERE banner LIKE 'Oracle%'
      FETCH FIRST 1 ROWS ONLY)
