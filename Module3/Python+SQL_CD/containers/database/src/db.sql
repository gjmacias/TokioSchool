CREATE DATABASE IF NOT EXISTS movies;

USE movies;

CREATE TABLE IF NOT EXISTS movies (
    name VARCHAR(255) UNIQUE,
    rating DOUBLE
);

INSERT IGNORE INTO movies (name, rating) VALUES
    ("The Dark Knight", 8.1),
    ("Inception", 5.7),
    ("The Matrix", 9.9),
    ("The Lord of the Rings", 11.0),
    ("Star Wars", 3.4),
    ("Saving Private Ryan", 4.5),
    ("The Green Mile", 10.0),
    ("Gladiator", 1.1),
    ("Logan", 8.5);