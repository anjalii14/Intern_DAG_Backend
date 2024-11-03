# Intern_DAG_Backend

## Overview

This project implements a **Directed Acyclic Graph (DAG)**-based system where nodes and edges represent data flow between entities. The system provides APIs to create, configure, and execute graphs, with features such as topological sorting, data overwrite handling, and cycle detection. The backend is powered by FastAPI and MongoDB.

This README provides instructions to clone, set up, and run the project locally, along with the tech stack used, and a script to populate the backend with some test graphs.

## Tech Stack

The backend is built using the following technologies:

1. **Python**: Core programming language used for implementing business logic and algorithms.
2. **FastAPI**: A modern web framework for building APIs with Python.
3. **Pydantic**: Used for data validation and schema enforcement.
4. **MongoDB**: NoSQL database used for storing graphs, nodes, and edges.
5. **Docker**: Used for containerizing the application to ensure consistency across environments.

## Getting Started

### Prerequisites

Ensure you have the following tools installed:

- **Python 3.8+**
- **Docker** (optional but recommended)
- **MongoDB** (optional or use MongoDB atlas)

### Cloning the Repository

```bash
git clone https://github.com/anjalii14/Intern_DAG_Backend.git
cd Intern_DAG_Backend
```

### Setting up the Backend

#### 1. Install Dependencies
You can either use a Python virtual environment or Docker for managing dependencies.

##### Option:1 Using python virtual environment
```bash
python3 -m venv env
source env/bin/activate  # For Linux/macOS
# For Windows, use 'env\Scripts\activate'

pip install -r requirements.txt
```
###### Environment Variables
Create a .env file in the root directory to configure environment variables. Store your mongodb uri from mongodb atlas or mongodb app.
Note: It should as same level as src.

###### Running the Application
Once the dependencies are installed and the environment variables are set up, you can run the FastAPI server.
```bash
uvicorn src.main:app --reload
```
The server will be accessible at http://localhost:8000.

#### Option 2: Using Docker
If you prefer Docker, you can build and run the backend using the provided Dockerfile.

```bash
docker build -t "your docker project name in lowercase" .
```
Put the MongoDB URI while running the build image of docker.

```
docker run -p 8000:8000 -e MONGO_URI="" "your docker project name in lowercase"
```
The server will be accessible at http://localhost:8000.

### Swagger API Documentation
FastAPI provides built-in interactive API documentation using Swagger. You can access it by navigating to the /docs endpoint in your browser: http://localhost:8000/docs
This interactive documentation allows you to explore the available API routes, send test requests, and view the expected request and response formats.






