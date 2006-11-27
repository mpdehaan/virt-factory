
CREATE TABLE users (
   id INTEGER PRIMARY KEY,
   username VARCHAR (255) UNIQUE,
   password VARCHAR (255) NOT NULL,
   first VARCHAR (255) NOT NULL,
   middle VARCHAR (255),
   last VARCHAR (255) NOT NULL,
   description VARCHAR (255),
   email VARCHAR (255) NOT NULL
);

CREATE TABLE events (
   id INTEGER PRIMARY KEY,
   time           INT,
   user_id        INT,
   machine_id     INT,
   deployment_id  INT,
   image_id       INT,
   severity       INT,
   category       VARCHAR (255),
   action         VARCHAR (255),
   user_comment   VARCHAR (255)
);

CREATE TABLE distribution (
   id INTEGER PRIMARY KEY,
   kernel VARCHAR(255),
   initrd VARCHAR(255),
   options VARCHAR(255),
   kickstart VARCHAR(255),
   name VARCHAR(255)
);

CREATE TABLE images (
   id INTEGER PRIMARY KEY,
   name       VARCHAR (255) UNIQUE,
   version    VARCHAR (255),
   filename   VARCHAR (255),
   specfile   VARCHAR (255),
   distribution_id    INT,
   virt_storage_size  INT,
   virt_ram           INT,
   kickstart_metadata VARCHAR(255)
);

CREATE TABLE deployments (
   id INTEGER PRIMARY KEY,
   machine_id INT,
   image_id   INT,
   state      INT
);

CREATE TABLE machines (
   id INTEGER PRIMARY KEY,
   address VARCHAR(255) UNIQUE,
   architecture INT,
   processor_speed INT,
   processor_count INT,
   memory          INT,
   distribution_id INT,
   kernel_options     VARCHAR(255),
   kickstart_metadata VARCHAR(255),
   list_group         VARCHAR(255)
);

