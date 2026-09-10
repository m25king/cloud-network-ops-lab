CREATE TABLE IF NOT EXISTS assets (
  id INT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  zone VARCHAR(32) NOT NULL
);
INSERT IGNORE INTO assets VALUES
 (1, 'demo-core-1', 'management'),
 (2, 'demo-web-1', 'server'),
 (3, 'demo-branch-1', 'branch');
