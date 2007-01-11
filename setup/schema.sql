CREATE TABLE tasks (
   id INTEGER PRIMARY KEY,
   machine_id INTEGER,
   deployment_id INTEGER,
   user_id INTEGER,
   operation INTEGER NOT NULL,
   parameters VARCHAR,
   state INTEGER NOT NULL,
   time INTEGER NOT NULL
);

CREATE TABLE users (
   id INTEGER PRIMARY KEY,
   username VARCHAR (255) UNIQUE NOT NULL,
   password VARCHAR (255) NOT NULL,
   first VARCHAR (255) NOT NULL,
   middle VARCHAR (255),
   last VARCHAR (255) NOT NULL,
   description VARCHAR (255),
   email VARCHAR (255) NOT NULL
);

CREATE TABLE events (
   id INTEGER PRIMARY KEY,
   time           INT NOT NULL,
   user_id        INT NOT NULL,
   machine_id     INT,
   deployment_id  INT,
   image_id       INT,
   severity       INT NOT NULL,
   category       VARCHAR (255) NOT NULL,
   action         VARCHAR (255) NOT NULL,
   user_comment   VARCHAR (255)
);

CREATE TABLE distributions (
   id INTEGER PRIMARY KEY,
   kernel VARCHAR(255) NOT NULL,
   initrd VARCHAR(255) NOT NULL,
   options VARCHAR(255),
   kickstart VARCHAR(255),
   name VARCHAR(255) UNIQUE,
   architecture INT NOT NULL,
   kernel_options VARCHAR(255),       
   kickstart_metadata VARCHAR(255)   
);

CREATE TABLE images (
   id INTEGER PRIMARY KEY,
   name       VARCHAR (255) UNIQUE,
   version    VARCHAR (255) NOT NULL,
   filename   VARCHAR (255),
   specfile   VARCHAR (255),
   distribution_id    INT NOT NULL,
   virt_storage_size  INT NOT NULL,
   virt_ram           INT NOT NULL,
   kickstart_metadata VARCHAR(255),
   kernel_options VARCHAR(255),
   valid_targets INT NOT NULL,
   is_container INT NOT NULL 
);

CREATE TABLE deployments (
   id INTEGER PRIMARY KEY,
   machine_id    INT NOT NULL,
   image_id      INT NOT NULL,
   state         INT NOT NULL,
   display_name VARCHAR(255) NOT NULL
);

CREATE TABLE machines (
   id INTEGER PRIMARY KEY,
   address VARCHAR(255) UNIQUE NOT NULL,
   architecture INT NOT NULL,
   processor_speed INT NOT NULL,
   processor_count INT NOT NULL,
   memory          INT NOT NULL,
   kernel_options     VARCHAR(255),
   kickstart_metadata VARCHAR(255),
   list_group         VARCHAR(255),
   mac_address VARCHAR(255) NOT NULL,
   is_container INT NOT NULL,
   image_id INT NOT NULL
);

