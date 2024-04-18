CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    nickname VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    UNIQUE KEY nickname (nickname)
);

CREATE TABLE IF NOT EXISTS game_stats (
    user_id INT NOT NULL PRIMARY KEY,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    draws INT DEFAULT 0,
    last_game_session_id INT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS game_sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    player1_id INT,
    player2_id INT,
    player1_move ENUM('rock', 'paper', 'scissors'),
    player2_move ENUM('rock', 'paper', 'scissors'),
    status ENUM('waiting', 'completed', 'timeout') DEFAULT 'waiting',
    FOREIGN KEY (player1_id) REFERENCES users (user_id),
    FOREIGN KEY (player2_id) REFERENCES users (user_id)
);
