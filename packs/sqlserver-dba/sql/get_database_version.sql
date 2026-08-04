SELECT CONVERT(varchar, SERVERPROPERTY('productversion')) AS version,
       CONVERT(int, PARSENAME(CONVERT(varchar, SERVERPROPERTY('productversion')), 4)) AS version_number,
       SUBSTRING(@@VERSION, 1, 120) AS full_version
