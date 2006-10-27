CREATE TABLE users (
   id INTEGER PRIMARY KEY,
   username VARCHAR (255) NOT NULL,
   first VARCHAR (255) NOT NULL,
   middle VARCHAR (255),
   last VARCHAR (255) NOT NULL,
   description VARCHAR (255),
   email VARCHAR (255) NOT NULL,
   role_id INT,
   auth_how VARCHAR (255) NOT NULL
);

CREATE TABLE roles (
   id INTEGER PRIMARY KEY,
   rolename VARCHAR (255),
   description TEXT
);

CREATE TABLE features (
   id INTEGEGER PRIMARY KEY,
   description VARCHAR (255)
);

CREATE TABLE permissions (
   id INTEGER PRIMARY KEY,
   role_id INT,
   feature_id INT,
   parameters VARCHAR (255)
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
   filename   VARCHAR (255)
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
   time VARCHAR(255)
);

CREATE TABLE image_configuration_values (
   id INTEGER PRIMARY KEY,
   image_id INT,
   field VARCHAR(255),
   value VARCHAR(255)
);

CREATE TABLE deployment_configuration_values (
   id INTEGER PRIMARY_KEY,
   deployment_id INT,
   field VARCHAR(255),
   value VARCHAR(255)
);

CREATE TABLE machine_configuration_values (
   id INTEGER PRIMARY_KEY,
   machine_id INT,
   field VARCHAR(255),
   value VARCHAR(255)
);

CREATE TABLE image_types (
   id INTEGER PRIMARY KEY,
   image_id INT,
   field VARCHAR(255),
   datatype INT,
   display_hint INT,
   lower_bound VARCHAR(255),
   upper_bound VARCHAR(255),
   step VARCHAR(255)
);

CREATE TABLE deployment_types (
   id INTEGER PRIMARY KEY,
   deployment_id INT,
   field VARCHAR(255),
   datatype INT,
   display_hint INT,
   lower_bound VARCHAR(255),
   upper_bound VARCHAR(255),
   step VARCHAR(255)
);

CREATE TABLE machine_types (
   id INTEGER PRIMARY KEY,
   machine_id INT,
   field VARCHAR(255),
   datatype INT,
   display_hint INT,
   lower_bound VARCHAR(255),
   upper_bound VARCHAR(255),
   step VARCHAR(255)
);

