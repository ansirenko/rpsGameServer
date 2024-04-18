# Rock-Paper-Scissors Game

This project includes both a server and a client application for playing the "Rock-Paper-Scissors" game.

## Getting Started

To run the game, you need to clone both the server and client repositories and then launch the application using Docker.

### Steps to Launch

1. Clone the server repository:
   ```bash
   git clone https://github.com/ansirenko/rpsGameServer
   ```
2. Clone the client repository:
    ```bash
   git clone https://github.com/ansirenko/rpsGameFront
   ```
3. Navigate to the server directory:
    ```bash
   cd rpsGameServer
   ```
4. Launch the application using Docker Compose:
    ```bash
   docker-compose up
   ```
   
## Game Description
"Rock-Paper-Scissors" is a popular game where each of the three choices beats one of the other choices and loses to the other. The server handles the game logic, while the client application provides the user interface.

## Interface
The client application allows users to select one of the elements and send their choice to the server, where it is matched against another player's choice. The outcome of the match is displayed to each participant.

## Technologies
### This project utilizes the following technologies:

#### Backend: Python, FastAPI, SQLAlchemy, MySQL
#### Frontend: Vue.js
#### Docker for deployment and dependency management.