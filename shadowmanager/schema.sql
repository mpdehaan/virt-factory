CREATE TABLE users (
   id INTEGER PRIMARY KEY,
   username VARCHAR (255) NOT NULL,
   password VARCHAR (255) NOT NULL,
   first VARCHAR (255) NOT NULL,
   middle VARCHAR (255),
   last VARCHAR (255) NOT NULL,
   description VARCHAR (255),
   email VARCHAR (255) NOT NULL
);

CREATE TABLE audits (
   id INTEGER PRIMARY KEY,
   time           VARCHAR (255),
   user_id        INT,
   feature_id     INT,
   action         VARCHAR (255),
   user_comment   VARCHAR (255)
);

CREATE TABLE images (
   id INTEGER PRIMARY KEY,
   name       VARCHAR (255),
   version    VARCHAR (255),
   filename   VARCHAR (255),
   specfile   VARCHAR (255)
);

CREATE TABLE deployments (
   id INTEGER PRIMARY KEY,
   machine_id INT,
   image_id INT
);

CREATE TABLE machines (
   id INTEGER PRIMARY KEY,
   architecture VARCHAR (255),
   processors  VARCHAR (255),
   memory VARCHAR (255)
);

CREATE TABLE events (
   id INTEGER PRIMARY KEY,
   deployment_id INT,
   category VARCHAR (255),
   severity INT,
   time VARCHAR(255)
);

CREATE TABLE metrics (
   id INTEGER PRIMARY KEY,
   deployment_id INT,
   category VARCHAR(255),
   time VARCHAR(255),
   value VARCHAR(255),
   type VARCHAR(255)
);

