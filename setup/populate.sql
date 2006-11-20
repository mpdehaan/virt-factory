INSERT INTO users VALUES(200, "admin", "fedora", "first", "middle", "last", "something", "guest@redhat.com");

INSERT INTO images VALUES(100, "image-foo", "1.00", "", "/tmp/foo.spec");
INSERT INTO images VALUES(101, "image-bar", "1.00", "", "/tmp/foo.spec");

INSERT INTO machines VALUES(200, "127.0.0.1", 1, 2000, 1, 1024);
INSERT INTO machines VALUES(201, "127.0.0.2", 2, 3000, 2, 2048);

INSERT INTO deployments VALUES(300, 100, 200, 1);
INSERT INTO deployments VALUES(301, 101, 201, 2);

