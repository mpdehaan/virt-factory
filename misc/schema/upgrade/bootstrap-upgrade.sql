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
  id                  INTEGER PRIMARY KEY,
  action              VARCHAR(50),
  message_type        VARCHAR(50), --info, warning, error
  message_timestamp   REAL NOT NULL,
  message             VARCHAR(4000)
);

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE upgrade_log_messages TO virtfactory;

