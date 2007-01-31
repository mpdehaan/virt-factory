CREATE TABLE tasks (
   id              INTEGER PRIMARY KEY,
   user_id         INTEGER,
   operation       INTEGER NOT NULL,
   parameters      VARCHAR,
   state           INTEGER NOT NULL,
   time            REAL NOT NULL
);

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

CREATE TABLE events (
   id              INTEGER PRIMARY KEY,
   time            INTEGER NOT NULL,
   user_id         INTEGER NOT NULL,
   machine_id      INTEGER,
   deployment_id   INTEGER,
   image_id        INTEGER,
   severity        INTEGER NOT NULL,
   category        VARCHAR (255) NOT NULL,
   action          VARCHAR (255) NOT NULL,
   user_comment    VARCHAR (255)
);

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

CREATE TABLE images (
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

CREATE TABLE deployments (
   id                 INTEGER PRIMARY KEY,
   machine_id         INTEGER NOT NULL,
   image_id           INTEGER NOT NULL,
   state              INTEGER NOT NULL,
   display_name       VARCHAR(255) NOT NULL,
   puppet_node_diff   TEXT
);

CREATE TABLE machines (
   id                 INTEGER PRIMARY KEY,
   address            VARCHAR(255),
   architecture       INTEGER,
   processor_speed    INTEGER,
   processor_count    INTEGER,
   memory             INTEGER,
   kernel_options     VARCHAR(255),
   kickstart_metadata VARCHAR(255),
   list_group         VARCHAR(255),
   mac_address        VARCHAR(255),
   is_container       INTEGER,
   image_id           INTEGER,
   puppet_node_diff   TEXT
);

CREATE TABLE regtokens (
   id                 INTEGER PRIMARY KEY,
   token              VARCHAR(255),
   image_id           INTEGER, 
   uses_remaining     INTEGER
);

CREATE TABLE sessions (
   session_token      VARCHAR(255) UNIQUE NOT NULL,
   user_id	      INTEGER NOT NULL,
   session_timestamp  REAL NOT NULL
);
   
