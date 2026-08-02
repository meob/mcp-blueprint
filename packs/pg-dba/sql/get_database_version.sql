SELECT regexp_replace(current_setting('server_version'), '[^0-9.].*$', '') AS version,
       current_setting('server_version_num')                                AS version_number,
       version()                                                           AS full_version;
