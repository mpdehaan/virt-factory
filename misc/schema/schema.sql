CREATE SCHEMA virtfactory;

CREATE ROLE virtfactory LOGIN PASSWORD '%(password)s'
NOINHERIT
VALID UNTIL 'infinity';

ALTER ROLE virtfactory SET search_path=virtfactory,public;

CREATE TABLE tasks (
   id              INTEGER PRIMARY KEY,
   user_id         INTEGER NOT NULL,
   action_type     INTEGER NOT NULL,
   machine_id      INTEGER NOT NULL,
   deployment_id   INTEGER NOT NULL,
   state           INTEGER NOT NULL,
   time            REAL NOT NULL
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE tasks TO virtfactory;

CREATE TABLE users (
   id              INTEGER PRIMARY KEY,
   username        VARCHAR (255) UNIQUE NOT NULL,
   password        VARCHAR (255) NOT NULL,
   first           VARCHAR (255) NOT NULL,
   middle          VARCHAR (255),
   last            VARCHAR (255) NOT NULL,
   description     VARCHAR (255),
   email           VARCHAR (255) NOT NULL
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE users TO virtfactory;

CREATE TABLE events (
   id              INTEGER PRIMARY KEY,
   time            INTEGER NOT NULL,
   user_id         INTEGER NOT NULL,
   machine_id      INTEGER,
   deployment_id   INTEGER,
   profile_id      INTEGER,
   severity        INTEGER NOT NULL,
   category        VARCHAR (255) NOT NULL,
   action          VARCHAR (255) NOT NULL,
   user_comment    VARCHAR (255)
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE events TO virtfactory;

CREATE TABLE distributions (
   id                  INTEGER PRIMARY KEY,
   kernel              VARCHAR(255) NOT NULL,
   initrd              VARCHAR(255) NOT NULL,
   options             VARCHAR(255),
   kickstart           VARCHAR(255),
   name                VARCHAR(255) UNIQUE,
   architecture        INTEGER NOT NULL,
   kernel_options      VARCHAR(255),       
   kickstart_metadata  VARCHAR(255)   
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE distributions TO virtfactory;

CREATE TABLE profiles (
   id INTEGER PRIMARY KEY,
   name               VARCHAR (255) UNIQUE,
   version            VARCHAR (255) NOT NULL,
   distribution_id    INTEGER NOT NULL,
   virt_storage_size  INTEGER,
   virt_ram           INTEGER,
   kickstart_metadata VARCHAR(255),
   kernel_options     VARCHAR(255),
   valid_targets      INTEGER NOT NULL,
   is_container       INTEGER NOT NULL,
   puppet_classes     TEXT
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE profiles TO virtfactory;

CREATE TABLE deployments (
   id                  INTEGER PRIMARY KEY,
   hostname            VARCHAR(255),
   ip_address          VARCHAR(255),
   registration_token  VARCHAR(255),
   mac_address         VARCHAR(255),
   machine_id          INTEGER NOT NULL,
   profile_id          INTEGER NOT NULL,
   state               INTEGER NOT NULL,
   display_name        VARCHAR(255) NOT NULL,
   puppet_node_diff    TEXT,
   netboot_enabled     INTEGER,
   is_locked           INTEGER
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE deployments TO virtfactory;

CREATE TABLE machines (
   id                 INTEGER PRIMARY KEY,
   hostname           VARCHAR(255),
   ip_address         VARCHAR(255),
   registration_token VARCHAR(255),
   architecture       INTEGER,
   processor_speed    INTEGER,
   processor_count    INTEGER,
   memory             INTEGER,
   kernel_options     VARCHAR(255),
   kickstart_metadata VARCHAR(255),
   list_group         VARCHAR(255),
   mac_address        VARCHAR(255),
   is_container       INTEGER,
   profile_id         INTEGER NOT NULL,
   puppet_node_diff   TEXT,
   netboot_enabled    INTEGER,
   is_locked          INTEGER
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE machines TO virtfactory;

CREATE TABLE regtokens (
   id                 INTEGER PRIMARY KEY,
   token              VARCHAR(255),
   profile_id         INTEGER, 
   uses_remaining     INTEGER
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE regtokens TO virtfactory;

CREATE TABLE sessions (
   session_token      VARCHAR(255) UNIQUE NOT NULL,
   user_id	      INTEGER NOT NULL,
   session_timestamp  REAL NOT NULL
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE sessions TO virtfactory;
   
CREATE TABLE schema_versions (
  id                  INTEGER PRIMARY KEY,
  version             INTEGER,
  git_tag             VARCHAR(100),
  install_timestamp   REAL NOT NULL,
  status              VARCHAR(20) NOT NULL,
  notes               VARCHAR(4000)
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE schema_versions TO virtfactory;

create table upgrade_log_messages (
  id   	              INTEGER PRIMARY KEY,
  action              VARCHAR(50),
  message_type	      VARCHAR(50), --info, warning, error
  message_timestamp   REAL NOT NULL,
  message	      VARCHAR(4000)
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE upgrade_log_messages TO virtfactory;

