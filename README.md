# Avenge-R: Distributed Task Queue

A robust, production-ready distributed task queue built with Python, FastAPI, Redis, and PostgreSQL. Avenge-R is designed to handle background processing, scheduled tasks, and provides a sleek live dashboard for monitoring task status.

## 🚀 Features

* **Distributed Workers:** Horizontally scalable worker processes for asynchronous task execution.
* **Scheduled Tasks:** Schedule tasks to run at a specific time in the future.
* **Dead Letter Queue (DLQ):** Failed tasks are automatically moved to a DLQ for inspection.
* **Atomic Operations:** Uses Redis Lua scripts to ensure safe, race-condition-free task promotion.
* **Secure by Default:** Built-in Nginx proxy with auto-generated SSL/TLS certificates and API key authentication.
* **Live Dashboard:** Real-time visibility into task queues, worker status, and processed metrics.

## 🛠️ Technology Stack

* **Backend:** Python, FastAPI
* **Task Broker:** Redis (with Lua scripting)
* **Persistent Storage:** PostgreSQL
* **Reverse Proxy:** Nginx (Alpine)
* **Deployment:** Docker & Docker Compose

## 🚦 Getting Started

### Prerequisites
* Docker and Docker Compose installed on your machine.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Avenge-R.git
   cd Avenge-R
   ```

2. **Configure Environment Variables:**
   Copy the example environment file and update it with your own secure values (the default values are fine for local development).
   ```bash
   cp .env.example .env
   ```

3. **Start the System:**
   Use Docker Compose to build and start all services (API, Worker, Scheduler, Postgres, Redis, and Nginx Proxy).
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Dashboard:**
   Navigate to `https://localhost` in your web browser. 
   *(Note: Because the SSL certificate is self-signed for local development, your browser will show a warning. You can safely bypass this for local testing).*

## 📖 System Architecture

* `api`: The FastAPI web server that handles incoming requests to enqueue tasks and serves the dashboard.
* `worker`: A background process that constantly listens to the Redis `ready` queue and executes tasks.
* `scheduler`: A background process that monitors the `scheduled` sorted set and atomically promotes tasks to the `ready` queue when they are due.
* `postgres`: Stores permanent records of task outcomes and metrics.
* `redis`: Acts as the blazing-fast, in-memory broker for the `ready`, `scheduled`, and `dlq` queues.
* `proxy`: Nginx reverse proxy that handles SSL termination.
