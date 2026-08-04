-- Development-only grants for the 'monitor' user (MariaDB 11.4).
-- Runs on first startup via /docker-entrypoint-initdb.d.
GRANT PROCESS, REPLICATION CLIENT, SHOW DATABASES ON *.* TO 'monitor'@'%';
GRANT SELECT ON *.* TO 'monitor'@'%';
GRANT SELECT ON performance_schema.* TO 'monitor'@'%';
GRANT SELECT ON mysql.user TO 'monitor'@'%';
FLUSH PRIVILEGES;
