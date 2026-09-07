# Smart Building Management System

A full-featured IoT platform for monitoring and managing smart buildings with LoRaWAN sensors, real-time dashboards, and automated alerting.

## Features
- Real-time sensor monitoring with interactive floor maps
- LoRaWAN integration via The Things Network (TTN)
- ThingsBoard cloud sync (optional)
- Multi-tenant client portal with role-based access
- Automated alarm system with email notifications
- Device telemetry history with interactive charts
- CSV data export for analytics
- Bulk device provisioning via CSV upload
- Offline device watchdog (24h inactivity detection)
- Progressive Web App (PWA) — installable on mobile
- Firmware template generator for adding new sensors
- Real-time WebSocket toast notifications
- Contextual help system and guided onboarding tour
- Global spotlight search (Ctrl+K)

## Architecture
The platform is built on a FastAPI backend, utilizing a SQLite database for persistent storage. The API is structured via multiple routers including `api.py` (REST endpoints), `pages.py` (HTML views), `auth.py` (authentication), `ws.py` (WebSockets via `ws_manager.py`), and `webhooks.py` (for handling TTN data). Static files, including uploaded assets, themes, and client-side scripts, are served from the `uploads/` directory.

## Prerequisites
- Python 3.8+
- pip

## Installation
### Windows
.\install.ps1 then .\run.bat
### Linux
sudo ./install.sh then ./run.sh

## Configuration
Copy .env.example to .env and fill in your credentials.
- `TTN_BASE_URL`, `TTN_APP_ID`, `TTN_API_KEY`: Integrates the system with The Things Network.
- `SMTP_SERVER`, `SMTP_PORT`, `ALERT_EMAIL_FROM`: Configures email notifications.
- `ADMIN_PASSWORD`: Default password for the admin account.

## Usage
### Admin Portal (/admin)
Log in to the Admin Portal to manage the building hierarchy (Sites, Buildings, Floors, Rooms), configure gateways, set up alarm templates, and manage user roles. From here, admins can provision devices and map them to physical locations on uploaded floorplans.

### Client Portal (/client)
Clients can access a restricted dashboard to view live telemetry, alarms, and history for the specific buildings or sites they have been granted access to.

### Default Credentials
Set in .env file

## Adding a New Sensor
1. Navigate to **Provision Options** -> **Provision Devices**.
2. Select the Floor and Room where the sensor will be installed.
3. Assign a **Sensor Profile** (this tells the system how to decode the sensor's payload).
4. Enter the Device EUI.
5. Upon successful provision via TTN, you can use the **Floor Editor** to place the sensor icon visually on the map.
*(Refer to the included `How_to_Add_a_New_Sensor_Simple_Guide.docx` for more detailed hardware steps).*

## API Documentation
Swagger UI available at /docs

## PWA Installation
The application includes a `manifest.json` and a Service Worker, making it an installable Progressive Web App (PWA). Simply navigate to the site on a mobile browser or Chrome on desktop, and select the option to "Add to Home Screen" or "Install App".

## Project Structure
- `maintestfinal2.py`: Application entry point.
- `routers/`: Contains `api.py`, `pages.py`, `auth.py`, `ws.py`, `webhooks.py`.
- `uploads/`: Stores static assets, custom CSS themes (`bright_theme.css`), client scripts, `manifest.json`, and the `service-worker.js`.
- `README.md`: Project documentation.
