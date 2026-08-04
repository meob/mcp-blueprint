-- Development-only grants for the 'monitor' application user (Oracle Free).
-- gvenzl/oracle-free runs this file on first startup only.
-- The APP_USER lives in the pluggable database, so the script must switch
-- container before altering or granting.
ALTER SESSION SET CONTAINER = FREEPDB1;
ALTER USER monitor IDENTIFIED BY monitor_pw ACCOUNT UNLOCK;
GRANT CONNECT TO monitor;
GRANT SELECT_CATALOG_ROLE TO monitor;
GRANT SELECT ANY DICTIONARY TO monitor;
