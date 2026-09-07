from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from app.main import *

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Building Login</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card {
            width: 480px;
            max-width: calc(100% - 32px);
            background: #111827;
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 20px 70px rgba(0,0,0,0.45);
        }

        .logo {
            width: 60px;
            height: 60px;
            border-radius: 16px;
            background: linear-gradient(135deg, #2563eb, #16a34a);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 18px;
        }

        h1 {
            margin: 0;
            font-size: 28px;
        }

        p {
            margin: 8px 0 24px 0;
            color: #94a3b8;
        }

        a {
            display: block;
            text-decoration: none;
            padding: 18px;
            border-radius: 14px;
            background: #020617;
            border: 1px solid #334155;
            color: white;
            margin-top: 14px;
        }

        a:hover {
            background: #1e293b;
            border-color: #60a5fa;
        }

        strong {
            display: block;
            font-size: 18px;
            margin-bottom: 6px;
        }

        span {
            color: #94a3b8;
            font-size: 14px;
        }

        .footer {
            margin-top: 20px;
            color: #64748b;
            font-size: 12px;
            text-align: center;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
<div class="card">
    <div class="logo">SB</div>

    <h1>Smart Building Login</h1>
    <p>Select which portal you want to access.</p>

    <a href="/admin-login">
        <strong>Admin Portal</strong>
        <span>Manage clients, devices, gateways, alarms, reports, exports, and permissions.</span>
    </a>

    <a href="/client-login">
        <strong>Client Portal</strong>
        <span>View assigned buildings, floors, devices, alarms, activity logs, and reports.</span>
    </a>

    <div class="footer">
        LoRa Smart Building Management System
    </div>
</div>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/bulk_import.js"></script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """
    return HTMLResponse(html)

@router.get("/admin-login", response_class=HTMLResponse)
def admin_login_page():
    return render_role_login_page(
        login_type="admin",
        title="Admin Login",
        subtitle="Administrator access for managing clients, devices, gateways, alarms, reports, and permissions.",
        badge="ADMIN PORTAL",
        accent="linear-gradient(135deg, #2563eb, #7c3aed)"
    )

@router.get("/client-login", response_class=HTMLResponse)
def client_login_page():
    return render_role_login_page(
        login_type="client",
        title="Client Login",
        subtitle="Client access for viewing assigned buildings, floors, devices, alarms, activity, and reports.",
        badge="CLIENT PORTAL",
        accent="linear-gradient(135deg, #16a34a, #0f766e)"
    )

@router.get("/gateway-monitor", response_class=HTMLResponse)
def gateway_monitor_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Gateway Monitor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        .header {
            padding: 20px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 28px;
        }

        .header p {
            margin: 6px 0 0;
            color: #94a3b8;
        }

        .filters {
            margin-top: 18px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .filters label {
            color: #e5e7eb;
            font-weight: bold;
        }

        .filters select {
            background: #1e293b;
            color: white;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 15px;
        }

        .container {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }

        .card {
            background: #1e293b;
            border-radius: 14px;
            padding: 22px;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }

        .card.online {
            border-left: 6px solid #22c55e;
        }

        .card.offline {
            border-left: 6px solid #ef4444;
        }

        .card.error {
            border-left: 6px solid #f97316;
        }

        .card.unknown {
            border-left: 6px solid #94a3b8;
        }

        .top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
        }

        .gateway-name {
            font-size: 22px;
            font-weight: bold;
        }

        .status {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .status.online {
            background: #14532d;
            color: #86efac;
        }

        .status.offline {
            background: #7f1d1d;
            color: #fecaca;
        }

        .status.error {
            background: #7c2d12;
            color: #fed7aa;
        }

        .status.unknown {
            background: #334155;
            color: #e2e8f0;
        }

        .info {
            margin-top: 18px;
            display: grid;
            gap: 10px;
        }

        .row {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
        }

        .label {
            color: #94a3b8;
        }

        .value {
            color: #e5e7eb;
            text-align: right;
            word-break: break-word;
        }

        .loading {
            padding: 30px;
            color: #94a3b8;
        }

        .error-box {
            padding: 30px;
            color: #fecaca;
        }
        .admin-home-btn {
            display: inline-block;
            background: #334155;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
        }

.admin-home-btn:hover {
    background: #475569;
}
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

    <div class="header">
        <h1>Gateway Monitor</h1>
        <p>Live TTN gateway health, uplinks, downlinks, protocol, IP, and last-seen status.</p>

        <div class="filters">
            <button class="admin-home-btn" onclick="window.location.href='/admin'">
                ← Admin Home
            </button>

            <label>Select Site:</label>
            <select id="siteSelect">
                <option value="">All Sites</option>
            </select>
        </div>
    </div>

    <div id="content" class="loading">
        Loading gateways...
    </div>

    <script>
        async function loadSites() {
            const siteSelect = document.getElementById("siteSelect");

            try {
                const res = await fetch("/sites");

                if (!res.ok) {
                    throw new Error("Failed to load sites");
                }

                const sites = await res.json();

                sites.forEach(site => {
                    const option = document.createElement("option");
                    option.value = site.id;
                    option.textContent = site.name;
                    siteSelect.appendChild(option);
                });

            } catch (err) {
                console.error("Failed to load sites:", err);
            }
        }

        async function loadGateways() {
            const content = document.getElementById("content");
            const siteSelect = document.getElementById("siteSelect");
            const siteId = siteSelect.value;

            const apiUrl = siteId
                ? `/gateways/health?site_id=${siteId}`
                : "/gateways/health";

            try {
                const res = await fetch(apiUrl);

                if (!res.ok) {
                    throw new Error("Failed to load gateway health");
                }

                const gateways = await res.json();

                if (!gateways.length) {
                    content.className = "loading";
                    content.innerHTML = "No gateways found for this site.";
                    return;
                }

                content.className = "container";
                content.innerHTML = "";

                gateways.forEach(gw => {
                    const status = gw.connection_status || "unknown";

                    const card = document.createElement("div");
                    card.className = "card " + status;

                    card.innerHTML = `
                        <div class="top-row">
                            <div class="gateway-name">${gw.name}</div>
                            <div class="status ${status}">${status}</div>
                        </div>

                        <div class="info">
                            <div class="row">
                                <span class="label">Gateway ID</span>
                                <span class="value">${gw.gateway_id}</span>
                            </div>

                            <div class="row">
                                <span class="label">Protocol</span>
                                <span class="value">${gw.protocol || "--"}</span>
                            </div>

                            <div class="row">
                                <span class="label">IP Address</span>
                                <span class="value">${gw.ip || "--"}</span>
                            </div>

                            <div class="row">
                                <span class="label">Uplink Count</span>
                                <span class="value">${gw.uplink_count || 0}</span>
                            </div>

                            <div class="row">
                                <span class="label">Downlink Count</span>
                                <span class="value">${gw.downlink_count || 0}</span>
                            </div>

                            <div class="row">
                                <span class="label">Last Seen</span>
                                <span class="value">${gw.last_seen || "--"}</span>
                            </div>

                            <div class="row">
                                <span class="label">Last Status</span>
                                <span class="value">${gw.last_status_received_at || "--"}</span>
                            </div>

                            <div class="row">
                                <span class="label">Last Uplink</span>
                                <span class="value">${gw.last_uplink_received_at || "--"}</span>
                            </div>

                            <div class="row">
                                <span class="label">Last Downlink</span>
                                <span class="value">${gw.last_downlink_received_at || "--"}</span>
                            </div>

                            ${
                                gw.error_message
                                ? `
                                    <div class="row">
                                        <span class="label">Error</span>
                                        <span class="value">${gw.error_message}</span>
                                    </div>
                                  `
                                : ""
                            }
                        </div>
                    `;

                    content.appendChild(card);
                });

            } catch (err) {
                content.className = "error-box";
                content.innerHTML = "Error loading gateway health: " + err.message;
            }
        }

        document.addEventListener("DOMContentLoaded", async () => {
            await loadSites();
            await loadGateways();

            document.getElementById("siteSelect").addEventListener("change", loadGateways);

            setInterval(loadGateways, 5000);
        });
    </script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/admin/gateway-placement", response_class=HTMLResponse)
def gateway_placement_editor():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Gateway Placement Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        .header {
            padding: 22px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
        }

        .header p {
            color: #94a3b8;
            margin: 8px 0 0;
        }

        .toolbar {
            padding: 18px 30px;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, button, input {
            padding: 9px 12px;
            border-radius: 8px;
            border: 1px solid #334155;
            font-size: 14px;
        }

        select, input {
            background: #1e293b;
            color: white;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #1d4ed8;
        }

        .main {
            display: grid;
            grid-template-columns: 1fr 360px;
            gap: 20px;
            padding: 0 30px 30px;
        }

        .map-wrap {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 14px;
            overflow: auto;
        }

        .map {
            position: relative;
            display: inline-block;
            background: #0f172a;
            border-radius: 10px;
            overflow: hidden;
        }

        .map img {
            max-width: 1000px;
            display: block;
        }

        .gateway-marker {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f97316;
            border: 3px solid white;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0,0,0,0.45);
            font-size: 18px;
            z-index: 20;
            user-select: none;
            pointer-events: auto;
        }

        .gateway-marker.online {
            background: #22c55e;
        }

        .gateway-marker.offline {
            background: #ef4444;
        }

        .gateway-marker.error {
            background: #f97316;
        }

        .gateway-marker.unknown {
            background: #64748b;
        }

        .side {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 18px;
        }

        .side h2 {
            margin-top: 0;
        }

        .field {
            margin-bottom: 12px;
        }

        .field label {
            display: block;
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 5px;
        }

        .field input, .field select {
            width: 100%;
            box-sizing: border-box;
        }

        .details {
            margin-top: 18px;
            background: #0f172a;
            border-radius: 10px;
            padding: 12px;
            font-size: 14px;
        }

        .muted {
            color: #94a3b8;
        }

        .status {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status.online {
            background: #14532d;
            color: #86efac;
        }

        .status.offline {
            background: #7f1d1d;
            color: #fecaca;
        }

        .status.error {
            background: #7c2d12;
            color: #fed7aa;
        }

        .status.unknown {
            background: #334155;
            color: #e2e8f0;
        }

        .admin-home-btn {
            display: inline-block;
            background: #334155;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
        }

        .admin-home-btn:hover {
            background: #475569;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Gateway Placement Editor</h1>
    <p>Select a floor, choose a gateway, then click on the floor plan to place it.</p>
</div>

<div class="toolbar">
    <label>Floor:</label>
    <select id="floorSelect"></select>

    <label>Gateway:</label>
    <select id="gatewaySelect"></select>

    <button onclick="loadFloor()">Refresh</button>
    <button class="admin-home-btn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>
</div>

<div class="main">
    <div class="map-wrap">
        <div id="map" class="map">
            <span class="muted">Loading floor...</span>
        </div>
    </div>

    <div class="side">
        <h2>Gateway Info</h2>

        <div class="field">
            <label>Name</label>
            <input id="nameInput">
        </div>

        <div class="field">
            <label>Label</label>
            <input id="labelInput">
        </div>

        <div class="field">
            <label>Location Note</label>
            <input id="noteInput">
        </div>

        <div class="field">
            <label>X</label>
            <input id="xInput" type="number">
        </div>

        <div class="field">
            <label>Y</label>
            <input id="yInput" type="number">
        </div>

        <button onclick="saveSelectedGateway()">Save Gateway Info / Placement</button>

        <div id="gatewayDetails" class="details">
            Select a gateway marker to view details.
        </div>
    </div>
</div>

<script>
let floors = [];
let floorLive = null;
let selectedGateway = null;

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

async function loadFloors() {
    const res = await fetch("/floors");
    floors = await res.json();

    const floorSelect = document.getElementById("floorSelect");
    floorSelect.innerHTML = "";

    floors.forEach(floor => {
        const option = document.createElement("option");
        option.value = floor.id;
        option.textContent = `${floor.name || "Floor"} - ID ${floor.id}`;
        floorSelect.appendChild(option);
    });

        const params = new URLSearchParams(window.location.search);
    const requestedFloorId = params.get("floor_id");

    if (
        requestedFloorId &&
        floors.some(floor => String(floor.id) === String(requestedFloorId))
    ) {
        floorSelect.value = requestedFloorId;
        await loadFloor();
    }

    else if (floors.length > 0) {
        await loadFloor();
    }
}

async function loadFloor() {
    const floorId = document.getElementById("floorSelect").value;

    if (!floorId) return;

    const res = await fetch(`/floors/${floorId}/live`);
    floorLive = await res.json();

    const gatewaySelect = document.getElementById("gatewaySelect");
    gatewaySelect.innerHTML = "";

    floorLive.gateways.forEach(gw => {
        const option = document.createElement("option");
        option.value = gw.id;
        option.textContent = gw.label || gw.name || gw.gateway_id;
        gatewaySelect.appendChild(option);
    });

    drawMap();
}

function drawMap() {
    const map = document.getElementById("map");
    const floor = floorLive.floor;

    map.innerHTML = "";

    const img = document.createElement("img");
    img.src = floor.image_path;
    img.id = "floorImage";

    img.onload = () => {
        drawGateways();
    };

    img.onerror = () => {
        map.innerHTML = `<div style="padding:20px;">Could not load floor image: ${escapeHtml(floor.image_path)}</div>`;
    };

    img.addEventListener("click", async function(e) {
        const gatewayId = document.getElementById("gatewaySelect").value;

        if (!gatewayId) {
            alert("Select a gateway first.");
            return;
        }

        const rect = img.getBoundingClientRect();

        const displayX = e.clientX - rect.left;
        const displayY = e.clientY - rect.top;

        const originalX = Math.round(displayX * floor.image_width / img.clientWidth);
        const originalY = Math.round(displayY * floor.image_height / img.clientHeight);

        document.getElementById("xInput").value = originalX;
        document.getElementById("yInput").value = originalY;

        const gateway = floorLive.gateways.find(g => String(g.id) === String(gatewayId));
        if (gateway) {
            selectedGateway = gateway;
            fillForm(gateway);
        }

        await saveSelectedGateway();
    });

    map.appendChild(img);
}

function drawGateways() {
    const map = document.getElementById("map");
    const img = document.getElementById("floorImage");
    const floor = floorLive.floor;

    floorLive.gateways.forEach(gw => {
        if (gw.x === null || gw.y === null) return;

        const marker = document.createElement("div");
        const status = gw.status || "unknown";

        marker.className = "gateway-marker " + status;
        marker.innerHTML = "📡";
        marker.title = gw.label || gw.name || gw.gateway_id;

        marker.style.left = (gw.x * img.clientWidth / floor.image_width) + "px";
        marker.style.top = (gw.y * img.clientHeight / floor.image_height) + "px";

        let startX = 0;
        let startY = 0;
        let moved = false;
        let dragging = false;

        marker.addEventListener("pointerdown", function(event) {
            event.preventDefault();
            event.stopPropagation();

            startX = event.clientX;
            startY = event.clientY;
            moved = false;
            dragging = true;

            marker.setPointerCapture(event.pointerId);
            marker.style.cursor = "grabbing";

            selectedGateway = gw;
            document.getElementById("gatewaySelect").value = gw.id;
            fillForm(gw);
            showDetails(gw);
        });

        marker.addEventListener("pointermove", function(event) {
            if (!dragging) return;

            const dx = Math.abs(event.clientX - startX);
            const dy = Math.abs(event.clientY - startY);

            if (dx > 3 || dy > 3) {
                moved = true;
            }

            if (!moved) return;

            const rect = img.getBoundingClientRect();

            let displayX = event.clientX - rect.left;
            let displayY = event.clientY - rect.top;

            displayX = Math.max(0, Math.min(displayX, img.clientWidth));
            displayY = Math.max(0, Math.min(displayY, img.clientHeight));

            marker.style.left = displayX + "px";
            marker.style.top = displayY + "px";

            const originalX = Math.round(displayX * floor.image_width / img.clientWidth);
            const originalY = Math.round(displayY * floor.image_height / img.clientHeight);

            document.getElementById("xInput").value = originalX;
            document.getElementById("yInput").value = originalY;
        });

        marker.addEventListener("pointerup", async function(event) {
            event.preventDefault();
            event.stopPropagation();

            dragging = false;
            marker.style.cursor = "grab";

            selectedGateway = gw;
            document.getElementById("gatewaySelect").value = gw.id;

            const latestX = Number(document.getElementById("xInput").value);
            const latestY = Number(document.getElementById("yInput").value);

            gw.x = latestX;
            gw.y = latestY;

            fillForm(gw);
            showDetails(gw);

            if (moved) {
                await saveSelectedGateway();
            }
        });

        marker.addEventListener("pointercancel", function(event) {
            dragging = false;
            marker.style.cursor = "grab";
        });

        map.appendChild(marker);
    });
}

function fillForm(gw) {
    document.getElementById("nameInput").value = gw.name || "";
    document.getElementById("labelInput").value = gw.label || "";
    document.getElementById("noteInput").value = gw.location_note || "";
    document.getElementById("xInput").value = gw.x || "";
    document.getElementById("yInput").value = gw.y || "";
}

function showDetails(gw) {
    const status = gw.status || "unknown";

    document.getElementById("gatewayDetails").innerHTML = `
        <b>${escapeHtml(gw.label || gw.name || gw.gateway_id)}</b><br><br>
        <span class="status ${status}">${status}</span><br><br>

        <span class="muted">Gateway ID:</span><br>
        ${escapeHtml(gw.gateway_id)}<br><br>

        <span class="muted">Last Seen:</span><br>
        ${escapeHtml(gw.last_seen || "--")}<br><br>

        <span class="muted">Position:</span><br>
        X: ${escapeHtml(gw.x)} / Y: ${escapeHtml(gw.y)}<br><br>

        <span class="muted">Note:</span><br>
        ${escapeHtml(gw.location_note || "--")}
    `;
}

async function saveSelectedGateway() {
    const gatewayId = document.getElementById("gatewaySelect").value;

    if (!gatewayId) {
        alert("Select a gateway first.");
        return;
    }

    const payload = {
        name: document.getElementById("nameInput").value,
        label: document.getElementById("labelInput").value,
        location_note: document.getElementById("noteInput").value,
        floor_id: Number(document.getElementById("floorSelect").value),
        x: Number(document.getElementById("xInput").value),
        y: Number(document.getElementById("yInput").value)
    };

    const res = await fetch(`/gateways/${gatewayId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Failed to save gateway");
        return;
    }

    await loadFloor();

    const updated = floorLive.gateways.find(g => String(g.id) === String(gatewayId));
    if (updated) {
        selectedGateway = updated;
        fillForm(updated);
        showDetails(updated);
    }
}

document.getElementById("floorSelect").addEventListener("change", loadFloor);
document.getElementById("gatewaySelect").addEventListener("change", function() {
    const id = this.value;
    const gw = floorLive.gateways.find(g => String(g.id) === String(id));

    if (gw) {
        selectedGateway = gw;
        fillForm(gw);
        showDetails(gw);
    }
});

document.addEventListener("DOMContentLoaded", loadFloors);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/admin/client-access", response_class=HTMLResponse)
def admin_client_access_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Client Access Manager</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
        }

        header {
            padding: 22px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        header h1 {
            margin: 0;
            font-size: 26px;
        }

        header p {
            margin: 8px 0 0;
            color: #94a3b8;
        }

        .container {
            padding: 25px 30px;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
        }

        .card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        }

        h2 {
            margin-top: 0;
            font-size: 20px;
            color: #f8fafc;
        }

        label {
            display: block;
            margin-top: 12px;
            color: #cbd5e1;
            font-size: 14px;
        }

        input, select {
            width: 100%;
            padding: 10px;
            margin-top: 6px;
            border-radius: 8px;
            border: 1px solid #475569;
            background: #020617;
            color: white;
            box-sizing: border-box;
        }

        .checks {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }

        .checks label {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 0;
            background: #020617;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #334155;
        }

        .checks input {
            width: auto;
            margin: 0;
        }

        button {
            margin-top: 14px;
            padding: 10px 14px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            background: #2563eb;
            color: white;
        }

        button:hover {
            opacity: 0.9;
        }

        .danger {
            background: #dc2626;
        }

        .warning {
            background: #f97316;
        }

        .success {
            background: #16a34a;
        }

        .secondary {
            background: #475569;
        }

        .small-btn {
            padding: 7px 10px;
            margin: 3px;
            font-size: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
            font-size: 14px;
        }

        th, td {
            border-bottom: 1px solid #334155;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }

        th {
            color: #93c5fd;
            background: #020617;
        }

        .muted {
            color: #94a3b8;
            font-size: 13px;
        }

        .notice {
            margin-top: 10px;
            padding: 10px;
            border-radius: 8px;
            background: #020617;
            border: 1px solid #334155;
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.5;
        }

        .enabled {
            color: #22c55e;
            font-weight: bold;
        }

        .disabled {
            color: #ef4444;
            font-weight: bold;
        }

        .back {
            display: inline-block;
            margin-bottom: 16px;
            color: #93c5fd;
            text-decoration: none;
        }

        .full {
            margin-top: 22px;
        }

        @media(max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
<header>
    <h1>Client Access Manager</h1>
    <p>Create client users, set login credentials, and control what client/site/building/floor they can view.</p>
</header>

<div class="container">
    <a class="back" href="/admin">← Back to Admin</a>

    <div class="grid">
        <div class="card">
            <h2>Create Client User</h2>

            <label>Name</label>
            <input id="userName" placeholder="Example: Ahmed Client">

            <label>Login Email</label>
            <input id="userEmail" type="email" placeholder="client@example.com">

            <label>Initial Password</label>
            <input id="userPassword" type="text" placeholder="Minimum 8 characters">

            <button class="success" onclick="generateCreatePassword()">
                Generate Temporary Password
            </button>

            <label>Role</label>
            <select id="userRole">
                <option value="client">client</option>
            </select>

            <button onclick="createUser()">Create Client User + Credentials</button>

            <div class="notice">
                Password is shown only while creating/resetting. The system stores only a secure password hash.
            </div>
        </div>

        <div class="card">
            <h2>Give Access</h2>

            <label>User</label>
            <select id="accessUser"></select>

            <label>Client Scope</label>
            <select id="clientSelect">
                <option value="">No specific client</option>
            </select>

            <label>Site Scope</label>
            <select id="siteSelect">
                <option value="">No specific site</option>
            </select>

            <label>Building Scope</label>
            <select id="buildingSelect">
                <option value="">No specific building</option>
            </select>

            <label>Floor Scope</label>
            <select id="floorSelect">
                <option value="">No specific floor</option>
            </select>

            <label>Access Level</label>
            <select id="accessLevel">
                <option value="viewer">viewer</option>
                <option value="operator">operator</option>
                <option value="admin">admin</option>
            </select>

            <div class="checks">
                <label><input type="checkbox" id="canDevices" checked> Devices</label>
                <label><input type="checkbox" id="canGateways" checked> Gateways</label>
                <label><input type="checkbox" id="canAlarms" checked> Alarms</label>
                <label><input type="checkbox" id="canTelemetry" checked> Telemetry</label>
                <label><input type="checkbox" id="canEmail"> Email Settings</label>
            </div>

            <button id="accessSaveBtn" onclick="saveAccess()">Save Access</button>
            <button class="warning" onclick="clearAccessForm()">Cancel Edit</button>
        </div>

        <div class="card">
            <h2>Client Login Credentials</h2>

            <label>Client User</label>
            <select id="credentialsUser" onchange="fillCredentialsForm()"></select>

            <label>Name</label>
            <input id="credentialsName" placeholder="Client name">

            <label>Login Email</label>
            <input id="credentialsEmail" type="email" placeholder="client@example.com">

            <label>New Password</label>
            <input id="credentialsPassword" type="text" placeholder="Leave empty to keep current password">

            <button class="success" onclick="generateCredentialsPassword()">
                Generate Temporary Password
            </button>

            <label>Status</label>
            <select id="credentialsEnabled">
                <option value="1">Enabled</option>
                <option value="0">Disabled</option>
            </select>

            <button onclick="saveClientCredentials()">Save Credentials</button>

            <div class="notice">
                Admin can reset the password, but old passwords cannot be viewed.
            </div>
        </div>
    </div>

    <div class="card full">
        <h2>Users</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="usersTable"></tbody>
        </table>
    </div>

    <div class="card full">
        <h2>Access Records</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Scope</th>
                    <th>Permissions</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="accessTable"></tbody>
        </table>
    </div>
</div>

<script>
let users = [];
let accessRecords = [];
let editingAccessId = null;
const accessParams = new URLSearchParams(window.location.search);

function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function valueOrNull(id) {
    const value = document.getElementById(id).value;
    return value === "" ? null : Number(value);
}

function checkboxValue(id) {
    return document.getElementById(id).checked ? 1 : 0;
}

async function safeFetchJson(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) return [];
        return await res.json();
    } catch (e) {
        return [];
    }
}

async function loadScopes() {
    const clients = await safeFetchJson("/clients");
    const sites = await safeFetchJson("/sites");
    const buildings = await safeFetchJson("/buildings");
    const floors = await safeFetchJson("/floors");

    fillSelect("clientSelect", clients, "No specific client");
    fillSelect("siteSelect", sites, "No specific site");
    fillSelect("buildingSelect", buildings, "No specific building");
    fillSelect("floorSelect", floors, "No specific floor");
}

function fillSelect(selectId, items, emptyText) {
    const select = document.getElementById(selectId);
    select.innerHTML = `<option value="">${emptyText}</option>`;

    items.forEach(item => {
        const label =
            item.name ||
            item.label ||
            item.room_name ||
            item.floor_number ||
            ("ID " + item.id);

        select.innerHTML += `<option value="${item.id}">${escapeHtml(label)} (ID ${item.id})</option>`;
    });
}

async function loadUsers() {
    users = await safeFetchJson("/users");

    const accessUser = document.getElementById("accessUser");
    accessUser.innerHTML = "";

    const credentialsUser = document.getElementById("credentialsUser");
    credentialsUser.innerHTML = "";

    users.forEach(user => {
        accessUser.innerHTML += `
            <option value="${user.id}">
                ${escapeHtml(user.name)} - ${escapeHtml(user.email)}
            </option>
        `;

        if (user.role === "client") {
            credentialsUser.innerHTML += `
                <option value="${user.id}">
                    ${escapeHtml(user.name)} - ${escapeHtml(user.email)}
                </option>
            `;
        }
    });

    const tbody = document.getElementById("usersTable");
    tbody.innerHTML = "";

    users.forEach(user => {
        const statusClass = user.enabled ? "enabled" : "disabled";
        const statusText = user.enabled ? "Enabled" : "Disabled";

        tbody.innerHTML += `
            <tr>
                <td>${user.id}</td>
                <td>
                    <strong>${escapeHtml(user.name)}</strong><br>
                    <span class="muted">${escapeHtml(user.email)}</span><br>
                    <span class="muted">Last login: ${escapeHtml(user.last_login_at || "--")}</span><br>
                    <span class="muted">Password updated: ${escapeHtml(user.password_updated_at || "--")}</span>
                </td>
                <td>${escapeHtml(user.role)}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>${escapeHtml(user.created_at || "--")}</td>
                <td>
                    <button class="small-btn" onclick="window.open('/client-portal?user_id=${user.id}', '_blank')">
                        Open Portal
                    </button>

                    ${user.role === "client" ? `
                        <button class="secondary small-btn" onclick="selectCredentialsUser(${user.id})">
                            Credentials
                        </button>
                    ` : ""}

                    ${user.enabled
                    ? `<button class="warning small-btn" onclick="disableUser(${user.id})">Disable</button>`
                    : `<button class="success small-btn" onclick="enableUser(${user.id})">Enable</button>`
                    }

                    <button class="danger small-btn" onclick="deleteUser(${user.id})">Delete</button>
                </td>
            </tr>
        `;
    });

    fillCredentialsForm();
}

async function loadAccess() {
    accessRecords = await safeFetchJson("/user-access");

    const tbody = document.getElementById("accessTable");
    tbody.innerHTML = "";

    accessRecords.forEach(a => {
        const scope = `
            Client: ${a.client_id || "--"}<br>
            Site: ${a.site_id || "--"}<br>
            Building: ${a.building_id || "--"}<br>
            Floor: ${a.floor_id || "--"}
        `;

        const permissions = `
            Level: <strong>${escapeHtml(a.access_level)}</strong><br>
            Devices: ${a.can_view_devices ? "Yes" : "No"} |
            Gateways: ${a.can_view_gateways ? "Yes" : "No"}<br>
            Alarms: ${a.can_view_alarms ? "Yes" : "No"} |
            Telemetry: ${a.can_view_telemetry ? "Yes" : "No"}<br>
            Email settings: ${a.can_manage_email_settings ? "Yes" : "No"}
        `;

        tbody.innerHTML += `
            <tr>
                <td>${a.id}</td>
                <td>
                    <strong>${escapeHtml(a.user_name || ("User " + a.user_id))}</strong><br>
                    <span class="muted">${escapeHtml(a.user_email || "")}</span>
                </td>
                <td>${scope}</td>
                <td>${permissions}</td>
                <td>${escapeHtml(a.created_at || "--")}</td>
                <td>
                    <button class="small-btn" onclick="editAccess(${a.id})">Edit</button>
                    <button class="danger small-btn" onclick="deleteAccess(${a.id})">Delete Access</button>
                </td>
            </tr>
        `;
    });
}

async function createUser() {
    const name = document.getElementById("userName").value.trim();
    const email = document.getElementById("userEmail").value.trim().toLowerCase();
    const password = document.getElementById("userPassword").value;

    if (!name) {
        alert("Client name is required");
        return;
    }

    if (!email) {
        alert("Client login email is required");
        return;
    }

    if (!password || password.length < 8) {
        alert("Initial password must be at least 8 characters");
        return;
    }

    const body = {
        name: name,
        email: email,
        role: "client",
        enabled: 1
    };

    const res = await fetch("/users", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Failed to create user");
        return;
    }

    const newUserId =
        (data.user && data.user.id) ||
        data.id ||
        data.user_id;

    if (!newUserId) {
        alert("User created, but the response did not include the new user ID. Refreshing page.");
        document.getElementById("userName").value = "";
        document.getElementById("userEmail").value = "";
        document.getElementById("userPassword").value = "";
        await refreshAll();
        return;
    }

    const credentialsRes = await fetch(`/users/${newUserId}/credentials`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: name,
            email: email,
            password: password,
            enabled: true
        })
    });

    const credentialsData = await credentialsRes.json();

    if (!credentialsRes.ok) {
        alert(
            "User was created, but password setup failed: " +
            (credentialsData.detail || "Unknown error")
        );
        await refreshAll();
        return;
    }

    alert(
        "Client user created successfully. Temporary password: " + password +
        "\\nCopy/send it now. It will not be stored as plain text."
    );

    document.getElementById("userName").value = "";
    document.getElementById("userEmail").value = "";
    document.getElementById("userPassword").value = "";

    await refreshAll();
}

function generateRandomPassword(length = 12) {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%";
    let password = "";

    for (let i = 0; i < length; i++) {
        password += chars[Math.floor(Math.random() * chars.length)];
    }

    return password;
}

function generateCreatePassword() {
    const password = generateRandomPassword(12);
    document.getElementById("userPassword").value = password;
}

function generateCredentialsPassword() {
    const password = generateRandomPassword(12);
    document.getElementById("credentialsPassword").value = password;

    alert(
        "Temporary password generated: " + password +
        "\\nCopy/send it now. It will not be stored as plain text."
    );
}

function getUserById(userId) {
    return users.find(user => Number(user.id) === Number(userId));
}

function fillCredentialsForm() {
    const select = document.getElementById("credentialsUser");

    if (!select || !select.value) {
        document.getElementById("credentialsName").value = "";
        document.getElementById("credentialsEmail").value = "";
        document.getElementById("credentialsPassword").value = "";
        document.getElementById("credentialsEnabled").value = "1";
        return;
    }

    const user = getUserById(select.value);

    if (!user) {
        return;
    }

    document.getElementById("credentialsName").value = user.name || "";
    document.getElementById("credentialsEmail").value = user.email || "";
    document.getElementById("credentialsPassword").value = "";
    document.getElementById("credentialsEnabled").value = user.enabled ? "1" : "0";
}

function selectCredentialsUser(userId) {
    const select = document.getElementById("credentialsUser");

    if (!select) {
        return;
    }

    select.value = String(userId);
    fillCredentialsForm();

    document.getElementById("credentialsName").scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}

async function saveClientCredentials() {
    const userId = document.getElementById("credentialsUser").value;

    if (!userId) {
        alert("Select a client user first");
        return;
    }

    const name = document.getElementById("credentialsName").value.trim();
    const email = document.getElementById("credentialsEmail").value.trim().toLowerCase();
    const password = document.getElementById("credentialsPassword").value;
    const enabledValue = document.getElementById("credentialsEnabled").value;

    if (!name) {
        alert("Name is required");
        return;
    }

    if (!email) {
        alert("Email is required");
        return;
    }

    if (password && password.length < 8) {
        alert("Password must be at least 8 characters");
        return;
    }

    const body = {
        name: name,
        email: email,
        enabled: enabledValue === "1"
    };

    if (password) {
        body.password = password;
    }

    const res = await fetch(`/users/${userId}/credentials`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Failed to save credentials");
        return;
    }

    if (password) {
        alert(
            "Credentials updated. New temporary password: " + password +
            "\\nCopy/send it now. It will not be stored as plain text."
        );
    } else {
        alert("Credentials updated.");
    }

    document.getElementById("credentialsPassword").value = "";

    await refreshAll();
}

async function saveAccess() {
    const body = {
        user_id: Number(document.getElementById("accessUser").value),
        client_id: valueOrNull("clientSelect"),
        site_id: valueOrNull("siteSelect"),
        building_id: valueOrNull("buildingSelect"),
        floor_id: valueOrNull("floorSelect"),
        access_level: document.getElementById("accessLevel").value,
        can_view_devices: checkboxValue("canDevices"),
        can_view_gateways: checkboxValue("canGateways"),
        can_view_alarms: checkboxValue("canAlarms"),
        can_view_telemetry: checkboxValue("canTelemetry"),
        can_manage_email_settings: checkboxValue("canEmail")
    };

    let url = "/user-access";
    let method = "POST";

    if (editingAccessId !== null) {
        url = `/user-access/${editingAccessId}`;
        method = "PUT";
        delete body.user_id;
    }

    const res = await fetch(url, {
        method: method,
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok) {
        alert(data.detail || "Failed to save access");
        return;
    }

    clearAccessForm();
    await refreshAll();
}

function editAccess(accessId) {
    const access = accessRecords.find(a => a.id === accessId);

    if (!access) {
        alert("Access record not found");
        return;
    }

    editingAccessId = access.id;

    document.getElementById("accessUser").value = access.user_id;
    document.getElementById("clientSelect").value = access.client_id || "";
    document.getElementById("siteSelect").value = access.site_id || "";
    document.getElementById("buildingSelect").value = access.building_id || "";
    document.getElementById("floorSelect").value = access.floor_id || "";
    document.getElementById("accessLevel").value = access.access_level || "viewer";

    document.getElementById("canDevices").checked = access.can_view_devices === 1;
    document.getElementById("canGateways").checked = access.can_view_gateways === 1;
    document.getElementById("canAlarms").checked = access.can_view_alarms === 1;
    document.getElementById("canTelemetry").checked = access.can_view_telemetry === 1;
    document.getElementById("canEmail").checked = access.can_manage_email_settings === 1;

    document.getElementById("accessSaveBtn").innerText = "Update Access";
    window.scrollTo({top: 0, behavior: "smooth"});
}

function clearAccessForm() {
    editingAccessId = null;

    document.getElementById("accessSaveBtn").innerText = "Save Access";

    document.getElementById("clientSelect").value = "";
    document.getElementById("siteSelect").value = "";
    document.getElementById("buildingSelect").value = "";
    document.getElementById("floorSelect").value = "";

    document.getElementById("accessLevel").value = "viewer";

    document.getElementById("canDevices").checked = true;
    document.getElementById("canGateways").checked = true;
    document.getElementById("canAlarms").checked = true;
    document.getElementById("canTelemetry").checked = true;
    document.getElementById("canEmail").checked = false;
}

async function disableUser(userId) {
    await fetch(`/users/${userId}/disable`, {method: "POST"});
    await refreshAll();
}

async function enableUser(userId) {
    await fetch(`/users/${userId}/enable`, {method: "POST"});
    await refreshAll();
}

async function deleteUser(userId) {
    if (!confirm("Delete this user and all his access records?")) return;

    await fetch(`/users/${userId}`, {method: "DELETE"});
    await refreshAll();
}

async function deleteAccess(accessId) {
    if (!confirm("Delete this access record?")) return;

    await fetch(`/user-access/${accessId}`, {method: "DELETE"});
    await refreshAll();
}

async function refreshAll() {
    await loadUsers();
    await loadAccess();
}

function applyScopeFromUrl() {
    const clientId = accessParams.get("client_id");
    const siteId = accessParams.get("site_id");
    const buildingId = accessParams.get("building_id");
    const floorId = accessParams.get("floor_id");

    if (clientId) {
        document.getElementById("clientSelect").value = clientId;
    }

    if (siteId) {
        document.getElementById("siteSelect").value = siteId;
    }

    if (buildingId) {
        document.getElementById("buildingSelect").value = buildingId;
    }

    if (floorId) {
        document.getElementById("floorSelect").value = floorId;
    }
}
async function init() {
    await loadScopes();
    applyScopeFromUrl();
    await refreshAll();
}

init();
</script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""
    return HTMLResponse(html)

@router.get(
    "/sensor-catalog-manager",
    response_class=HTMLResponse,
)
def sensor_catalog_manager_page():
    """Product-level Admin Portal for physical sensor records."""

    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensor Catalog Manager</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        * { box-sizing: border-box; }
        :root {
            --bg: #08111f;
            --surface: #101b2d;
            --surface-2: #17253b;
            --border: #2a3d58;
            --text: #f8fafc;
            --muted: #94a3b8;
            --primary: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left,
                    rgba(59, 130, 246, 0.14), transparent 32%),
                radial-gradient(circle at top right,
                    rgba(34, 197, 94, 0.10), transparent 30%),
                var(--bg);
        }
        button, input, select, textarea { font: inherit; }
        button { cursor: pointer; }
        .topbar {
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 28px;
            background: rgba(8, 17, 31, 0.94);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(14px);
        }
        .title h1 { margin: 0; font-size: 24px; }
        .title p { margin: 6px 0 0; color: var(--muted); }
        .top-actions { display: flex; gap: 10px; flex-wrap: wrap; }
        .page { max-width: 1420px; margin: 0 auto; padding: 24px; }
        .message {
            display: none;
            margin-bottom: 18px;
            padding: 14px 16px;
            border-radius: 12px;
            white-space: pre-wrap;
        }
        .message.show { display: block; }
        .message.success {
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.45);
        }
        .message.error {
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.45);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }
        .summary-card, .panel {
            background: rgba(16, 27, 45, 0.96);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 16px 45px rgba(0, 0, 0, 0.25);
        }
        .summary-card { padding: 18px; }
        .summary-label { color: var(--muted); font-size: 13px; }
        .summary-value { margin-top: 6px; font-size: 28px; font-weight: 800; }
        .layout {
            display: grid;
            grid-template-columns: minmax(360px, 0.75fr) minmax(560px, 1.45fr);
            gap: 18px;
            align-items: start;
        }
        .panel { padding: 20px; }
        .panel h2 { margin: 0; font-size: 19px; }
        .panel-description { color: var(--muted); margin: 7px 0 18px; }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
        }
        .form-group { display: grid; gap: 7px; }
        .form-group.full { grid-column: 1 / -1; }
        label { font-size: 13px; font-weight: 700; }
        .control {
            width: 100%;
            padding: 11px 12px;
            color: var(--text);
            background: #0b1525;
            border: 1px solid var(--border);
            border-radius: 10px;
            outline: none;
        }
        .control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }
        textarea.control { min-height: 95px; resize: vertical; }
        .help { color: var(--muted); font-size: 12px; }
        .checkbox-row { display: flex; align-items: center; gap: 9px; }
        .actions { display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap; }
        .btn {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            color: var(--text);
            background: var(--surface-2);
            font-weight: 750;
        }
        .btn:hover { filter: brightness(1.08); }
        .btn-primary { background: var(--primary); border-color: var(--primary); }
        .btn-success { background: #16803b; border-color: #16803b; }
        .btn-warning { background: #9a5d08; border-color: #9a5d08; }
        .btn-danger { background: #a52b2b; border-color: #a52b2b; }
        .btn-small { padding: 7px 10px; font-size: 12px; }
        .toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 15px;
        }
        .toolbar .control { max-width: 320px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 850px; }
        th, td {
            padding: 12px 10px;
            border-bottom: 1px solid var(--border);
            text-align: left;
            vertical-align: top;
        }
        th {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        td { font-size: 13px; }
        .code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        .muted { color: var(--muted); }
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 800;
        }
        .badge-enabled { background: rgba(34,197,94,.16); color: #86efac; }
        .badge-disabled { background: rgba(148,163,184,.16); color: #cbd5e1; }
        .badge-used { background: rgba(59,130,246,.16); color: #93c5fd; }
        .row-actions { display: flex; flex-wrap: wrap; gap: 7px; }
        .empty {
            padding: 34px 14px;
            text-align: center;
            color: var(--muted);
        }
        @media (max-width: 1050px) {
            .layout { grid-template-columns: 1fr; }
        }
        @media (max-width: 720px) {
            .topbar { align-items: flex-start; flex-direction: column; padding: 16px; }
            .page { padding: 15px; }
            .summary-grid, .form-grid { grid-template-columns: 1fr; }
            .form-group.full { grid-column: auto; }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>
<body>
    <header class="topbar">
        <div class="title">
            <h1>Sensor Catalog Manager</h1>
            <p>Register physical sensor models supported by your firmware.</p>
        </div>
        <div class="top-actions">
            <button class="btn" style="background:#10b981; border-color:#10b981;" onclick="openFirmwareGenerator()">
                🚀 Generate C++ Firmware
            </button>
            <button class="btn" onclick="location.href='/sensor-profile-manager'">
                Sensor Profiles
            </button>
            <button class="btn" onclick="location.href='/admin'">
                Admin Home
            </button>
        </div>
    </header>

    <main class="page">
        <div id="message" class="message"></div>

        <section class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total sensors</div>
                <div id="totalCount" class="summary-value">0</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Enabled</div>
                <div id="enabledCount" class="summary-value">0</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Used by profiles</div>
                <div id="usedCount" class="summary-value">0</div>
            </div>
        </section>

        <div class="layout">
            <section class="panel">
                <h2 id="formTitle">Add Sensor</h2>
                <p class="panel-description">
                    This registers metadata only. The matching driver must
                    already exist in an uploaded firmware build.
                </p>

                <div class="form-grid">
                    <div class="form-group">
                        <label for="sensorCode">Sensor code *</label>
                        <input id="sensorCode" class="control"
                            placeholder="BME688" maxlength="64">
                        <div class="help">Uppercase letters, numbers and underscores.</div>
                    </div>
                    <div class="form-group">
                        <label for="manufacturer">Manufacturer</label>
                        <input id="manufacturer" class="control"
                            placeholder="Bosch Sensortec" maxlength="120">
                    </div>
                    <div class="form-group">
                        <label for="model">Model *</label>
                        <input id="model" class="control"
                            placeholder="BME688" maxlength="120">
                    </div>
                    <div class="form-group">
                        <label for="useCase">Use case *</label>
                        <input id="useCase" class="control"
                            placeholder="environment" maxlength="64">
                    </div>
                    <div class="form-group">
                        <label for="protocol">Protocol *</label>
                        <input id="protocol" class="control"
                            placeholder="i2c" maxlength="64">
                    </div>
                    <div class="form-group">
                        <label for="defaultBus">Default bus</label>
                        <input id="defaultBus" class="control"
                            placeholder="I2C" maxlength="64">
                    </div>
                    <div class="form-group">
                        <label for="defaultAddress">Default address</label>
                        <input id="defaultAddress" class="control"
                            placeholder="0x77" maxlength="64">
                    </div>
                    <div class="form-group">
                        <label for="datasheetUrl">Datasheet URL</label>
                        <input id="datasheetUrl" class="control"
                            placeholder="https://...">
                    </div>
                    <div class="form-group full">
                        <label for="description">Description</label>
                        <textarea id="description" class="control"
                            placeholder="Describe measurements and intended use."></textarea>
                    </div>
                    <div class="form-group full">
                        <label class="checkbox-row">
                            <input id="enabled" type="checkbox" checked>
                            Enabled and selectable in profile creation
                        </label>
                    </div>
                </div>

                <div class="actions">
                    <button id="saveButton" class="btn btn-primary"
                        onclick="saveSensor()">Create sensor</button>
                    <button class="btn" onclick="resetForm()">Clear</button>
                </div>
            </section>

            <section class="panel">
                <div class="toolbar">
                    <div>
                        <h2>Registered Sensors</h2>
                        <div class="panel-description" style="margin-bottom:0;">
                            Sensors used by profiles cannot be deleted.
                        </div>
                    </div>
                    <input id="searchInput" class="control"
                        placeholder="Search sensors..." oninput="renderTable()">
                </div>

                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Sensor</th>
                                <th>Use case</th>
                                <th>Connection</th>
                                <th>Status</th>
                                <th>Profiles</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="sensorRows"></tbody>
                    </table>
                </div>
                <div id="emptyState" class="empty" style="display:none;">
                    No sensor records match the current search.
                </div>
            </section>
        </div>
    </main>

    <script>
        const state = {
            sensors: [],
            editingId: null
        };

        async function fetchJson(url, options = {}) {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },
                ...options
            });

            let payload = null;
            try {
                payload = await response.json();
            } catch (error) {
                payload = { detail: "Invalid server response" };
            }

            if (!response.ok) {
                const detail = payload.detail;
                throw new Error(
                    typeof detail === "string"
                    ? detail
                    : JSON.stringify(detail || payload)
                );
            }

            return payload;
        }

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function showMessage(message, type = "success") {
            const element = document.getElementById("message");
            element.textContent = message;
            element.className = `message ${type} show`;
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        function clearMessage() {
            const element = document.getElementById("message");
            element.textContent = "";
            element.className = "message";
        }

        function collectDefinition() {
            return {
                sensor_code: document.getElementById("sensorCode")
                    .value.trim().toUpperCase(),
                manufacturer: document.getElementById("manufacturer")
                    .value.trim() || null,
                model: document.getElementById("model").value.trim(),
                use_case: document.getElementById("useCase")
                    .value.trim().toLowerCase(),
                protocol: document.getElementById("protocol")
                    .value.trim().toLowerCase(),
                default_bus: document.getElementById("defaultBus")
                    .value.trim() || null,
                default_address: document.getElementById("defaultAddress")
                    .value.trim() || null,
                datasheet_url: document.getElementById("datasheetUrl")
                    .value.trim() || null,
                description: document.getElementById("description")
                    .value.trim() || null,
                enabled: document.getElementById("enabled").checked
            };
        }

        function resetForm() {
            state.editingId = null;
            document.getElementById("formTitle").textContent = "Add Sensor";
            document.getElementById("saveButton").textContent = "Create sensor";
            document.getElementById("sensorCode").value = "";
            document.getElementById("manufacturer").value = "";
            document.getElementById("model").value = "";
            document.getElementById("useCase").value = "environment";
            document.getElementById("protocol").value = "i2c";
            document.getElementById("defaultBus").value = "I2C";
            document.getElementById("defaultAddress").value = "";
            document.getElementById("datasheetUrl").value = "";
            document.getElementById("description").value = "";
            document.getElementById("enabled").checked = true;
            clearMessage();
        }

        function editSensor(sensorId) {
            const sensor = state.sensors.find(item => item.id === sensorId);
            if (!sensor) return;

            state.editingId = sensorId;
            document.getElementById("formTitle").textContent = "Edit Sensor";
            document.getElementById("saveButton").textContent = "Update sensor";
            document.getElementById("sensorCode").value = sensor.sensor_code || "";
            document.getElementById("manufacturer").value = sensor.manufacturer || "";
            document.getElementById("model").value = sensor.model || "";
            document.getElementById("useCase").value = sensor.use_case || "";
            document.getElementById("protocol").value = sensor.protocol || "";
            document.getElementById("defaultBus").value = sensor.default_bus || "";
            document.getElementById("defaultAddress").value = sensor.default_address || "";
            document.getElementById("datasheetUrl").value = sensor.datasheet_url || "";
            document.getElementById("description").value = sensor.description || "";
            document.getElementById("enabled").checked = Boolean(sensor.enabled);
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        async function saveSensor() {
            const button = document.getElementById("saveButton");
            button.disabled = true;
            button.textContent = "Saving...";

            try {
                const definition = collectDefinition();
                const url = state.editingId
                    ? `/sensor-catalog/${state.editingId}`
                    : "/sensor-catalog";
                const method = state.editingId ? "PUT" : "POST";

                const result = await fetchJson(url, {
                    method,
                    body: JSON.stringify(definition)
                });

                showMessage(result.message, "success");
                resetForm();
                await loadSensors();

            } catch (error) {
                showMessage(error.message, "error");
            } finally {
                button.disabled = false;
                button.textContent = state.editingId
                    ? "Update sensor"
                    : "Create sensor";
            }
        }

        async function toggleSensor(sensorId, enabled) {
            try {
                const action = enabled ? "enable" : "disable";
                const result = await fetchJson(
                    `/sensor-catalog/${sensorId}/${action}`,
                    { method: "POST" }
                );
                showMessage(result.message, "success");
                await loadSensors();
            } catch (error) {
                showMessage(error.message, "error");
            }
        }

        async function deleteSensor(sensorId) {
            const sensor = state.sensors.find(item => item.id === sensorId);
            if (!sensor) return;

            if (!confirm(`Delete ${sensor.sensor_code}?`)) return;

            try {
                const result = await fetchJson(
                    `/sensor-catalog/${sensorId}`,
                    { method: "DELETE" }
                );
                showMessage(result.message, "success");
                if (state.editingId === sensorId) resetForm();
                await loadSensors();
            } catch (error) {
                showMessage(error.message, "error");
            }
        }

        function updateSummary() {
            document.getElementById("totalCount").textContent =
                state.sensors.length;
            document.getElementById("enabledCount").textContent =
                state.sensors.filter(item => item.enabled).length;
            document.getElementById("usedCount").textContent =
                state.sensors.filter(item => Number(item.profile_count) > 0).length;
        }

        function renderTable() {
            const query = document.getElementById("searchInput")
                .value.trim().toLowerCase();

            const sensors = state.sensors.filter(sensor => {
                const text = [
                    sensor.sensor_code,
                    sensor.manufacturer,
                    sensor.model,
                    sensor.use_case,
                    sensor.protocol,
                    sensor.default_address
                ].join(" ").toLowerCase();
                return text.includes(query);
            });

            const tbody = document.getElementById("sensorRows");
            const empty = document.getElementById("emptyState");

            empty.style.display = sensors.length ? "none" : "block";

            tbody.innerHTML = sensors.map(sensor => {
                const used = Number(sensor.profile_count || 0);
                const statusBadge = sensor.enabled
                    ? '<span class="badge badge-enabled">Enabled</span>'
                    : '<span class="badge badge-disabled">Disabled</span>';
                const usageBadge = used
                    ? `<span class="badge badge-used">${used} profile${used === 1 ? "" : "s"}</span>`
                    : '<span class="muted">Unused</span>';

                return `
                    <tr>
                        <td>
                            <strong class="code">${escapeHtml(sensor.sensor_code)}</strong>
                            <div>${escapeHtml(sensor.manufacturer || "")} ${escapeHtml(sensor.model || "")}</div>
                            <div class="muted">${escapeHtml(sensor.description || "")}</div>
                        </td>
                        <td>${escapeHtml(sensor.use_case || "—")}</td>
                        <td>
                            <div>${escapeHtml(sensor.protocol || "—")}</div>
                            <div class="muted">
                                ${escapeHtml(sensor.default_bus || "")}
                                ${escapeHtml(sensor.default_address || "")}
                            </div>
                        </td>
                        <td>${statusBadge}</td>
                        <td>${usageBadge}</td>
                        <td>
                            <div class="row-actions">
                                <button class="btn btn-small"
                                    onclick="editSensor(${sensor.id})">Edit</button>
                                <button class="btn btn-small ${sensor.enabled ? "btn-warning" : "btn-success"}"
                                    onclick="toggleSensor(${sensor.id}, ${sensor.enabled ? "false" : "true"})">
                                    ${sensor.enabled ? "Disable" : "Enable"}
                                </button>
                                <button class="btn btn-small btn-danger"
                                    ${used ? "disabled" : ""}
                                    onclick="deleteSensor(${sensor.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join("");
        }

        async function loadSensors() {
            try {
                const result = await fetchJson(
                    "/sensor-catalog?include_disabled=true"
                );
                state.sensors = result.sensors || [];
                updateSummary();
                renderTable();
            } catch (error) {
                showMessage("Could not load sensors: " + error.message, "error");
            }
        }

        document.addEventListener("DOMContentLoaded", async () => {
            resetForm();
            await loadSensors();
        });
    </script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get(
    "/firmware-module-manager",
    response_class=HTMLResponse,
)
def firmware_module_manager_page():
    """Admin Portal for drivers compiled into LILYGO firmware."""

    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Firmware Module Manager</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        * { box-sizing: border-box; }
        :root {
            --bg: #08111f;
            --surface: #101b2d;
            --surface-2: #17253b;
            --border: #2a3d58;
            --text: #f8fafc;
            --muted: #94a3b8;
            --primary: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left,
                    rgba(59, 130, 246, 0.14), transparent 32%),
                radial-gradient(circle at top right,
                    rgba(139, 92, 246, 0.12), transparent 30%),
                var(--bg);
        }
        button, input, select, textarea { font: inherit; }
        button { cursor: pointer; }
        .topbar {
            position: sticky;
            top: 0;
            z-index: 20;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 28px;
            background: rgba(8, 17, 31, 0.94);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(14px);
        }
        .title h1 { margin: 0; font-size: 24px; }
        .title p { margin: 6px 0 0; color: var(--muted); }
        .top-actions { display: flex; gap: 10px; flex-wrap: wrap; }
        .page { max-width: 1500px; margin: 0 auto; padding: 24px; }
        .notice {
            margin-bottom: 18px;
            padding: 14px 16px;
            border: 1px solid rgba(245, 158, 11, 0.45);
            border-radius: 12px;
            background: rgba(245, 158, 11, 0.10);
            color: #fde68a;
        }
        .message {
            display: none;
            margin-bottom: 18px;
            padding: 14px 16px;
            border-radius: 12px;
            white-space: pre-wrap;
        }
        .message.show { display: block; }
        .message.success {
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.45);
        }
        .message.error {
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.45);
        }
        .layout {
            display: grid;
            grid-template-columns: minmax(370px, 0.85fr) minmax(0, 1.65fr);
            gap: 18px;
            align-items: start;
        }
        .panel {
            background: rgba(16, 27, 45, 0.96);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 16px 45px rgba(0, 0, 0, 0.25);
        }
        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 18px;
            border-bottom: 1px solid var(--border);
        }
        .panel-header h2 { margin: 0; font-size: 18px; }
        .panel-header p { margin: 5px 0 0; color: var(--muted); font-size: 13px; }
        .panel-body { padding: 18px; }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 13px;
        }
        .form-group { display: grid; gap: 6px; }
        .form-group.full { grid-column: 1 / -1; }
        label { color: #dbeafe; font-size: 13px; font-weight: 700; }
        .control {
            width: 100%;
            padding: 10px 11px;
            color: var(--text);
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-radius: 10px;
            outline: none;
        }
        .control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }
        textarea.control { min-height: 92px; resize: vertical; }
        .help { color: var(--muted); font-size: 12px; line-height: 1.45; }
        .checkbox-row { display: flex; align-items: center; gap: 9px; color: var(--text); }
        .actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 16px; }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            padding: 9px 13px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--surface-2);
            color: var(--text);
            text-decoration: none;
            font-weight: 750;
        }
        .btn:hover { filter: brightness(1.12); }
        .btn-primary { background: var(--primary); border-color: var(--primary); }
        .btn-success { background: var(--success); border-color: var(--success); color: #052e16; }
        .btn-warning { background: var(--warning); border-color: var(--warning); color: #422006; }
        .btn-danger { background: var(--danger); border-color: var(--danger); }
        .btn-small { padding: 7px 9px; font-size: 12px; }
        .toolbar {
            display: flex;
            gap: 10px;
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
        }
        .toolbar .control { max-width: 360px; }
        .table-wrap { overflow: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 980px; }
        th, td { padding: 12px 13px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
        th { color: #bfdbfe; background: rgba(23, 37, 59, 0.72); font-size: 12px; position: sticky; top: 0; }
        td { font-size: 13px; }
        .muted { color: var(--muted); }
        .key { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 800; }
        .pill {
            display: inline-flex;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
        }
        .pill.on { background: rgba(34, 197, 94, 0.15); color: #86efac; }
        .pill.off { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }
        .row-actions { display: flex; flex-wrap: wrap; gap: 6px; }
        .empty { padding: 35px; text-align: center; color: var(--muted); }
        @media (max-width: 1050px) {
            .layout { grid-template-columns: 1fr; }
        }
        @media (max-width: 720px) {
            .topbar { align-items: flex-start; flex-direction: column; padding: 16px; }
            .page { padding: 14px; }
            .form-grid { grid-template-columns: 1fr; }
            .form-group.full { grid-column: auto; }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>
<body>
    <header class="topbar">
        <div class="title">
            <h1>Firmware Module Manager</h1>
            <p>Register drivers and libraries already compiled into compatible LILYGO firmware.</p>
        </div>
        <div class="top-actions">
            <a class="btn" href="/sensor-catalog-manager">Sensor Catalog</a>
            <a class="btn" href="/sensor-profile-manager">Sensor Profiles</a>
            <a class="btn" href="/admin">Admin Home</a>
        </div>
    </header>

    <main class="page">
        <div class="notice">
            Registering a module here does not install its Arduino library. Only register a driver after it has been compiled into the selected firmware version.
        </div>
        <div id="message" class="message"></div>

        <div class="layout">
            <section class="panel">
                <div class="panel-header">
                    <div>
                        <h2 id="formTitle">Register firmware module</h2>
                        <p>Describe the driver contract available to sensor profiles.</p>
                    </div>
                </div>
                <div class="panel-body">
                    <div class="form-grid">
                        <div class="form-group full">
                            <label>Module key *</label>
                            <input id="moduleKey" class="control" placeholder="bme688_i2c">
                            <div class="help">Lowercase letters, numbers, and underscores.</div>
                        </div>
                        <div class="form-group full">
                            <label>Display name *</label>
                            <input id="displayName" class="control" placeholder="BME688 I2C Module">
                        </div>
                        <div class="form-group">
                            <label>Driver class *</label>
                            <input id="driverClass" class="control" placeholder="BME688SensorModule">
                        </div>
                        <div class="form-group">
                            <label>Protocol *</label>
                            <input id="protocol" class="control" value="i2c" placeholder="i2c">
                        </div>
                        <div class="form-group">
                            <label>Library name</label>
                            <input id="libraryName" class="control" placeholder="Bosch BME68x Library">
                        </div>
                        <div class="form-group">
                            <label>Library version</label>
                            <input id="libraryVersion" class="control" placeholder="Leave empty when unrestricted">
                        </div>
                        <div class="form-group full">
                            <label>Supported board *</label>
                            <input id="supportedBoard" class="control" value="LILYGO LoRa32">
                        </div>
                        <div class="form-group">
                            <label>Minimum firmware version</label>
                            <input id="minFirmwareVersion" class="control" value="1.0.0" placeholder="1.0.0">
                        </div>
                        <div class="form-group">
                            <label>Source file</label>
                            <input id="sourceFile" class="control" placeholder="BME688SensorModule.cpp">
                        </div>
                        <div class="form-group full">
                            <label>Notes</label>
                            <textarea id="notes" class="control" placeholder="I2C address 0x77; payload encoder bme688_v1."></textarea>
                        </div>
                        <div class="form-group full">
                            <label class="checkbox-row">
                                <input id="enabled" type="checkbox" checked>
                                Available for new sensor profiles
                            </label>
                        </div>
                    </div>
                    <div class="actions">
                        <button id="saveButton" class="btn btn-primary" onclick="saveModule()">Register module</button>
                        <button class="btn" onclick="resetForm()">Clear</button>
                    </div>
                </div>
            </section>

            <section class="panel">
                <div class="panel-header">
                    <div>
                        <h2>Registered firmware modules</h2>
                        <p><span id="moduleCount">0</span> module(s)</p>
                    </div>
                    <button class="btn" onclick="loadModules()">Refresh</button>
                </div>
                <div class="toolbar">
                    <input id="search" class="control" placeholder="Search module, driver, library, or protocol..." oninput="renderModules()">
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Driver / Protocol</th>
                                <th>Library</th>
                                <th>Compatibility</th>
                                <th>Status</th>
                                <th>Profiles</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="moduleRows"></tbody>
                    </table>
                    <div id="emptyState" class="empty" style="display:none;">No firmware modules found.</div>
                </div>
            </section>
        </div>
    </main>

    <script>
        const state = { modules: [], editingId: null };

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function showMessage(message, type = "success") {
            const box = document.getElementById("message");
            box.textContent = message;
            box.className = `message ${type} show`;
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        function clearMessage() {
            const box = document.getElementById("message");
            box.textContent = "";
            box.className = "message";
        }

        async function fetchJson(url, options = {}) {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },
                ...options
            });

            let payload = {};
            try { payload = await response.json(); } catch (_) {}

            if (!response.ok) {
                const detail = payload.detail;
                throw new Error(
                    typeof detail === "string"
                        ? detail
                        : JSON.stringify(detail || payload.message || "Request failed")
                );
            }

            return payload;
        }

        function collectDefinition() {
            return {
                module_key: document.getElementById("moduleKey").value.trim().toLowerCase(),
                display_name: document.getElementById("displayName").value.trim(),
                driver_class: document.getElementById("driverClass").value.trim(),
                protocol: document.getElementById("protocol").value.trim().toLowerCase(),
                library_name: document.getElementById("libraryName").value.trim() || null,
                library_version: document.getElementById("libraryVersion").value.trim() || null,
                supported_board: document.getElementById("supportedBoard").value.trim(),
                min_firmware_version: document.getElementById("minFirmwareVersion").value.trim() || null,
                source_file: document.getElementById("sourceFile").value.trim() || null,
                notes: document.getElementById("notes").value.trim() || null,
                enabled: document.getElementById("enabled").checked
            };
        }

        function resetForm() {
            state.editingId = null;
            document.getElementById("formTitle").textContent = "Register firmware module";
            document.getElementById("saveButton").textContent = "Register module";
            document.getElementById("moduleKey").value = "";
            document.getElementById("displayName").value = "";
            document.getElementById("driverClass").value = "";
            document.getElementById("protocol").value = "i2c";
            document.getElementById("libraryName").value = "";
            document.getElementById("libraryVersion").value = "";
            document.getElementById("supportedBoard").value = "LILYGO LoRa32";
            document.getElementById("minFirmwareVersion").value = "1.0.0";
            document.getElementById("sourceFile").value = "";
            document.getElementById("notes").value = "";
            document.getElementById("enabled").checked = true;
        }

        function editModule(id) {
            const module = state.modules.find(item => item.id === id);
            if (!module) return;

            state.editingId = id;
            document.getElementById("formTitle").textContent = "Edit firmware module";
            document.getElementById("saveButton").textContent = "Update module";
            document.getElementById("moduleKey").value = module.module_key || "";
            document.getElementById("displayName").value = module.display_name || "";
            document.getElementById("driverClass").value = module.driver_class || "";
            document.getElementById("protocol").value = module.protocol || "";
            document.getElementById("libraryName").value = module.library_name || "";
            document.getElementById("libraryVersion").value = module.library_version || "";
            document.getElementById("supportedBoard").value = module.supported_board || "LILYGO LoRa32";
            document.getElementById("minFirmwareVersion").value = module.min_firmware_version || "";
            document.getElementById("sourceFile").value = module.source_file || "";
            document.getElementById("notes").value = module.notes || "";
            document.getElementById("enabled").checked = Boolean(module.enabled);
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        async function saveModule() {
            clearMessage();
            const button = document.getElementById("saveButton");
            button.disabled = true;
            const original = button.textContent;
            button.textContent = "Saving...";

            try {
                const definition = collectDefinition();
                const url = state.editingId
                    ? `/firmware-modules/${state.editingId}`
                    : "/firmware-modules";
                const method = state.editingId ? "PUT" : "POST";

                const result = await fetchJson(url, {
                    method,
                    body: JSON.stringify(definition)
                });

                showMessage(result.message || "Firmware module saved.");
                resetForm();
                await loadModules(false);
            } catch (error) {
                showMessage(error.message, "error");
            } finally {
                button.disabled = false;
                button.textContent = state.editingId ? "Update module" : "Register module";
                if (!button.textContent) button.textContent = original;
            }
        }

        async function changeStatus(id, enabled) {
            try {
                const result = await fetchJson(
                    `/firmware-modules/${id}/${enabled ? "enable" : "disable"}`,
                    { method: "POST", body: "{}" }
                );
                showMessage(result.message || "Status changed.");
                await loadModules(false);
            } catch (error) {
                showMessage(error.message, "error");
            }
        }

        async function deleteModule(id) {
            const module = state.modules.find(item => item.id === id);
            if (!module) return;
            if (!confirm(`Delete firmware module ${module.module_key}?`)) return;

            try {
                const result = await fetchJson(
                    `/firmware-modules/${id}`,
                    { method: "DELETE" }
                );
                showMessage(result.message || "Firmware module deleted.");
                if (state.editingId === id) resetForm();
                await loadModules(false);
            } catch (error) {
                showMessage(error.message, "error");
            }
        }

        function renderModules() {
            const query = document.getElementById("search").value.trim().toLowerCase();
            const rows = document.getElementById("moduleRows");

            const filtered = state.modules.filter(module => {
                const searchable = [
                    module.module_key,
                    module.display_name,
                    module.driver_class,
                    module.protocol,
                    module.library_name,
                    module.supported_board
                ].join(" ").toLowerCase();
                return !query || searchable.includes(query);
            });

            document.getElementById("moduleCount").textContent = state.modules.length;
            document.getElementById("emptyState").style.display = filtered.length ? "none" : "block";

            rows.innerHTML = filtered.map(module => `
                <tr>
                    <td>
                        <div class="key">${escapeHtml(module.module_key)}</div>
                        <div class="muted">${escapeHtml(module.display_name)}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(module.driver_class)}</div>
                        <div class="muted">${escapeHtml(module.protocol)}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(module.library_name || "—")}</div>
                        <div class="muted">${escapeHtml(module.library_version || "Unrestricted version")}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(module.supported_board || "—")}</div>
                        <div class="muted">Min firmware: ${escapeHtml(module.min_firmware_version || "—")}</div>
                    </td>
                    <td>
                        <span class="pill ${module.enabled ? "on" : "off"}">
                            ${module.enabled ? "Enabled" : "Disabled"}
                        </span>
                    </td>
                    <td>${Number(module.profile_count || 0)}</td>
                    <td>
                        <div class="row-actions">
                            <button class="btn btn-small" onclick="editModule(${module.id})">Edit</button>
                            <button class="btn btn-small ${module.enabled ? "btn-warning" : "btn-success"}"
                                onclick="changeStatus(${module.id}, ${module.enabled ? "false" : "true"})">
                                ${module.enabled ? "Disable" : "Enable"}
                            </button>
                            <button class="btn btn-small btn-danger"
                                ${module.can_delete ? "" : "disabled title='Used by a profile'"}
                                onclick="deleteModule(${module.id})">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join("");
        }

        async function loadModules(showErrors = true) {
            try {
                const result = await fetchJson("/firmware-modules?include_disabled=true");
                state.modules = result.modules || [];
                renderModules();
            } catch (error) {
                if (showErrors) showMessage(error.message, "error");
            }
        }

        document.addEventListener("DOMContentLoaded", () => {
            resetForm();
            loadModules();
        });
    </script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get(
    "/sensor-profile-manager",
    response_class=HTMLResponse,
)
def sensor_profile_manager_page():
    """
    Visual administrator interface for viewing and managing
    sensor profiles.
    """

    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Sensor Profile Manager</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        * {
            box-sizing: border-box;
        }

        :root {
            --background: #08111f;
            --surface: #101b2d;
            --surface-light: #17253b;
            --surface-hover: #1d2d46;
            --border: #2a3d58;
            --text: #f8fafc;
            --muted: #94a3b8;
            --primary: #3b82f6;
            --primary-dark: #2563eb;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --purple: #8b5cf6;
            --shadow: 0 18px 45px rgba(0, 0, 0, 0.32);
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
            background:
                radial-gradient(
                    circle at top left,
                    rgba(59, 130, 246, 0.13),
                    transparent 34%
                ),
                radial-gradient(
                    circle at top right,
                    rgba(139, 92, 246, 0.12),
                    transparent 30%
                ),
                var(--background);
            color: var(--text);
        }

        button,
        input,
        select {
            font: inherit;
        }

        button {
            cursor: pointer;
        }

        .topbar {
            position: sticky;
            top: 0;
            z-index: 40;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 18px 28px;
            background: rgba(8, 17, 31, 0.92);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(14px);
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo {
            width: 46px;
            height: 46px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            background:
                linear-gradient(
                    135deg,
                    var(--primary),
                    var(--purple)
                );
            font-size: 23px;
            box-shadow:
                0 10px 30px rgba(59, 130, 246, 0.28);
        }

        .title-block h1 {
            margin: 0;
            font-size: 22px;
        }

        .title-block p {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 13px;
        }

        .topbar-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .btn {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            background: var(--surface-light);
            color: var(--text);
            font-weight: 650;
            transition:
                transform 0.15s ease,
                background 0.15s ease,
                border-color 0.15s ease;
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-1px);
            background: var(--surface-hover);
            border-color: #46617f;
        }

        .btn:disabled {
            opacity: 0.43;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--primary);
            border-color: var(--primary);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--primary-dark);
        }

        .btn-danger {
            color: #fecaca;
            border-color: rgba(239, 68, 68, 0.46);
            background: rgba(239, 68, 68, 0.10);
        }

        .btn-success {
            color: #bbf7d0;
            border-color: rgba(34, 197, 94, 0.45);
            background: rgba(34, 197, 94, 0.10);
        }

        .page {
            max-width: 1550px;
            margin: 0 auto;
            padding: 26px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns:
                repeat(5, minmax(150px, 1fr));
            gap: 14px;
            margin-bottom: 22px;
        }

        .summary-card {
            position: relative;
            overflow: hidden;
            padding: 18px;
            border: 1px solid var(--border);
            border-radius: 15px;
            background:
                linear-gradient(
                    145deg,
                    rgba(23, 37, 59, 0.94),
                    rgba(12, 25, 43, 0.94)
                );
            box-shadow: var(--shadow);
        }

        .summary-label {
            color: var(--muted);
            font-size: 12px;
            font-weight: 750;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .summary-value {
            margin-top: 10px;
            font-size: 29px;
            font-weight: 800;
        }

        .summary-accent {
            position: absolute;
            width: 60px;
            height: 60px;
            right: -20px;
            bottom: -22px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.18);
        }

        .toolbar {
            display: grid;
            grid-template-columns:
                minmax(220px, 1fr)
                190px
                190px
                auto;
            gap: 12px;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(16, 27, 45, 0.78);
            border: 1px solid var(--border);
            border-radius: 14px;
        }

        .control {
            width: 100%;
            min-height: 42px;
            padding: 10px 12px;
            color: var(--text);
            background: var(--surface-light);
            border: 1px solid var(--border);
            border-radius: 10px;
            outline: none;
        }

        .control:focus {
            border-color: var(--primary);
            box-shadow:
                0 0 0 3px rgba(59, 130, 246, 0.13);
        }

        .content-layout {
            display: grid;
            grid-template-columns:
                minmax(0, 1fr)
                minmax(390px, 510px);
            gap: 18px;
            align-items: start;
        }

        .profile-grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }

        .profile-card {
            position: relative;
            padding: 18px;
            border-radius: 15px;
            border: 1px solid var(--border);
            background:
                linear-gradient(
                    145deg,
                    rgba(23, 37, 59, 0.92),
                    rgba(13, 27, 47, 0.92)
                );
            box-shadow: var(--shadow);
            cursor: pointer;
            transition:
                transform 0.18s ease,
                border-color 0.18s ease;
        }

        .profile-card:hover {
            transform: translateY(-3px);
            border-color: #4b6888;
        }

        .profile-card.selected {
            border-color: var(--primary);
            box-shadow:
                0 0 0 2px rgba(59, 130, 246, 0.17),
                var(--shadow);
        }

        .profile-card.disabled {
            opacity: 0.62;
        }

        .profile-heading {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }

        .profile-icon {
            width: 45px;
            height: 45px;
            display: grid;
            place-items: center;
            flex: 0 0 auto;
            border-radius: 13px;
            background: rgba(59, 130, 246, 0.14);
            border: 1px solid rgba(59, 130, 246, 0.25);
            font-size: 21px;
        }

        .profile-name {
            margin: 0;
            font-size: 16px;
            line-height: 1.3;
        }

        .profile-code {
            margin-top: 5px;
            color: #93c5fd;
            font-family:
                "Cascadia Code",
                Consolas,
                monospace;
            font-size: 11px;
            word-break: break-word;
        }

        .badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 14px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 8px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: rgba(148, 163, 184, 0.08);
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 700;
        }

        .badge-active {
            color: #bbf7d0;
            border-color: rgba(34, 197, 94, 0.35);
            background: rgba(34, 197, 94, 0.11);
        }

        .badge-disabled {
            color: #fecaca;
            border-color: rgba(239, 68, 68, 0.35);
            background: rgba(239, 68, 68, 0.10);
        }

        .badge-system {
            color: #ddd6fe;
            border-color: rgba(139, 92, 246, 0.35);
            background: rgba(139, 92, 246, 0.12);
        }

        .profile-description {
            min-height: 43px;
            margin: 14px 0;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.55;
        }

        .card-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 7px;
            padding-top: 13px;
            border-top: 1px solid var(--border);
        }

        .mini-stat {
            text-align: center;
        }

        .mini-stat strong {
            display: block;
            font-size: 16px;
        }

        .mini-stat span {
            color: var(--muted);
            font-size: 10px;
        }

        .details-panel {
            position: sticky;
            top: 101px;
            max-height: calc(100vh - 126px);
            overflow-y: auto;
            padding: 19px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: rgba(16, 27, 45, 0.96);
            box-shadow: var(--shadow);
        }

        .details-placeholder {
            min-height: 400px;
            display: grid;
            place-items: center;
            text-align: center;
            color: var(--muted);
            padding: 35px;
        }

        .details-title-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }

        .details-title-row h2 {
            margin: 0;
            font-size: 20px;
        }

        .detail-code {
            margin-top: 5px;
            color: #93c5fd;
            font-family:
                "Cascadia Code",
                Consolas,
                monospace;
            font-size: 12px;
        }

        .detail-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 18px 0;
        }

        .detail-actions .btn {
            padding: 8px 10px;
            font-size: 12px;
        }

        .section {
            margin-top: 17px;
            padding-top: 15px;
            border-top: 1px solid var(--border);
        }

        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 0 0 11px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #cbd5e1;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 9px;
        }

        .info-item {
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: rgba(8, 17, 31, 0.42);
        }

        .info-item span {
            display: block;
            color: var(--muted);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .info-item strong {
            display: block;
            margin-top: 5px;
            font-size: 13px;
            overflow-wrap: anywhere;
        }

        .list-card {
            margin-bottom: 8px;
            padding: 11px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: rgba(8, 17, 31, 0.43);
        }

        .list-card-header {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            font-weight: 750;
            font-size: 13px;
        }

        .list-card-subtitle {
            margin-top: 5px;
            color: var(--muted);
            font-size: 11px;
            line-height: 1.45;
        }

        .severity-critical {
            color: #fca5a5;
        }

        .severity-warning {
            color: #fcd34d;
        }

        .severity-info {
            color: #93c5fd;
        }

        .empty-state {
            padding: 50px 20px;
            text-align: center;
            color: var(--muted);
            border: 1px dashed var(--border);
            border-radius: 14px;
        }

        .loading {
            display: grid;
            place-items: center;
            min-height: 250px;
            color: var(--muted);
        }

        .modal-backdrop {
            position: fixed;
            inset: 0;
            z-index: 100;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: rgba(2, 6, 23, 0.78);
            backdrop-filter: blur(5px);
        }

        .modal-backdrop.open {
            display: flex;
        }

        .modal {
            width: min(520px, 100%);
            padding: 22px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: var(--surface);
            box-shadow: var(--shadow);
        }

        .modal h3 {
            margin: 0 0 7px;
        }

        .modal p {
            margin: 0 0 18px;
            color: var(--muted);
            line-height: 1.5;
            font-size: 13px;
        }

        .form-group {
            margin-bottom: 13px;
        }

        .form-label {
            display: block;
            margin-bottom: 6px;
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 700;
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 9px;
            margin-top: 19px;
        }

        .toast {
            position: fixed;
            z-index: 200;
            right: 22px;
            bottom: 22px;
            max-width: 420px;
            padding: 13px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: #111d30;
            color: var(--text);
            box-shadow: var(--shadow);
            transform: translateY(120px);
            opacity: 0;
            transition:
                transform 0.25s ease,
                opacity 0.25s ease;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .toast.success {
            border-color: rgba(34, 197, 94, 0.5);
        }

        .toast.error {
            border-color: rgba(239, 68, 68, 0.55);
        }

        @media (max-width: 1100px) {
            .summary-grid {
                grid-template-columns:
                    repeat(3, minmax(150px, 1fr));
            }

            .content-layout {
                grid-template-columns: 1fr;
            }

            .details-panel {
                position: static;
                max-height: none;
            }
        }

        @media (max-width: 720px) {
            .topbar {
                align-items: flex-start;
                flex-direction: column;
                padding: 16px;
            }

            .page {
                padding: 15px;
            }

            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }

            .toolbar {
                grid-template-columns: 1fr;
            }

            .profile-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
    <header class="topbar">
        <div class="topbar-left">
            <div class="logo">⚙</div>

            <div class="title-block">
                <h1>Sensor Profile Manager</h1>

                <p>
                    Profiles, telemetry schemas, alarms and
                    firmware compatibility
                </p>
            </div>
        </div>

        <div class="topbar-actions">
            <button
                class="btn btn-primary"
                onclick="window.location.href='/sensor-profile-editor'"
                title="Create a profile from an existing supported template"
            >
                + Quick Profile
            </button>

            <button
                class="btn btn-primary"
                onclick="window.location.href='/sensor-profile-editor/advanced'"
                title="Create a fully customized technical sensor profile"
            >
                + Advanced Profile
            </button>

            <button
                class="btn"
                onclick="window.location.href='/admin'"
            >
                ← Admin Home
            </button>

            <button
                class="btn btn-primary"
                onclick="refreshAll()"
            >
                Refresh
            </button>
        </div>
    </header>

    <main class="page">
        <section
            id="summaryGrid"
            class="summary-grid"
        >
            <div class="summary-card">
                <div class="summary-label">Profiles</div>
                <div class="summary-value" id="profileCount">–</div>
                <div class="summary-accent"></div>
            </div>

            <div class="summary-card">
                <div class="summary-label">Active Profiles</div>
                <div class="summary-value" id="activeCount">–</div>
                <div class="summary-accent"></div>
            </div>

            <div class="summary-card">
                <div class="summary-label">Catalog Sensors</div>
                <div class="summary-value" id="sensorCount">–</div>
                <div class="summary-accent"></div>
            </div>

            <div class="summary-card">
                <div class="summary-label">Firmware Modules</div>
                <div class="summary-value" id="moduleCount">–</div>
                <div class="summary-accent"></div>
            </div>

            <div class="summary-card">
                <div class="summary-label">Alarm Rules</div>
                <div class="summary-value" id="ruleCount">–</div>
                <div class="summary-accent"></div>
            </div>
        </section>

        <section class="toolbar">
            <input
                id="searchInput"
                class="control"
                type="search"
                placeholder="Search name, code, type or capability..."
                oninput="renderProfiles()"
            >

            <select
                id="statusFilter"
                class="control"
                onchange="renderProfiles()"
            >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="draft">Draft</option>
                <option value="deprecated">Deprecated</option>
                <option value="archived">Archived</option>
                <option value="disabled">Disabled</option>
            </select>

            <select
                id="typeFilter"
                class="control"
                onchange="renderProfiles()"
            >
                <option value="">All node types</option>
            </select>

            <button
                class="btn"
                onclick="clearFilters()"
            >
                Clear filters
            </button>
        </section>

        <section class="content-layout">
            <div>
                <div
                    id="profileGrid"
                    class="profile-grid"
                >
                    <div class="loading">
                        Loading sensor profiles...
                    </div>
                </div>
            </div>

            <aside
                id="detailsPanel"
                class="details-panel"
            >
                <div class="details-placeholder">
                    <div>
                        <div style="font-size: 42px;">⚙</div>

                        <h3>Select a sensor profile</h3>

                        <p>
                            Select a profile to inspect its fields,
                            alarm rules, sensors and firmware support.
                        </p>
                    </div>
                </div>
            </aside>
        </section>
    </main>

    <div
        id="cloneModal"
        class="modal-backdrop"
        onclick="closeCloneModalOnBackdrop(event)"
    >
        <div class="modal">
            <h3>Clone sensor profile</h3>

            <p id="cloneSourceText">
                Create an editable copy of this profile.
            </p>

            <div class="form-group">
                <label class="form-label">
                    New profile code
                </label>

                <input
                    id="cloneCode"
                    class="control"
                    maxlength="64"
                    placeholder="EXAMPLE_PROFILE_V1"
                >
            </div>

            <div class="form-group">
                <label class="form-label">
                    New profile name
                </label>

                <input
                    id="cloneName"
                    class="control"
                    maxlength="120"
                    placeholder="Example Sensor Profile"
                >
            </div>

            <div class="modal-actions">
                <button
                    class="btn"
                    onclick="closeCloneModal()"
                >
                    Cancel
                </button>

                <button
                    id="confirmCloneButton"
                    class="btn btn-primary"
                    onclick="submitClone()"
                >
                    Clone profile
                </button>
            </div>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let profiles = [];
        let selectedProfileId = null;
        let selectedProfile = null;
        let cloneSourceProfile = null;

        const iconMap = {
            environment: "🌡",
            occupancy: "◉",
            safety: "⚠",
            energy: "⚡",
            multi: "⬡",
            default: "⚙"
        };

        async function fetchJson(url, options = {}) {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },
                ...options
            });

            let payload = null;

            try {
                payload = await response.json();
            } catch (error) {
                payload = {
                    detail: "The server returned an invalid response."
                };
            }

            if (!response.ok) {
                throw new Error(
                    payload.detail
                    || payload.message
                    || "Request failed"
                );
            }

            return payload;
        }

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function showToast(message, type = "success") {
            const toast = document.getElementById("toast");

            toast.textContent = message;
            toast.className = `toast ${type} show`;

            clearTimeout(showToast.timer);

            showToast.timer = setTimeout(() => {
                toast.classList.remove("show");
            }, 3500);
        }

        function profileIcon(profile) {
            return (
                iconMap[profile.node_type]
                || iconMap[profile.icon_type]
                || iconMap.default
            );
        }

        async function refreshAll() {
            document.getElementById("profileGrid").innerHTML = `
                <div class="loading">
                    Loading sensor profiles...
                </div>
            `;

            try {
                const [
                    profilesResult,
                    statusResult
                ] = await Promise.all([
                    fetchJson(
                        "/sensor-profiles?include_disabled=true"
                    ),
                    fetchJson(
                        "/sensor-profiles/system/status"
                    )
                ]);

                profiles = profilesResult.profiles || [];

                document.getElementById(
                    "profileCount"
                ).textContent = (
                    statusResult.profile_count ?? 0
                );

                document.getElementById(
                    "activeCount"
                ).textContent = (
                    statusResult.active_profile_count ?? 0
                );

                document.getElementById(
                    "sensorCount"
                ).textContent = (
                    statusResult.sensor_count ?? 0
                );

                document.getElementById(
                    "moduleCount"
                ).textContent = (
                    statusResult.firmware_module_count ?? 0
                );

                document.getElementById(
                    "ruleCount"
                ).textContent = (
                    statusResult.alarm_rule_count ?? 0
                );

                populateTypeFilter();
                renderProfiles();

                if (selectedProfileId) {
                    const stillExists = profiles.some(
                        profile =>
                            profile.id === selectedProfileId
                    );

                    if (stillExists) {
                        await selectProfile(
                            selectedProfileId,
                            false
                        );
                    } else {
                        clearDetails();
                    }
                }

            } catch (error) {
                document.getElementById(
                    "profileGrid"
                ).innerHTML = `
                    <div class="empty-state">
                        <strong>Could not load profiles</strong>
                        <div style="margin-top: 8px;">
                            ${escapeHtml(error.message)}
                        </div>
                    </div>
                `;

                showToast(error.message, "error");
            }
        }

        function populateTypeFilter() {
            const filter = document.getElementById(
                "typeFilter"
            );

            const previousValue = filter.value;

            const nodeTypes = [
                ...new Set(
                    profiles
                        .map(profile => profile.node_type)
                        .filter(Boolean)
                )
            ].sort();

            filter.innerHTML = `
                <option value="">All node types</option>
                ${nodeTypes.map(nodeType => `
                    <option value="${escapeHtml(nodeType)}">
                        ${escapeHtml(nodeType)}
                    </option>
                `).join("")}
            `;

            if (nodeTypes.includes(previousValue)) {
                filter.value = previousValue;
            }
        }

        function clearFilters() {
            document.getElementById(
                "searchInput"
            ).value = "";

            document.getElementById(
                "statusFilter"
            ).value = "";

            document.getElementById(
                "typeFilter"
            ).value = "";

            renderProfiles();
        }

        function filteredProfiles() {
            const searchValue = document.getElementById(
                "searchInput"
            ).value.trim().toLowerCase();

            const statusValue = document.getElementById(
                "statusFilter"
            ).value;

            const typeValue = document.getElementById(
                "typeFilter"
            ).value;

            return profiles.filter(profile => {
                const searchableText = [
                    profile.profile_name,
                    profile.profile_code,
                    profile.node_type,
                    profile.description,
                    ...(profile.capabilities || [])
                ].join(" ").toLowerCase();

                const matchesSearch = (
                    !searchValue
                    || searchableText.includes(searchValue)
                );

                let matchesStatus = true;

                if (statusValue === "disabled") {
                    matchesStatus = !profile.enabled;
                } else if (statusValue) {
                    matchesStatus = (
                        profile.status === statusValue
                        && profile.enabled
                    );
                }

                const matchesType = (
                    !typeValue
                    || profile.node_type === typeValue
                );

                return (
                    matchesSearch
                    && matchesStatus
                    && matchesType
                );
            });
        }

        function renderProfiles() {
            const grid = document.getElementById(
                "profileGrid"
            );

            const filtered = filteredProfiles();

            if (!filtered.length) {
                grid.innerHTML = `
                    <div class="empty-state">
                        No profiles match the selected filters.
                    </div>
                `;
                return;
            }

            grid.innerHTML = filtered.map(profile => {
                const selectedClass = (
                    profile.id === selectedProfileId
                    ? "selected"
                    : ""
                );

                const disabledClass = (
                    profile.enabled
                    ? ""
                    : "disabled"
                );

                const statusBadge = profile.enabled
                    ? `
                        <span class="badge badge-active">
                            ${escapeHtml(profile.status)}
                        </span>
                    `
                    : `
                        <span class="badge badge-disabled">
                            disabled
                        </span>
                    `;

                const systemBadge = profile.is_system
                    ? `
                        <span class="badge badge-system">
                            system
                        </span>
                    `
                    : "";

                return `
                    <article
                        class="profile-card
                            ${selectedClass}
                            ${disabledClass}"
                        onclick="selectProfile(${profile.id})"
                    >
                        <div class="profile-heading">
                            <div style="
                                display:flex;
                                gap:11px;
                                align-items:flex-start;
                            ">
                                <div class="profile-icon">
                                    ${profileIcon(profile)}
                                </div>

                                <div>
                                    <h3 class="profile-name">
                                        ${escapeHtml(
                                            profile.profile_name
                                        )}
                                    </h3>

                                    <div class="profile-code">
                                        ${escapeHtml(
                                            profile.profile_code
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="badges">
                            ${statusBadge}
                            ${systemBadge}

                            <span class="badge">
                                ${escapeHtml(profile.node_type)}
                            </span>

                            <span class="badge">
                                v${profile.profile_version}
                            </span>
                        </div>

                        <p class="profile-description">
                            ${escapeHtml(
                                profile.description
                                || "No description provided."
                            )}
                        </p>

                        <div class="card-stats">
                            <div class="mini-stat">
                                <strong>
                                    ${profile.field_count}
                                </strong>
                                <span>Fields</span>
                            </div>

                            <div class="mini-stat">
                                <strong>
                                    ${profile.rule_count}
                                </strong>
                                <span>Rules</span>
                            </div>

                            <div class="mini-stat">
                                <strong>
                                    ${profile.sensor_count}
                                </strong>
                                <span>Sensors</span>
                            </div>

                            <div class="mini-stat">
                                <strong>
                                    ${profile.device_count}
                                </strong>
                                <span>Devices</span>
                            </div>
                        </div>
                    </article>
                `;
            }).join("");
        }

        async function selectProfile(
            profileId,
            scrollToPanel = true
        ) {
            selectedProfileId = profileId;
            renderProfiles();

            const panel = document.getElementById(
                "detailsPanel"
            );

            panel.innerHTML = `
                <div class="loading">
                    Loading profile details...
                </div>
            `;

            try {
                const result = await fetchJson(
                    `/sensor-profiles/${profileId}`
                );

                selectedProfile = result.profile;
                renderDetails(selectedProfile);

                if (
                    scrollToPanel
                    && window.innerWidth <= 1100
                ) {
                    panel.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }

            } catch (error) {
                panel.innerHTML = `
                    <div class="empty-state">
                        ${escapeHtml(error.message)}
                    </div>
                `;

                showToast(error.message, "error");
            }
        }

        function clearDetails() {
            selectedProfileId = null;
            selectedProfile = null;

            document.getElementById(
                "detailsPanel"
            ).innerHTML = `
                <div class="details-placeholder">
                    <div>
                        <div style="font-size:42px;">⚙</div>
                        <h3>Select a sensor profile</h3>
                        <p>
                            Select a profile to inspect its details.
                        </p>
                    </div>
                </div>
            `;

            renderProfiles();
        }

        function renderDetails(profile) {
            const panel = document.getElementById(
                "detailsPanel"
            );

            const enableButton = profile.enabled
                ? `
                    <button
                        class="btn"
                        onclick="setProfileEnabled(
                            ${profile.id},
                            false
                        )"
                    >
                        Disable
                    </button>
                `
                : `
                    <button
                        class="btn btn-success"
                        onclick="setProfileEnabled(
                            ${profile.id},
                            true
                        )"
                    >
                        Enable
                    </button>
                `;

            const deleteDisabled = (
                profile.can_delete
                ? ""
                : "disabled"
            );

            const capabilities = (
                profile.capabilities || []
            ).map(capability => `
                <span class="badge">
                    ${escapeHtml(capability)}
                </span>
            `).join("");

            const fieldsHtml = (
                profile.fields || []
            ).map(field => `
                <div class="list-card">
                    <div class="list-card-header">
                        <span>
                            ${escapeHtml(field.label)}
                        </span>

                        <span>
                            ${escapeHtml(field.unit || "")}
                        </span>
                    </div>

                    <div class="list-card-subtitle">
                        Key:
                        <strong>
                            ${escapeHtml(field.field_key)}
                        </strong>
                        · ${escapeHtml(field.data_type)}
                        · ${field.byte_length ?? "–"} byte(s)
                        · scale ${field.scale}
                    </div>
                </div>
            `).join("") || `
                <div class="empty-state">
                    No telemetry fields
                </div>
            `;

            const rulesHtml = (
                profile.rules || []
            ).map(rule => `
                <div class="list-card">
                    <div class="list-card-header">
                        <span>
                            ${escapeHtml(rule.rule_code)}
                        </span>

                        <span class="
                            severity-${escapeHtml(rule.severity)}
                        ">
                            ${escapeHtml(rule.severity)}
                        </span>
                    </div>

                    <div class="list-card-subtitle">
                        ${escapeHtml(rule.field_key)}
                        ${escapeHtml(rule.operator)}
                        ${escapeHtml(
                            rule.threshold_value
                            ?? rule.expected_boolean
                            ?? rule.expected_text
                            ?? ""
                        )}
                        <br>
                        ${escapeHtml(rule.message_template)}
                    </div>
                </div>
            `).join("") || `
                <div class="empty-state">
                    No alarm rules
                </div>
            `;

            const sensorsHtml = (
                profile.sensors || []
            ).map(sensor => `
                <div class="list-card">
                    <div class="list-card-header">
                        <span>
                            ${escapeHtml(sensor.model)}
                        </span>

                        <span class="badge">
                            ${escapeHtml(sensor.role)}
                        </span>
                    </div>

                    <div class="list-card-subtitle">
                        ${escapeHtml(
                            sensor.manufacturer || "Generic"
                        )}
                        · ${escapeHtml(sensor.sensor_protocol)}
                        <br>
                        Module:
                        ${escapeHtml(
                            sensor.module_key || "Not assigned"
                        )}
                    </div>
                </div>
            `).join("") || `
                <div class="empty-state">
                    No sensor components
                </div>
            `;

            const compatibilityHtml = (
                profile.firmware_compatibility || []
            ).map(item => `
                <div class="list-card">
                    <div class="list-card-header">
                        <span>
                            ${escapeHtml(item.display_name)}
                        </span>

                        <span class="badge">
                            ${escapeHtml(
                                item.min_firmware_version
                                || "Any version"
                            )}
                        </span>
                    </div>

                    <div class="list-card-subtitle">
                        ${escapeHtml(item.driver_class)}
                        · ${escapeHtml(item.supported_board)}
                    </div>
                </div>
            `).join("") || `
                <div class="empty-state">
                    No compatibility records
                </div>
            `;

            const versionsHtml = (
                profile.versions || []
            ).map(version => `
                <div class="list-card">
                    <div class="list-card-header">
                        <span>
                            Version ${version.version}
                        </span>

                        <span>
                            ${escapeHtml(
                                formatDate(version.created_at)
                            )}
                        </span>
                    </div>

                    <div class="list-card-subtitle">
                        ${escapeHtml(
                            version.change_note
                            || "No change note"
                        )}
                        <br>
                        By:
                        ${escapeHtml(
                            version.created_by
                            || "unknown"
                        )}
                    </div>
                </div>
            `).join("") || `
                <div class="empty-state">
                    No version history
                </div>
            `;

            panel.innerHTML = `
                <div class="details-title-row">
                    <div>
                        <h2>
                            ${escapeHtml(profile.profile_name)}
                        </h2>

                        <div class="detail-code">
                            ${escapeHtml(profile.profile_code)}
                        </div>
                    </div>

                    <div class="profile-icon">
                        ${profileIcon(profile)}
                    </div>
                </div>

                <div class="badges">
                    <span class="badge ${
                        profile.enabled
                        ? "badge-active"
                        : "badge-disabled"
                    }">
                        ${
                            profile.enabled
                            ? escapeHtml(profile.status)
                            : "disabled"
                        }
                    </span>

                    ${
                        profile.is_system
                        ? `
                            <span class="badge badge-system">
                                system profile
                            </span>
                        `
                        : `
                            <span class="badge">
                                custom profile
                            </span>
                        `
                    }

                    ${capabilities}
                </div>

                <div class="detail-actions">
                    <button
                        class="btn btn-primary"
                        onclick="openCloneModal()"
                    >
                        Clone
                    </button>
                    <button
                        class="btn"
                        ${profile.is_system ? "disabled" : ""}
                        onclick="
                            window.location.href=
                            '/sensor-profile-editor/advanced?profile_id=${profile.id}'
                        "
                        title="${
                            profile.is_system
                            ? "Clone system profiles before editing"
                            : "Edit this profile"
                        }"
                    >
                       Advanced Edit
                    </button>

                    ${enableButton}

                    <button
                        class="btn btn-danger"
                        ${deleteDisabled}
                        onclick="deleteSelectedProfile()"
                        title="${
                            profile.can_delete
                            ? "Delete this profile"
                            : "System or assigned profiles cannot be deleted"
                        }"
                    >
                        Delete
                    </button>
                </div>

                <p class="profile-description">
                    ${escapeHtml(
                        profile.description
                        || "No description provided."
                    )}
                </p>

                <div class="info-grid">
                    <div class="info-item">
                        <span>Node type</span>
                        <strong>
                            ${escapeHtml(profile.node_type)}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>Profile version</span>
                        <strong>
                            ${profile.profile_version}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>Payload version</span>
                        <strong>
                            ${profile.payload_version}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>LoRaWAN FPort</span>
                        <strong>
                            ${profile.f_port}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>Uplink interval</span>
                        <strong>
                            ${profile.uplink_interval_seconds}s
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>Assigned devices</span>
                        <strong>
                            ${profile.device_count}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>Payload encoder</span>
                        <strong>
                            ${escapeHtml(
                                profile.payload_encoder_key
                            )}
                        </strong>
                    </div>

                    <div class="info-item">
                        <span>ThingsBoard profile</span>
                        <strong>
                            ${escapeHtml(
                                profile.tb_device_profile_name
                                || "Not assigned"
                            )}
                        </strong>
                    </div>
                </div>

                <section class="section">
                    <h3 class="section-title">
                        Telemetry fields
                        <span>${profile.fields.length}</span>
                    </h3>

                    ${fieldsHtml}
                </section>

                <section class="section">
                    <h3 class="section-title">
                        Alarm rules
                        <span>${profile.rules.length}</span>
                    </h3>

                    ${rulesHtml}
                </section>

                <section class="section">
                    <h3 class="section-title">
                        Sensor components
                        <span>${profile.sensors.length}</span>
                    </h3>

                    ${sensorsHtml}
                </section>

                <section class="section">
                    <h3 class="section-title">
                        Firmware compatibility
                        <span>
                            ${profile.firmware_compatibility.length}
                        </span>
                    </h3>

                    ${compatibilityHtml}
                </section>

                <section class="section">
                    <h3 class="section-title">
                        Version history
                        <span>${profile.versions.length}</span>
                    </h3>

                    ${versionsHtml}
                </section>
            `;
        }

        function formatDate(value) {
            if (!value) {
                return "Unknown";
            }

            const date = new Date(value);

            if (Number.isNaN(date.getTime())) {
                return value;
            }

            return date.toLocaleString();
        }

        function openCloneModal() {
            if (!selectedProfile) {
                return;
            }

            cloneSourceProfile = selectedProfile;

            document.getElementById(
                "cloneSourceText"
            ).textContent = (
                `Create an editable copy of `
                + `${selectedProfile.profile_code}.`
            );

            document.getElementById(
                "cloneCode"
            ).value = (
                `${selectedProfile.profile_code}_COPY`
            ).replace(/[^A-Z0-9_]/g, "_");

            document.getElementById(
                "cloneName"
            ).value = (
                `${selectedProfile.profile_name} Copy`
            );

            document.getElementById(
                "cloneModal"
            ).classList.add("open");

            document.getElementById(
                "cloneCode"
            ).focus();
        }

        function closeCloneModal() {
            document.getElementById(
                "cloneModal"
            ).classList.remove("open");

            cloneSourceProfile = null;
        }

        function closeCloneModalOnBackdrop(event) {
            if (
                event.target.id === "cloneModal"
            ) {
                closeCloneModal();
            }
        }

        async function submitClone() {
            if (!cloneSourceProfile) {
                return;
            }

            const newProfileCode = document.getElementById(
                "cloneCode"
            ).value.trim().toUpperCase();

            const newProfileName = document.getElementById(
                "cloneName"
            ).value.trim();

            if (!newProfileCode || !newProfileName) {
                showToast(
                    "Profile code and name are required.",
                    "error"
                );
                return;
            }

            const button = document.getElementById(
                "confirmCloneButton"
            );

            button.disabled = true;
            button.textContent = "Cloning...";

            try {
                const result = await fetchJson(
                    `/sensor-profiles/${cloneSourceProfile.id}/clone`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            new_profile_code: newProfileCode,
                            new_profile_name: newProfileName
                        })
                    }
                );

                closeCloneModal();

                selectedProfileId = result.profile.id;

                showToast(
                    `Profile ${newProfileCode} created.`
                );

                await refreshAll();

            } catch (error) {
                showToast(error.message, "error");

            } finally {
                button.disabled = false;
                button.textContent = "Clone profile";
            }
        }

        async function setProfileEnabled(
            profileId,
            enabled
        ) {
            const action = enabled
                ? "enable"
                : "disable";

            const confirmation = confirm(
                `Are you sure you want to ${action} this profile?`
            );

            if (!confirmation) {
                return;
            }

            try {
                await fetchJson(
                    `/sensor-profiles/${profileId}/${action}`,
                    {
                        method: "POST",
                        body: JSON.stringify({})
                    }
                );

                showToast(
                    `Profile ${action}d successfully.`
                );

                await refreshAll();

            } catch (error) {
                showToast(error.message, "error");
            }
        }

        async function deleteSelectedProfile() {
            if (
                !selectedProfile
                || !selectedProfile.can_delete
            ) {
                return;
            }

            const confirmed = confirm(
                `Delete ${selectedProfile.profile_code}? `
                + `This action cannot be undone.`
            );

            if (!confirmed) {
                return;
            }

            try {
                await fetchJson(
                    `/sensor-profiles/${selectedProfile.id}`,
                    {
                        method: "DELETE"
                    }
                );

                showToast(
                    "Sensor profile deleted."
                );

                clearDetails();
                await refreshAll();

            } catch (error) {
                showToast(error.message, "error");
            }
        }

        document.addEventListener(
            "DOMContentLoaded",
            refreshAll
        );
    </script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get(
    "/sensor-profile-editor",
    response_class=HTMLResponse,
)
def simple_sensor_profile_editor_page():
    """
    Simplified profile creation page for normal administrators.

    Technical settings are copied automatically from a supported
    active template.
    """

    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Create Sensor Profile</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        * {
            box-sizing: border-box;
        }

        :root {
            --background: #08111f;
            --surface: #101b2d;
            --surface-light: #17253b;
            --border: #2a3d58;
            --text: #f8fafc;
            --muted: #94a3b8;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #22c55e;
            --danger: #ef4444;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background: var(--background);
            color: var(--text);
            font-family:
                Inter,
                Arial,
                sans-serif;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 20px 28px;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
        }

        .topbar h1 {
            margin: 0 0 5px;
            font-size: 25px;
        }

        .topbar p {
            margin: 0;
            color: var(--muted);
            font-size: 14px;
        }

        .topbar-actions {
            display: flex;
            gap: 10px;
        }

        .page {
            width: min(1050px, 100%);
            margin: 0 auto;
            padding: 28px;
        }

        .panel {
            padding: 24px;
            margin-bottom: 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
        }

        .panel h2 {
            margin: 0 0 6px;
            font-size: 19px;
        }

        .panel-description {
            margin: 0 0 22px;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.5;
        }

        .form-grid {
            display: grid;
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
            gap: 18px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 7px;
        }

        .form-group.full {
            grid-column: 1 / -1;
        }

        label {
            font-size: 13px;
            font-weight: 700;
        }

        .required {
            color: var(--danger);
        }

        .control {
            width: 100%;
            min-height: 44px;
            padding: 10px 12px;
            color: var(--text);
            background: var(--surface-light);
            border: 1px solid var(--border);
            border-radius: 10px;
            outline: none;
        }

        .control:focus {
            border-color: var(--primary);
        }

        .control[readonly] {
            color: var(--muted);
        }

        .help {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.45;
        }

        .template-info {
            display: none;
            margin-top: 18px;
            padding: 15px;
            color: var(--muted);
            background: rgba(59, 130, 246, 0.08);
            border: 1px solid rgba(59, 130, 246, 0.35);
            border-radius: 12px;
            line-height: 1.55;
            font-size: 13px;
        }

        .template-info.show {
            display: block;
        }

        .automatic-box {
            padding: 16px;
            color: var(--muted);
            background: rgba(34, 197, 94, 0.07);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.6;
        }

        .automatic-box strong {
            color: var(--text);
        }

        .alarm-grid {
            display: grid;
            gap: 13px;
        }

        .alarm-card {
            display: grid;
            grid-template-columns:
                minmax(180px, 1fr)
                minmax(130px, 180px)
                minmax(130px, 180px);
            gap: 14px;
            align-items: end;
            padding: 15px;
            background: rgba(8, 17, 31, 0.48);
            border: 1px solid var(--border);
            border-radius: 12px;
        }

        .alarm-title {
            font-weight: 700;
            margin-bottom: 5px;
        }

        .alarm-meta {
            color: var(--muted);
            font-size: 12px;
        }

        .empty-state {
            padding: 18px;
            color: var(--muted);
            text-align: center;
            border: 1px dashed var(--border);
            border-radius: 12px;
        }

        .message {
            display: none;
            margin-bottom: 18px;
            padding: 14px 16px;
            border-radius: 11px;
            line-height: 1.5;
        }

        .message.show {
            display: block;
        }

        .message.success {
            color: #bbf7d0;
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.4);
        }

        .message.error {
            color: #fecaca;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.4);
        }

        .actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .btn {
            min-height: 42px;
            padding: 9px 16px;
            color: var(--text);
            background: var(--surface-light);
            border: 1px solid var(--border);
            border-radius: 10px;
            cursor: pointer;
            font-weight: 700;
        }

        .btn:hover {
            filter: brightness(1.08);
        }

        .btn-primary {
            background: var(--primary);
            border-color: var(--primary);
        }

        .btn-primary:hover {
            background: var(--primary-hover);
        }

        .btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        @media (max-width: 760px) {
            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .form-grid,
            .alarm-card {
                grid-template-columns: 1fr;
            }

            .page {
                padding: 16px;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
    <header class="topbar">
        <div>
            <h1>Create Sensor Profile</h1>

            <p>
                Select a supported template and configure only the
                settings needed for deployment.
            </p>
        </div>

        <div class="topbar-actions">
            <button
                class="btn"
                onclick="window.location.href='/sensor-profile-manager'"
            >
                ← Profile Manager
            </button>

            <button
                class="btn"
                onclick="window.location.href='/admin'"
            >
                Admin Home
            </button>
        </div>
    </header>

    <main class="page">
        <div
            id="message"
            class="message"
        ></div>

        <section class="panel">
            <h2>Basic Profile Information</h2>

            <p class="panel-description">
                The backend automatically copies the payload format,
                telemetry fields, sensor driver, TTN decoder,
                ThingsBoard mapping and firmware compatibility.
            </p>

            <div class="form-grid">
                <div class="form-group full">
                    <label for="templateSelect">
                        Supported sensor template
                        <span class="required">*</span>
                    </label>

                    <select
                        id="templateSelect"
                        class="control"
                        onchange="loadSelectedTemplate()"
                    >
                        <option value="">
                            Loading supported templates...
                        </option>
                    </select>

                    <div class="help">
                        Only active supported templates are shown.
                    </div>
                </div>

                <div class="form-group">
                    <label for="useCase">
                        Use case
                    </label>

                    <input
                        id="useCase"
                        class="control"
                        readonly
                        placeholder="Selected automatically"
                    >
                </div>

                <div class="form-group">
                    <label for="profileName">
                        Profile name
                        <span class="required">*</span>
                    </label>

                    <input
                        id="profileName"
                        class="control"
                        maxlength="120"
                        placeholder="Office Temperature Profile"
                    >
                </div>

                <div class="form-group">
                    <label for="uplinkInterval">
                        Uplink interval in seconds
                    </label>

                    <input
                        id="uplinkInterval"
                        class="control"
                        type="number"
                        min="5"
                        max="86400"
                        value="60"
                    >

                    <div class="help">
                        Allowed range: 5 to 86400 seconds.
                    </div>
                </div>
            </div>

            <div
                id="templateInfo"
                class="template-info"
            ></div>
        </section>

        <section class="panel">
            <h2>Optional Alarm Thresholds</h2>

            <p class="panel-description">
                Change numeric limits when necessary. Boolean safety
                and occupancy rules remain automatic.
            </p>

            <div
                id="alarmRules"
                class="alarm-grid"
            >
                <div class="empty-state">
                    Select a supported sensor template first.
                </div>
            </div>
        </section>

        <section class="panel">
            <div class="automatic-box">
                <strong>Created automatically:</strong>
                profile code, profile version, node type, capabilities,
                firmware module, payload encoder, TTN formatter,
                telemetry schema, ThingsBoard profile, icon and
                compatibility settings.
            </div>
        </section>

        <section class="panel">
            <div class="actions">
                <button
                    class="btn"
                    onclick="window.location.href='/sensor-profile-manager'"
                >
                    Cancel
                </button>

                <button
                    id="createButton"
                    class="btn btn-primary"
                    onclick="createProfile()"
                >
                    Create and activate profile
                </button>
            </div>
        </section>
    </main>

    <script>
        const state = {
            templates: [],
            selectedProfile: null
        };

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function showMessage(text, type) {
            const element = document.getElementById(
                "message"
            );

            element.textContent = text;
            element.className = (
                "message show " + type
            );

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        }

        async function fetchJson(url, options = {}) {
            const requestOptions = {
                ...options,
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                }
            };

            const response = await fetch(
                url,
                requestOptions
            );

            let data = {};

            try {
                data = await response.json();
            } catch (_) {
                data = {};
            }

            if (!response.ok) {
                let detail = data.detail;

                if (
                    detail
                    && typeof detail !== "string"
                ) {
                    detail = JSON.stringify(detail);
                }

                throw new Error(
                    detail
                    || data.message
                    || `Request failed: ${response.status}`
                );
            }

            return data;
        }

        function renderTemplateOptions() {
            const select = document.getElementById(
                "templateSelect"
            );

            if (!state.templates.length) {
                select.innerHTML = `
                    <option value="">
                        No active supported templates found
                    </option>
                `;

                select.disabled = true;
                return;
            }

            select.disabled = false;

            select.innerHTML = `
                <option value="">
                    Select a supported sensor template
                </option>
            `;

            for (const profile of state.templates) {
                const option = document.createElement(
                    "option"
                );

                option.value = profile.id;

                option.textContent = (
                    profile.profile_name
                    + " — "
                    + profile.node_type
                );

                select.appendChild(option);
            }
        }

        function renderAlarmRules(profile) {
            const container = document.getElementById(
                "alarmRules"
            );

            const editableRules = (
                profile.rules || []
            ).filter(rule => {
                return (
                    rule.threshold_value !== null
                    && rule.threshold_value !== undefined
                    && rule.threshold_value !== ""
                );
            });

            if (!editableRules.length) {
                container.innerHTML = `
                    <div class="empty-state">
                        This template has no numeric alarm thresholds.
                        Its automatic Boolean rules will be copied.
                    </div>
                `;

                return;
            }

            container.innerHTML = editableRules.map(
                rule => {
                    const needsSecondValue = (
                        rule.operator === "between"
                        || rule.operator === "outside"
                        || (
                            rule.threshold_value_2 !== null
                            && rule.threshold_value_2 !== undefined
                        )
                    );

                    const secondInput = needsSecondValue
                        ? `
                            <div class="form-group">
                                <label>
                                    Second threshold
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    data-threshold="2"
                                    value="${
                                        escapeHtml(
                                            rule.threshold_value_2 ?? ""
                                        )
                                    }"
                                >
                            </div>
                        `
                        : `
                            <div></div>
                        `;

                    return `
                        <div
                            class="alarm-card"
                            data-rule-code="${
                                escapeHtml(rule.rule_code)
                            }"
                        >
                            <div>
                                <div class="alarm-title">
                                    ${escapeHtml(
                                        rule.message_template
                                        || rule.rule_code
                                    )}
                                </div>

                                <div class="alarm-meta">
                                    ${escapeHtml(rule.field_key)}
                                    ${escapeHtml(rule.operator)}
                                    · ${escapeHtml(rule.severity)}
                                </div>
                            </div>

                            <div class="form-group">
                                <label>
                                    Threshold
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    data-threshold="1"
                                    value="${
                                        escapeHtml(
                                            rule.threshold_value
                                        )
                                    }"
                                >
                            </div>

                            ${secondInput}
                        </div>
                    `;
                }
            ).join("");
        }

        async function loadSelectedTemplate() {
            const profileId = document.getElementById(
                "templateSelect"
            ).value;

            state.selectedProfile = null;

            document.getElementById(
                "useCase"
            ).value = "";

            document.getElementById(
                "templateInfo"
            ).classList.remove("show");

            if (!profileId) {
                document.getElementById(
                    "alarmRules"
                ).innerHTML = `
                    <div class="empty-state">
                        Select a supported sensor template first.
                    </div>
                `;

                return;
            }

            try {
                const result = await fetchJson(
                    `/sensor-profiles/${profileId}`
                    + "?include_formatter=false"
                );

                const profile = result.profile;

                state.selectedProfile = profile;

                document.getElementById(
                    "useCase"
                ).value = (
                    profile.node_type || ""
                );

                document.getElementById(
                    "uplinkInterval"
                ).value = (
                    profile.uplink_interval_seconds
                    || 60
                );

                const capabilities = (
                    profile.capabilities || []
                ).join(", ");

                const sensorNames = (
                    profile.sensors || []
                ).map(sensor => {
                    return (
                        sensor.model
                        || sensor.sensor_code
                    );
                }).join(", ");

                const info = document.getElementById(
                    "templateInfo"
                );

                info.innerHTML = `
                    <strong>
                        ${escapeHtml(profile.profile_name)}
                    </strong>
                    <br>
                    Sensors:
                    ${escapeHtml(sensorNames || "Compatibility template")}
                    <br>
                    Capabilities:
                    ${escapeHtml(capabilities || "Not specified")}
                `;

                info.classList.add("show");

                renderAlarmRules(profile);

            } catch (error) {
                showMessage(
                    "Could not load the selected template: "
                    + error.message,
                    "error"
                );
            }
        }

        function collectAlarmThresholds() {
            const result = {};

            document.querySelectorAll(
                ".alarm-card"
            ).forEach(card => {
                const ruleCode = card.dataset.ruleCode;

                const firstInput = card.querySelector(
                    '[data-threshold="1"]'
                );

                const secondInput = card.querySelector(
                    '[data-threshold="2"]'
                );

                const override = {};

                if (
                    firstInput
                    && firstInput.value.trim() !== ""
                ) {
                    override.threshold_value = Number(
                        firstInput.value
                    );

                    if (
                        Number.isNaN(
                            override.threshold_value
                        )
                    ) {
                        throw new Error(
                            `${ruleCode} threshold must be numeric`
                        );
                    }
                }

                if (
                    secondInput
                    && secondInput.value.trim() !== ""
                ) {
                    override.threshold_value_2 = Number(
                        secondInput.value
                    );

                    if (
                        Number.isNaN(
                            override.threshold_value_2
                        )
                    ) {
                        throw new Error(
                            `${ruleCode} second threshold must be numeric`
                        );
                    }
                }

                if (
                    Object.keys(override).length
                ) {
                    result[ruleCode] = override;
                }
            });

            return result;
        }

        async function createProfile() {
            const templateId = document.getElementById(
                "templateSelect"
            ).value;

            const profileName = document.getElementById(
                "profileName"
            ).value.trim();

            const interval = Number(
                document.getElementById(
                    "uplinkInterval"
                ).value
            );

            if (!templateId) {
                showMessage(
                    "Select a supported sensor template.",
                    "error"
                );
                return;
            }

            if (!profileName) {
                showMessage(
                    "Enter a profile name.",
                    "error"
                );
                return;
            }

            if (
                !Number.isInteger(interval)
                || interval < 5
                || interval > 86400
            ) {
                showMessage(
                    "Uplink interval must be a whole number "
                    + "between 5 and 86400 seconds.",
                    "error"
                );
                return;
            }

            let alarmThresholds;

            try {
                alarmThresholds = (
                    collectAlarmThresholds()
                );

            } catch (error) {
                showMessage(
                    error.message,
                    "error"
                );
                return;
            }

            const button = document.getElementById(
                "createButton"
            );

            button.disabled = true;
            button.textContent = "Creating profile...";

            try {
                const result = await fetchJson(
                    `/sensor-profiles/${templateId}/clone`,
                    {
                        method: "POST",
                        body: JSON.stringify({
                            new_profile_name: profileName,
                            activate: true,
                            uplink_interval_seconds: interval,
                            alarm_thresholds: alarmThresholds
                        })
                    }
                );

                showMessage(
                    "Profile created and activated: "
                    + result.profile.profile_code,
                    "success"
                );

                setTimeout(() => {
                    window.location.href = (
                        "/sensor-profile-manager"
                    );
                }, 1200);

            } catch (error) {
                showMessage(
                    "Could not create the profile: "
                    + error.message,
                    "error"
                );

                button.disabled = false;
                button.textContent = (
                    "Create and activate profile"
                );
            }
        }

        async function initializePage() {
            try {
                const result = await fetchJson(
                    "/sensor-profiles"
                    + "?include_disabled=false"
                );

                const activeProfiles = (
                    result.profiles || []
                ).filter(profile => {
                    return (
                        Boolean(profile.enabled)
                        && profile.status === "active"
                    );
                });

                const systemTemplates = (
                    activeProfiles.filter(
                        profile => Boolean(
                            profile.is_system
                        )
                    )
                );

                state.templates = (
                    systemTemplates.length
                    ? systemTemplates
                    : activeProfiles
                );

                renderTemplateOptions();

            } catch (error) {
                showMessage(
                    "Could not load supported templates: "
                    + error.message,
                    "error"
                );
            }
        }

        document.addEventListener(
            "DOMContentLoaded",
            initializePage
        );
    </script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get(
    "/sensor-profile-editor/advanced",
    response_class=HTMLResponse,
)
def sensor_profile_advanced_editor_page():
    """
    Administrator page for creating and editing custom
    sensor profiles.
    """

    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Sensor Profile Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        * {
            box-sizing: border-box;
        }

        :root {
            --background: #08111f;
            --surface: #101b2d;
            --surface-light: #17253b;
            --surface-hover: #1d2d46;
            --border: #2a3d58;
            --text: #f8fafc;
            --muted: #94a3b8;
            --primary: #3b82f6;
            --primary-dark: #2563eb;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --purple: #8b5cf6;
            --shadow: 0 18px 45px rgba(0, 0, 0, 0.32);
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
            color: var(--text);
            background:
                radial-gradient(
                    circle at top left,
                    rgba(59, 130, 246, 0.14),
                    transparent 33%
                ),
                radial-gradient(
                    circle at top right,
                    rgba(139, 92, 246, 0.12),
                    transparent 30%
                ),
                var(--background);
        }

        button,
        input,
        select,
        textarea {
            font: inherit;
        }

        button {
            cursor: pointer;
        }

        .topbar {
            position: sticky;
            top: 0;
            z-index: 50;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            padding: 18px 28px;
            background: rgba(8, 17, 31, 0.94);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(14px);
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo {
            width: 46px;
            height: 46px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            background:
                linear-gradient(
                    135deg,
                    var(--primary),
                    var(--purple)
                );
            font-size: 22px;
        }

        .title-block h1 {
            margin: 0;
            font-size: 22px;
        }

        .title-block p {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 13px;
        }

        .topbar-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
        }

        .page {
            max-width: 1500px;
            margin: 0 auto;
            padding: 25px;
        }

        .btn {
            min-height: 41px;
            padding: 9px 14px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--surface-light);
            color: var(--text);
            font-weight: 700;
            transition:
                transform 0.15s ease,
                background 0.15s ease;
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-1px);
            background: var(--surface-hover);
        }

        .btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--primary);
            border-color: var(--primary);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--primary-dark);
        }

        .btn-success {
            color: #bbf7d0;
            border-color: rgba(34, 197, 94, 0.5);
            background: rgba(34, 197, 94, 0.11);
        }

        .btn-danger {
            color: #fecaca;
            border-color: rgba(239, 68, 68, 0.48);
            background: rgba(239, 68, 68, 0.10);
        }

        .btn-small {
            min-height: 34px;
            padding: 6px 10px;
            font-size: 12px;
        }

        .message {
            display: none;
            margin-bottom: 16px;
            padding: 13px 15px;
            border: 1px solid var(--border);
            border-radius: 11px;
            background: var(--surface);
            white-space: pre-wrap;
            line-height: 1.5;
        }

        .message.show {
            display: block;
        }

        .message.success {
            border-color: rgba(34, 197, 94, 0.52);
            color: #bbf7d0;
        }

        .message.error {
            border-color: rgba(239, 68, 68, 0.52);
            color: #fecaca;
        }

        .system-warning {
            display: none;
            margin-bottom: 18px;
            padding: 15px;
            border: 1px solid rgba(245, 158, 11, 0.48);
            border-radius: 12px;
            background: rgba(245, 158, 11, 0.10);
            color: #fde68a;
            line-height: 1.5;
        }

        .system-warning.show {
            display: block;
        }

        .layout {
            display: grid;
            grid-template-columns:
                minmax(0, 1fr)
                minmax(370px, 470px);
            gap: 18px;
            align-items: start;
        }

        .main-column,
        .side-column {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .side-column {
            position: sticky;
            top: 103px;
        }

        .panel {
            padding: 19px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: rgba(16, 27, 45, 0.95);
            box-shadow: var(--shadow);
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 17px;
        }

        .panel-title {
            margin: 0;
            font-size: 17px;
        }

        .panel-description {
            margin: 5px 0 0;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.45;
        }

        .form-grid {
            display: grid;
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
            gap: 13px;
        }

        .form-grid-three {
            display: grid;
            grid-template-columns:
                repeat(3, minmax(0, 1fr));
            gap: 13px;
        }

        .form-group {
            min-width: 0;
        }

        .form-group.full {
            grid-column: 1 / -1;
        }

        .label {
            display: block;
            margin-bottom: 6px;
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 750;
        }

        .required {
            color: #fca5a5;
        }

        .control {
            width: 100%;
            min-height: 42px;
            padding: 10px 11px;
            border: 1px solid var(--border);
            border-radius: 10px;
            outline: none;
            background: var(--surface-light);
            color: var(--text);
        }

        textarea.control {
            min-height: 115px;
            resize: vertical;
            font-family:
                "Cascadia Code",
                Consolas,
                monospace;
            font-size: 12px;
            line-height: 1.5;
        }

        textarea.formatter {
            min-height: 270px;
        }

        .control:focus {
            border-color: var(--primary);
            box-shadow:
                0 0 0 3px rgba(59, 130, 246, 0.13);
        }

        .control:disabled,
        .control[readonly] {
            opacity: 0.62;
            cursor: not-allowed;
        }

        .help {
            margin-top: 5px;
            color: var(--muted);
            font-size: 10px;
            line-height: 1.4;
        }

        .checkbox-row {
            min-height: 42px;
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 9px 11px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--surface-light);
        }

        .checkbox-row input {
            width: 17px;
            height: 17px;
        }

        .item-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .item-card {
            padding: 14px;
            border: 1px solid var(--border);
            border-radius: 13px;
            background: rgba(8, 17, 31, 0.48);
        }

        .item-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 13px;
        }

        .item-heading strong {
            font-size: 13px;
        }

        .empty-state {
            padding: 25px;
            text-align: center;
            color: var(--muted);
            border: 1px dashed var(--border);
            border-radius: 12px;
        }

        .validation-list {
            margin: 0;
            padding-left: 20px;
        }

        .validation-list li {
            margin-bottom: 5px;
        }

        .summary-row {
            display: flex;
            justify-content: space-between;
            gap: 15px;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }

        .summary-row:last-child {
            border-bottom: 0;
        }

        .summary-row span {
            color: var(--muted);
        }

        .summary-row strong {
            text-align: right;
            overflow-wrap: anywhere;
        }

        .action-stack {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 9px;
            margin-top: 15px;
        }

        .action-stack .btn-primary {
            grid-column: 1 / -1;
        }

        @media (max-width: 1050px) {
            .layout {
                grid-template-columns: 1fr;
            }

            .side-column {
                position: static;
            }
        }

        @media (max-width: 720px) {
            .topbar {
                align-items: flex-start;
                flex-direction: column;
                padding: 16px;
            }

            .page {
                padding: 15px;
            }

            .form-grid,
            .form-grid-three {
                grid-template-columns: 1fr;
            }

            .form-group.full {
                grid-column: auto;
            }

            .action-stack {
                grid-template-columns: 1fr;
            }

            .action-stack .btn-primary {
                grid-column: auto;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
    <header class="topbar">
        <div class="topbar-left">
            <div class="logo">✎</div>

            <div class="title-block">
                <h1 id="pageTitle">
                    Create Sensor Profile
                </h1>

                <p>
                    Define sensors, payload fields, alarms and
                    platform mappings
                </p>
            </div>
        </div>

        <div class="topbar-actions">
            <button
                class="btn"
                onclick="window.location.href='/sensor-profile-manager'"
            >
                ← Profile Manager
            </button>

            <button
                class="btn"
                onclick="window.location.href='/admin'"
            >
                Admin Home
            </button>
        </div>
    </header>

    <main class="page">
        <div
            id="message"
            class="message"
        ></div>

        <div
            id="systemWarning"
            class="system-warning"
        >
            This is a protected system profile. It cannot be edited
            directly. Return to the Profile Manager and clone it first.
        </div>

        <div class="layout">
            <div class="main-column">
                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                General Information
                            </h2>

                            <p class="panel-description">
                                Identity, type, status and visual settings.
                            </p>
                        </div>
                    </div>

                    <div class="form-grid">
                        <div class="form-group">
                            <label class="label">
                                Profile code
                                <span class="required">*</span>
                            </label>

                            <input
                                id="profileCode"
                                class="control"
                                maxlength="64"
                                placeholder="AIR_QUALITY_BME688_V1"
                            >

                            <div class="help">
                                Uppercase letters, numbers and underscores.
                                The code cannot change after creation.
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Profile name
                                <span class="required">*</span>
                            </label>

                            <input
                                id="profileName"
                                class="control"
                                maxlength="120"
                                placeholder="BME688 Air Quality"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Node type
                                <span class="required">*</span>
                            </label>

                            <input
                                id="nodeType"
                                class="control"
                                maxlength="64"
                                placeholder="air_quality"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Capabilities
                                <span class="required">*</span>
                            </label>

                            <input
                                id="capabilities"
                                class="control"
                                placeholder="air_quality, environment"
                            >

                            <div class="help">
                                Separate multiple capabilities using commas.
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="label">Status</label>

                            <select
                                id="profileStatus"
                                class="control"
                            >
                                <option value="draft">Draft</option>
                                <option value="active">Active</option>
                                <option value="deprecated">
                                    Deprecated
                                </option>
                                <option value="archived">
                                    Archived
                                </option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label class="label">Enabled</label>

                            <label class="checkbox-row">
                                <input
                                    id="profileEnabled"
                                    type="checkbox"
                                    checked
                                >
                                Available for use
                            </label>
                        </div>

                        <div class="form-group">
                            <label class="label">Icon type</label>

                            <input
                                id="iconType"
                                class="control"
                                value="default"
                                placeholder="air_quality"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">Icon color</label>

                            <input
                                id="iconColor"
                                class="control"
                                type="color"
                                value="#3b82f6"
                            >
                        </div>

                        <div class="form-group full">
                            <label class="label">Description</label>

                            <textarea
                                id="description"
                                class="control"
                                placeholder="Explain the sensor use case..."
                            ></textarea>
                        </div>
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                Payload and Platform Mapping
                            </h2>

                            <p class="panel-description">
                                Configure transmission, TTN and ThingsBoard.
                            </p>
                        </div>
                    </div>

                    <div class="form-grid-three">
                        <div class="form-group">
                            <label class="label">
                                Payload encoder key
                                <span class="required">*</span>
                            </label>

                            <input
                                id="payloadEncoderKey"
                                class="control"
                                placeholder="air_quality_v1"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Payload version
                            </label>

                            <input
                                id="payloadVersion"
                                class="control"
                                type="number"
                                min="1"
                                value="1"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                LoRaWAN FPort
                            </label>

                            <input
                                id="fPort"
                                class="control"
                                type="number"
                                min="1"
                                max="223"
                                value="1"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Uplink interval
                            </label>

                            <input
                                id="uplinkInterval"
                                class="control"
                                type="number"
                                min="5"
                                value="60"
                            >

                            <div class="help">Seconds</div>
                        </div>

                        <div class="form-group">
                            <label class="label">
                                ThingsBoard profile
                            </label>

                            <input
                                id="tbProfileName"
                                class="control"
                                placeholder="air_quality_profile"
                            >
                        </div>

                        <div class="form-group">
                            <label class="label">
                                Formatter type
                            </label>

                            <input
                                id="formatterType"
                                class="control"
                                value="javascript"
                                readonly
                            >
                        </div>

                        <div class="form-group full">
                            <label class="label">
                                Device configuration schema
                            </label>

                            <textarea
                                id="configurationSchema"
                                class="control"
                            >{"protocol":"i2c","properties":{}}</textarea>

                            <div class="help">
                                JSON configuration sent to or used by
                                firmware provisioning.
                            </div>
                        </div>

                        <div class="form-group full">
                            <label class="label">
                                TTN JavaScript decoder
                                <span class="required">*</span>
                            </label>

                            <textarea
                                id="formatterCode"
                                class="control formatter"
                                spellcheck="false"
                            >function decodeUplink(input) {
    return {
        data: {}
    };
}</textarea>
                        </div>
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                Sensor Components
                            </h2>

                            <p class="panel-description">
                                Select physical sensors and compatible
                                firmware modules.
                            </p>
                        </div>

                        <button
                            class="btn btn-small btn-success"
                            onclick="addSensor()"
                        >
                            + Add sensor
                        </button>
                    </div>

                    <div
                        id="sensorList"
                        class="item-list"
                    ></div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                Telemetry Fields
                            </h2>

                            <p class="panel-description">
                                Define decoded values and payload layout.
                            </p>
                        </div>

                        <button
                            class="btn btn-small btn-success"
                            onclick="addField()"
                        >
                            + Add field
                        </button>
                    </div>

                    <div
                        id="fieldList"
                        class="item-list"
                    ></div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                Alarm Rules
                            </h2>

                            <p class="panel-description">
                                Configure profile-driven dynamic alarms.
                            </p>
                        </div>

                        <button
                            class="btn btn-small btn-success"
                            onclick="addRule()"
                        >
                            + Add rule
                        </button>
                    </div>

                    <div
                        id="ruleList"
                        class="item-list"
                    ></div>
                </section>
            </div>

            <aside class="side-column">
                <section class="panel">
                    <div class="panel-header">
                        <div>
                            <h2 class="panel-title">
                                Profile Summary
                            </h2>

                            <p class="panel-description">
                                Review and validate before saving.
                            </p>
                        </div>
                    </div>

                    <div class="summary-row">
                        <span>Mode</span>
                        <strong id="summaryMode">Create</strong>
                    </div>

                    <div class="summary-row">
                        <span>Telemetry fields</span>
                        <strong id="summaryFields">0</strong>
                    </div>

                    <div class="summary-row">
                        <span>Alarm rules</span>
                        <strong id="summaryRules">0</strong>
                    </div>

                    <div class="summary-row">
                        <span>Sensor components</span>
                        <strong id="summarySensors">0</strong>
                    </div>

                    <div class="summary-row">
                        <span>Current version</span>
                        <strong id="summaryVersion">1</strong>
                    </div>

                    <div class="form-group" style="margin-top:15px;">
                        <label class="label">
                            Change note
                        </label>

                        <textarea
                            id="changeNote"
                            class="control"
                            placeholder="Describe this change..."
                        ></textarea>
                    </div>

                    <div class="action-stack">
                        <button
                            id="saveButton"
                            class="btn btn-primary"
                            onclick="saveProfile()"
                        >
                            Create profile
                        </button>

                        <button
                            class="btn"
                            onclick="validateProfile()"
                        >
                            Validate
                        </button>

                        <button
                            class="btn"
                            onclick="window.location.href='/sensor-profile-manager'"
                        >
                            Cancel
                        </button>
                    </div>
                </section>
            </aside>
        </div>
    </main>

    <script>
        const state = {
            profileId: null,
            profile: null,
            isSystem: false,
            catalog: [],
            modules: [],
            fields: [],
            sensors: [],
            rules: []
        };

        async function fetchJson(url, options = {}) {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                },
                ...options
            });

            let payload = null;

            try {
                payload = await response.json();
            } catch (error) {
                payload = {
                    detail: "The server returned an invalid response."
                };
            }

            if (!response.ok) {
                throw new Error(
                    payload.detail
                    || payload.message
                    || "Request failed"
                );
            }

            return payload;
        }

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function showMessage(message, type = "success") {
            const element = document.getElementById("message");

            element.textContent = message;
            element.className = `message ${type} show`;

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        }

        function clearMessage() {
            const element = document.getElementById("message");
            element.className = "message";
            element.textContent = "";
        }

        function numberOrNull(value) {
            if (
                value === null
                || value === undefined
                || String(value).trim() === ""
            ) {
                return null;
            }

            const number = Number(value);

            return Number.isFinite(number)
                ? number
                : null;
        }

        function parseJson(value, fieldName) {
            try {
                return JSON.parse(value || "{}");
            } catch (error) {
                throw new Error(
                    `${fieldName} contains invalid JSON.`
                );
            }
        }

        function sensorOptions(selectedValue) {
            return state.catalog.map(sensor => `
                <option
                    value="${escapeHtml(sensor.sensor_code)}"
                    ${
                        sensor.sensor_code === selectedValue
                        ? "selected"
                        : ""
                    }
                >
                    ${escapeHtml(sensor.sensor_code)}
                    — ${escapeHtml(sensor.model)}
                </option>
            `).join("");
        }

        function moduleOptions(selectedValue) {
            return state.modules.map(module => `
                <option
                    value="${escapeHtml(module.module_key)}"
                    ${
                        module.module_key === selectedValue
                        ? "selected"
                        : ""
                    }
                >
                    ${escapeHtml(module.module_key)}
                    — ${escapeHtml(module.display_name)}
                </option>
            `).join("");
        }

        function fieldKeyOptions(selectedValue) {
            return state.fields.map(field => `
                <option
                    value="${escapeHtml(field.field_key)}"
                    ${
                        field.field_key === selectedValue
                        ? "selected"
                        : ""
                    }
                >
                    ${escapeHtml(
                        field.field_key || "Unnamed field"
                    )}
                </option>
            `).join("");
        }

        function addSensor(sensor = null) {
            const defaultSensor = state.catalog[0];
            const defaultModule = state.modules[0];

            state.sensors.push({
                sensor_code:
                    sensor?.sensor_code
                    || defaultSensor?.sensor_code
                    || "",
                module_key:
                    sensor?.module_key
                    || defaultModule?.module_key
                    || "",
                role: sensor?.role || "primary",
                required: sensor?.required ?? true,
                configuration_text: JSON.stringify(
                    sensor?.configuration || {},
                    null,
                    2
                ),
                display_order:
                    sensor?.display_order
                    || state.sensors.length + 1
            });

            renderSensors();
            updateSummary();
        }

        function removeSensor(index) {
            state.sensors.splice(index, 1);
            renderSensors();
            updateSummary();
        }

        function updateSensor(index, key, value) {
            if (key === "required") {
                state.sensors[index][key] = Boolean(value);
            } else {
                state.sensors[index][key] = value;
            }
        }

        function renderSensors() {
            const list = document.getElementById("sensorList");

            if (!state.sensors.length) {
                list.innerHTML = `
                    <div class="empty-state">
                        No sensor components. Add at least one sensor.
                    </div>
                `;
                return;
            }

            list.innerHTML = state.sensors.map(
                (sensor, index) => `
                    <div class="item-card">
                        <div class="item-heading">
                            <strong>
                                Sensor component ${index + 1}
                            </strong>

                            <button
                                class="btn btn-small btn-danger"
                                onclick="removeSensor(${index})"
                            >
                                Remove
                            </button>
                        </div>

                        <div class="form-grid">
                            <div class="form-group">
                                <label class="label">
                                    Sensor
                                </label>

                                <select
                                    class="control"
                                    onchange="
                                        updateSensor(
                                            ${index},
                                            'sensor_code',
                                            this.value
                                        )
                                    "
                                >
                                    ${sensorOptions(sensor.sensor_code)}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Firmware module
                                </label>

                                <select
                                    class="control"
                                    onchange="
                                        updateSensor(
                                            ${index},
                                            'module_key',
                                            this.value
                                        )
                                    "
                                >
                                    ${moduleOptions(sensor.module_key)}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">Role</label>

                                <input
                                    class="control"
                                    value="${escapeHtml(sensor.role)}"
                                    onchange="
                                        updateSensor(
                                            ${index},
                                            'role',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Required</label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${sensor.required ? "checked" : ""}
                                        onchange="
                                            updateSensor(
                                                ${index},
                                                'required',
                                                this.checked
                                            )
                                        "
                                    >
                                    Required component
                                </label>
                            </div>

                            <div class="form-group full">
                                <label class="label">
                                    Sensor configuration
                                </label>

                                <textarea
                                    class="control"
                                    onchange="
                                        updateSensor(
                                            ${index},
                                            'configuration_text',
                                            this.value
                                        )
                                    "
                                >${escapeHtml(
                                    sensor.configuration_text
                                )}</textarea>
                            </div>
                        </div>
                    </div>
                `
            ).join("");
        }

        function addField(field = null) {
            state.fields.push({
                field_key:
                    field?.field_key
                    || `field_${state.fields.length + 1}`,
                label:
                    field?.label
                    || `Field ${state.fields.length + 1}`,
                unit: field?.unit || "",
                data_type: field?.data_type || "number",
                payload_order:
                    field?.payload_order
                    || state.fields.length + 1,
                byte_offset:
                    field?.byte_offset ?? 0,
                byte_length:
                    field?.byte_length ?? 2,
                scale:
                    field?.scale ?? 1,
                signed:
                    field?.signed ?? false,
                required:
                    field?.required ?? true,
                nullable:
                    field?.nullable ?? false,
                display_order:
                    field?.display_order
                    || state.fields.length + 1,
                precision_digits:
                    field?.precision_digits ?? 2,
                visible_floor:
                    field?.visible_floor ?? true,
                visible_dashboard:
                    field?.visible_dashboard ?? true,
                min_value:
                    field?.min_value ?? null,
                max_value:
                    field?.max_value ?? null
            });

            renderFields();
            renderRules();
            updateSummary();
        }

        function removeField(index) {
            state.fields.splice(index, 1);
            renderFields();
            renderRules();
            updateSummary();
        }

        function updateField(index, key, value) {
            const booleanKeys = new Set([
                "signed",
                "required",
                "nullable",
                "visible_floor",
                "visible_dashboard"
            ]);

            if (booleanKeys.has(key)) {
                state.fields[index][key] = Boolean(value);
            } else {
                state.fields[index][key] = value;
            }

            if (key === "field_key") {
                renderRules();
            }
        }

        function renderFields() {
            const list = document.getElementById("fieldList");

            if (!state.fields.length) {
                list.innerHTML = `
                    <div class="empty-state">
                        No fields. Add at least one telemetry field.
                    </div>
                `;
                return;
            }

            list.innerHTML = state.fields.map(
                (field, index) => `
                    <div class="item-card">
                        <div class="item-heading">
                            <strong>
                                Field ${index + 1}:
                                ${escapeHtml(field.field_key)}
                            </strong>

                            <button
                                class="btn btn-small btn-danger"
                                onclick="removeField(${index})"
                            >
                                Remove
                            </button>
                        </div>

                        <div class="form-grid-three">
                            <div class="form-group">
                                <label class="label">
                                    Field key
                                </label>

                                <input
                                    class="control"
                                    value="${escapeHtml(field.field_key)}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'field_key',
                                            this.value.trim().toLowerCase()
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Label</label>

                                <input
                                    class="control"
                                    value="${escapeHtml(field.label)}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'label',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Unit</label>

                                <input
                                    class="control"
                                    value="${escapeHtml(field.unit)}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'unit',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Data type
                                </label>

                                <select
                                    class="control"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'data_type',
                                            this.value
                                        )
                                    "
                                >
                                    ${[
                                        "number",
                                        "integer",
                                        "boolean",
                                        "string"
                                    ].map(type => `
                                        <option
                                            value="${type}"
                                            ${
                                                type === field.data_type
                                                ? "selected"
                                                : ""
                                            }
                                        >
                                            ${type}
                                        </option>
                                    `).join("")}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Byte offset
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    min="0"
                                    value="${field.byte_offset ?? ""}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'byte_offset',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Byte length
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    min="1"
                                    value="${field.byte_length ?? ""}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'byte_length',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Scale</label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    value="${field.scale ?? 1}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'scale',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Minimum value
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    value="${field.min_value ?? ""}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'min_value',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Maximum value
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    value="${field.max_value ?? ""}"
                                    onchange="
                                        updateField(
                                            ${index},
                                            'max_value',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Signed</label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${field.signed ? "checked" : ""}
                                        onchange="
                                            updateField(
                                                ${index},
                                                'signed',
                                                this.checked
                                            )
                                        "
                                    >
                                    Signed numeric value
                                </label>
                            </div>

                            <div class="form-group">
                                <label class="label">Required</label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${field.required ? "checked" : ""}
                                        onchange="
                                            updateField(
                                                ${index},
                                                'required',
                                                this.checked
                                            )
                                        "
                                    >
                                    Required telemetry
                                </label>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Floor visibility
                                </label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${
                                            field.visible_floor
                                            ? "checked"
                                            : ""
                                        }
                                        onchange="
                                            updateField(
                                                ${index},
                                                'visible_floor',
                                                this.checked
                                            )
                                        "
                                    >
                                    Show in Floor Live View
                                </label>
                            </div>
                        </div>
                    </div>
                `
            ).join("");
        }

        function addRule(rule = null) {
            state.rules.push({
                rule_code:
                    rule?.rule_code
                    || `RULE_${state.rules.length + 1}`,
                field_key:
                    rule?.field_key
                    || state.fields[0]?.field_key
                    || "",
                operator: rule?.operator || ">",
                threshold_value:
                    rule?.threshold_value ?? null,
                threshold_value_2:
                    rule?.threshold_value_2 ?? null,
                expected_boolean:
                    rule?.expected_boolean ?? null,
                expected_text:
                    rule?.expected_text ?? "",
                severity:
                    rule?.severity || "warning",
                alarm_type:
                    rule?.alarm_type
                    || document.getElementById("nodeType").value
                    || "sensor",
                message_template:
                    rule?.message_template
                    || "Alarm condition detected",
                debounce_seconds:
                    rule?.debounce_seconds ?? 0,
                cooldown_seconds:
                    rule?.cooldown_seconds ?? 300,
                auto_resolve:
                    rule?.auto_resolve ?? true,
                enabled:
                    rule?.enabled ?? true
            });

            renderRules();
            updateSummary();
        }

        function removeRule(index) {
            state.rules.splice(index, 1);
            renderRules();
            updateSummary();
        }

        function updateRule(index, key, value) {
            const booleanKeys = new Set([
                "auto_resolve",
                "enabled"
            ]);

            if (booleanKeys.has(key)) {
                state.rules[index][key] = Boolean(value);
            } else {
                state.rules[index][key] = value;
            }
        }

        function renderRules() {
            const list = document.getElementById("ruleList");

            if (!state.rules.length) {
                list.innerHTML = `
                    <div class="empty-state">
                        No alarm rules. Rules are optional.
                    </div>
                `;
                return;
            }

            list.innerHTML = state.rules.map(
                (rule, index) => `
                    <div class="item-card">
                        <div class="item-heading">
                            <strong>
                                ${escapeHtml(rule.rule_code)}
                            </strong>

                            <button
                                class="btn btn-small btn-danger"
                                onclick="removeRule(${index})"
                            >
                                Remove
                            </button>
                        </div>

                        <div class="form-grid-three">
                            <div class="form-group">
                                <label class="label">
                                    Rule code
                                </label>

                                <input
                                    class="control"
                                    value="${escapeHtml(rule.rule_code)}"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'rule_code',
                                            this.value.trim().toUpperCase()
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Telemetry field
                                </label>

                                <select
                                    class="control"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'field_key',
                                            this.value
                                        )
                                    "
                                >
                                    ${fieldKeyOptions(rule.field_key)}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">Operator</label>

                                <select
                                    class="control"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'operator',
                                            this.value
                                        )
                                    "
                                >
                                    ${[
                                        ">",
                                        ">=",
                                        "<",
                                        "<=",
                                        "==",
                                        "!=",
                                        "between",
                                        "outside",
                                        "contains"
                                    ].map(operator => `
                                        <option
                                            value="${operator}"
                                            ${
                                                operator === rule.operator
                                                ? "selected"
                                                : ""
                                            }
                                        >
                                            ${escapeHtml(operator)}
                                        </option>
                                    `).join("")}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Threshold
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    value="${
                                        rule.threshold_value ?? ""
                                    }"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'threshold_value',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Second threshold
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    step="any"
                                    value="${
                                        rule.threshold_value_2 ?? ""
                                    }"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'threshold_value_2',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Expected Boolean
                                </label>

                                <select
                                    class="control"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'expected_boolean',
                                            this.value
                                        )
                                    "
                                >
                                    <option value="">Not used</option>

                                    <option
                                        value="true"
                                        ${
                                            rule.expected_boolean === true
                                            ? "selected"
                                            : ""
                                        }
                                    >
                                        True
                                    </option>

                                    <option
                                        value="false"
                                        ${
                                            rule.expected_boolean === false
                                            ? "selected"
                                            : ""
                                        }
                                    >
                                        False
                                    </option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Expected text
                                </label>

                                <input
                                    class="control"
                                    value="${escapeHtml(
                                        rule.expected_text || ""
                                    )}"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'expected_text',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">Severity</label>

                                <select
                                    class="control"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'severity',
                                            this.value
                                        )
                                    "
                                >
                                    ${[
                                        "info",
                                        "warning",
                                        "critical"
                                    ].map(severity => `
                                        <option
                                            value="${severity}"
                                            ${
                                                severity === rule.severity
                                                ? "selected"
                                                : ""
                                            }
                                        >
                                            ${severity}
                                        </option>
                                    `).join("")}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Alarm type
                                </label>

                                <input
                                    class="control"
                                    value="${escapeHtml(rule.alarm_type)}"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'alarm_type',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group full">
                                <label class="label">
                                    Alarm message
                                </label>

                                <input
                                    class="control"
                                    value="${escapeHtml(
                                        rule.message_template
                                    )}"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'message_template',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Cooldown seconds
                                </label>

                                <input
                                    class="control"
                                    type="number"
                                    min="0"
                                    value="${rule.cooldown_seconds}"
                                    onchange="
                                        updateRule(
                                            ${index},
                                            'cooldown_seconds',
                                            this.value
                                        )
                                    "
                                >
                            </div>

                            <div class="form-group">
                                <label class="label">
                                    Auto resolve
                                </label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${
                                            rule.auto_resolve
                                            ? "checked"
                                            : ""
                                        }
                                        onchange="
                                            updateRule(
                                                ${index},
                                                'auto_resolve',
                                                this.checked
                                            )
                                        "
                                    >
                                    Resolve automatically
                                </label>
                            </div>

                            <div class="form-group">
                                <label class="label">Enabled</label>

                                <label class="checkbox-row">
                                    <input
                                        type="checkbox"
                                        ${rule.enabled ? "checked" : ""}
                                        onchange="
                                            updateRule(
                                                ${index},
                                                'enabled',
                                                this.checked
                                            )
                                        "
                                    >
                                    Rule enabled
                                </label>
                            </div>
                        </div>
                    </div>
                `
            ).join("");
        }

        function collectProfileDefinition() {
            const sensors = state.sensors.map(
                (sensor, index) => ({
                    sensor_code:
                        sensor.sensor_code.trim().toUpperCase(),
                    module_key:
                        sensor.module_key.trim().toLowerCase(),
                    role:
                        sensor.role.trim().toLowerCase(),
                    required: Boolean(sensor.required),
                    configuration: parseJson(
                        sensor.configuration_text,
                        `Sensor ${index + 1} configuration`
                    ),
                    display_order: index + 1
                })
            );

            const fields = state.fields.map(
                (field, index) => ({
                    field_key:
                        String(field.field_key)
                        .trim()
                        .toLowerCase(),
                    label: String(field.label).trim(),
                    unit:
                        String(field.unit || "").trim()
                        || null,
                    data_type: field.data_type,
                    payload_order: index + 1,
                    byte_offset:
                        numberOrNull(field.byte_offset),
                    byte_length:
                        numberOrNull(field.byte_length),
                    scale:
                        numberOrNull(field.scale) ?? 1,
                    signed: Boolean(field.signed),
                    endianness: "big",
                    required: Boolean(field.required),
                    nullable: Boolean(field.nullable),
                    display_order: index + 1,
                    precision_digits:
                        numberOrNull(
                            field.precision_digits
                        ),
                    visible_floor:
                        Boolean(field.visible_floor),
                    visible_dashboard:
                        Boolean(field.visible_dashboard),
                    min_value:
                        numberOrNull(field.min_value),
                    max_value:
                        numberOrNull(field.max_value),
                    default_value: null
                })
            );

            const rules = state.rules.map(rule => {
                let expectedBoolean = null;

                if (rule.expected_boolean === true) {
                    expectedBoolean = true;
                } else if (
                    rule.expected_boolean === false
                ) {
                    expectedBoolean = false;
                } else if (
                    rule.expected_boolean === "true"
                ) {
                    expectedBoolean = true;
                } else if (
                    rule.expected_boolean === "false"
                ) {
                    expectedBoolean = false;
                }

                return {
                    rule_code:
                        String(rule.rule_code)
                        .trim()
                        .toUpperCase(),
                    field_key:
                        String(rule.field_key)
                        .trim()
                        .toLowerCase(),
                    operator: rule.operator,
                    threshold_value:
                        numberOrNull(rule.threshold_value),
                    threshold_value_2:
                        numberOrNull(rule.threshold_value_2),
                    expected_boolean: expectedBoolean,
                    expected_text:
                        String(rule.expected_text || "").trim()
                        || null,
                    severity: rule.severity,
                    alarm_type:
                        String(rule.alarm_type)
                        .trim()
                        .toLowerCase(),
                    message_template:
                        String(rule.message_template).trim(),
                    debounce_seconds:
                        numberOrNull(
                            rule.debounce_seconds
                        ) ?? 0,
                    cooldown_seconds:
                        numberOrNull(
                            rule.cooldown_seconds
                        ) ?? 300,
                    auto_resolve:
                        Boolean(rule.auto_resolve),
                    enabled: Boolean(rule.enabled)
                };
            });

            const definition = {
                profile_code:
                    document.getElementById(
                        "profileCode"
                    ).value.trim().toUpperCase(),

                profile_name:
                    document.getElementById(
                        "profileName"
                    ).value.trim(),

                node_type:
                    document.getElementById(
                        "nodeType"
                    ).value.trim().toLowerCase(),

                description:
                    document.getElementById(
                        "description"
                    ).value.trim(),

                capabilities:
                    document.getElementById(
                        "capabilities"
                    ).value
                    .split(",")
                    .map(value => value.trim().toLowerCase())
                    .filter(Boolean),

                configuration_schema: parseJson(
                    document.getElementById(
                        "configurationSchema"
                    ).value,
                    "Configuration schema"
                ),

                payload_encoder_key:
                    document.getElementById(
                        "payloadEncoderKey"
                    ).value.trim().toLowerCase(),

                payload_version:
                    Number(
                        document.getElementById(
                            "payloadVersion"
                        ).value
                    ),

                f_port:
                    Number(
                        document.getElementById(
                            "fPort"
                        ).value
                    ),

                uplink_interval_seconds:
                    Number(
                        document.getElementById(
                            "uplinkInterval"
                        ).value
                    ),

                ttn_formatter_code:
                    document.getElementById(
                        "formatterCode"
                    ).value,

                ttn_formatter_type:
                    document.getElementById(
                        "formatterType"
                    ).value,

                tb_device_profile_name:
                    document.getElementById(
                        "tbProfileName"
                    ).value.trim()
                    || null,

                icon_type:
                    document.getElementById(
                        "iconType"
                    ).value.trim().toLowerCase()
                    || "default",

                icon_color:
                    document.getElementById(
                        "iconColor"
                    ).value,

                status:
                    document.getElementById(
                        "profileStatus"
                    ).value,

                enabled:
                    document.getElementById(
                        "profileEnabled"
                    ).checked,

                fields,
                sensors,
                rules
            };

            if (state.profileId) {
                definition.id = state.profileId;
                definition.profile_version =
                    state.profile?.profile_version || 1;
            }

            const changeNote = document.getElementById(
                "changeNote"
            ).value.trim();

            if (changeNote) {
                definition.change_note = changeNote;
            }

            return definition;
        }

        async function validateProfile(showSuccess = true) {
            clearMessage();

            try {
                const definition =
                    collectProfileDefinition();

                const result = await fetchJson(
                    "/sensor-profiles/validate",
                    {
                        method: "POST",
                        body: JSON.stringify(definition)
                    }
                );

                if (!result.valid) {
                    showMessage(
                        result.errors
                            .map(error => `• ${error}`)
                            .join("\n"),
                        "error"
                    );

                    return false;
                }

                if (showSuccess) {
                    showMessage(
                        "Profile validation passed successfully.",
                        "success"
                    );
                }

                return true;

            } catch (error) {
                showMessage(error.message, "error");
                return false;
            }
        }

        async function saveProfile() {
            if (state.isSystem) {
                showMessage(
                    "System profiles cannot be edited. "
                    + "Clone the profile first.",
                    "error"
                );
                return;
            }

            const saveButton = document.getElementById(
                "saveButton"
            );

            saveButton.disabled = true;
            saveButton.textContent = "Saving...";

            try {
                const valid = await validateProfile(false);

                if (!valid) {
                    return;
                }

                const definition =
                    collectProfileDefinition();

                const url = state.profileId
                    ? `/sensor-profiles/${state.profileId}`
                    : "/sensor-profiles";

                const method = state.profileId
                    ? "PUT"
                    : "POST";

                const result = await fetchJson(
                    url,
                    {
                        method,
                        body: JSON.stringify(definition)
                    }
                );

                showMessage(
                    state.profileId
                    ? "Profile updated successfully."
                    : "Profile created successfully.",
                    "success"
                );

                setTimeout(() => {
                    window.location.href =
                        "/sensor-profile-manager";
                }, 850);

            } catch (error) {
                showMessage(error.message, "error");

            } finally {
                saveButton.disabled = false;
                saveButton.textContent = state.profileId
                    ? "Update profile"
                    : "Create profile";
            }
        }

        function updateSummary() {
            document.getElementById(
                "summaryFields"
            ).textContent = state.fields.length;

            document.getElementById(
                "summaryRules"
            ).textContent = state.rules.length;

            document.getElementById(
                "summarySensors"
            ).textContent = state.sensors.length;

            document.getElementById(
                "summaryVersion"
            ).textContent = (
                state.profile?.profile_version || 1
            );
        }

        function fillGeneralForm(profile) {
            document.getElementById(
                "profileCode"
            ).value = profile.profile_code || "";

            document.getElementById(
                "profileName"
            ).value = profile.profile_name || "";

            document.getElementById(
                "nodeType"
            ).value = profile.node_type || "";

            document.getElementById(
                "description"
            ).value = profile.description || "";

            document.getElementById(
                "capabilities"
            ).value = (
                profile.capabilities || []
            ).join(", ");

            document.getElementById(
                "profileStatus"
            ).value = profile.status || "draft";

            document.getElementById(
                "profileEnabled"
            ).checked = Boolean(
                profile.enabled
            );

            document.getElementById(
                "iconType"
            ).value = profile.icon_type || "default";

            document.getElementById(
                "iconColor"
            ).value = (
                profile.icon_color
                || "#3b82f6"
            );

            document.getElementById(
                "payloadEncoderKey"
            ).value = (
                profile.payload_encoder_key || ""
            );

            document.getElementById(
                "payloadVersion"
            ).value = profile.payload_version || 1;

            document.getElementById(
                "fPort"
            ).value = profile.f_port || 1;

            document.getElementById(
                "uplinkInterval"
            ).value = (
                profile.uplink_interval_seconds || 60
            );

            document.getElementById(
                "tbProfileName"
            ).value = (
                profile.tb_device_profile_name || ""
            );

            document.getElementById(
                "formatterType"
            ).value = (
                profile.ttn_formatter_type || "javascript"
            );

            document.getElementById(
                "formatterCode"
            ).value = (
                profile.ttn_formatter_code || ""
            );

            document.getElementById(
                "configurationSchema"
            ).value = JSON.stringify(
                profile.configuration_schema || {},
                null,
                2
            );
        }

        function mapLoadedProfile(profile) {
            state.fields = (profile.fields || []).map(
                field => ({
                    ...field,
                    unit: field.unit || ""
                })
            );

            state.sensors = (profile.sensors || []).map(
                sensor => ({
                    sensor_code: sensor.sensor_code,
                    module_key: sensor.module_key,
                    role: sensor.role,
                    required: Boolean(sensor.required),
                    configuration_text: JSON.stringify(
                        sensor.configuration || {},
                        null,
                        2
                    ),
                    display_order:
                        sensor.display_order || 1
                })
            );

            state.rules = (profile.rules || []).map(
                rule => ({
                    ...rule,
                    expected_text:
                        rule.expected_text || ""
                })
            );
        }

        async function initializeEditor() {
            try {
                const query = new URLSearchParams(
                    window.location.search
                );

                const profileId = query.get("profile_id");

                const [
                    catalogResult,
                    modulesResult
                ] = await Promise.all([
                    fetchJson(
                        "/sensor-catalog?include_disabled=false"
                    ),
                    fetchJson(
                        "/firmware-modules?include_disabled=false"
                    )
                ]);

                state.catalog = catalogResult.sensors || [];
                state.modules = modulesResult.modules || [];

                if (profileId) {
                    state.profileId = Number(profileId);

                    const result = await fetchJson(
                        `/sensor-profiles/${state.profileId}`
                        + "?include_formatter=true"
                    );

                    state.profile = result.profile;
                    state.isSystem = Boolean(
                        result.profile.is_system
                    );

                    document.getElementById(
                        "pageTitle"
                    ).textContent = (
                        `Edit ${result.profile.profile_name}`
                    );

                    document.getElementById(
                        "summaryMode"
                    ).textContent = "Edit";

                    document.getElementById(
                        "saveButton"
                    ).textContent = "Update profile";

                    document.getElementById(
                        "profileCode"
                    ).readOnly = true;

                    fillGeneralForm(result.profile);
                    mapLoadedProfile(result.profile);

                    if (state.isSystem) {
                        document.getElementById(
                            "systemWarning"
                        ).classList.add("show");

                        document.getElementById(
                            "saveButton"
                        ).disabled = true;
                    }

                } else {
                    document.getElementById(
                        "summaryMode"
                    ).textContent = "Create";

                    addSensor();
                    addField();
                }

                renderSensors();
                renderFields();
                renderRules();
                updateSummary();

            } catch (error) {
                showMessage(
                    "Could not initialize the profile editor: "
                    + error.message,
                    "error"
                );
            }
        }

        document.addEventListener(
            "DOMContentLoaded",
            initializeEditor
        );
    </script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/admin/provision-options", response_class=HTMLResponse)
def admin_provision_options_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Node Provisioning Options</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
        }

        .header {
            padding: 24px 34px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 30px;
            color: #f8fafc;
        }

        .header p {
            margin: 8px 0 0;
            color: #94a3b8;
            line-height: 1.5;
        }

        .toolbar {
            padding: 16px 34px;
            background: #0f172a;
            border-bottom: 1px solid #1e293b;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        button {
            padding: 10px 14px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: bold;
            color: white;
            background: #2563eb;
        }

        button:hover {
            background: #1d4ed8;
        }

        .admin-btn {
            background: #334155;
        }

        .admin-btn:hover {
            background: #475569;
        }

        .json-btn {
            background: #64748b;
        }

        .json-btn:hover {
            background: #475569;
        }

        .container {
            padding: 24px 34px 34px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }

        .summary-card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.28);
        }

        .summary-card .label {
            color: #94a3b8;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .summary-card .value {
            margin-top: 10px;
            font-size: 34px;
            font-weight: bold;
            color: #f8fafc;
        }

        .summary-card .hint {
            margin-top: 6px;
            color: #94a3b8;
            font-size: 13px;
        }

        .card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.28);
            margin-bottom: 22px;
        }

        h2 {
            margin-top: 0;
            color: #f8fafc;
            font-size: 22px;
        }

        .muted {
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.5;
        }

        .node-types {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 14px;
        }

        .node-type {
            padding: 8px 12px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 999px;
            color: #93c5fd;
            font-weight: bold;
            font-size: 13px;
        }

        .building {
            margin-top: 16px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 14px;
            overflow: hidden;
        }

        .building-header {
            padding: 15px 16px;
            background: #1e293b;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }

        .building-title {
            font-size: 18px;
            font-weight: bold;
            color: #f8fafc;
        }

        .building-count {
            color: #93c5fd;
            font-size: 13px;
            font-weight: bold;
        }

        .floor {
            padding: 14px 16px;
            border-bottom: 1px solid #1e293b;
        }

        .floor:last-child {
            border-bottom: none;
        }

        .floor-title {
            color: #cbd5e1;
            font-weight: bold;
            margin-bottom: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border-radius: 10px;
            font-size: 14px;
        }

        th, td {
            padding: 11px 12px;
            border-bottom: 1px solid #334155;
            text-align: left;
            vertical-align: top;
        }

        th {
            background: #0f172a;
            color: #93c5fd;
        }

        tr:hover {
            background: #1e293b;
        }

        .room-badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #1e3a8a;
            color: #bfdbfe;
            font-weight: bold;
            font-size: 12px;
        }

        .id-badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #14532d;
            color: #bbf7d0;
            font-weight: bold;
            font-size: 12px;
        }

        .coord {
            color: #cbd5e1;
            font-family: Consolas, monospace;
            font-size: 13px;
        }

        .empty {
            padding: 18px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 12px;
            color: #94a3b8;
        }

        pre {
            display: none;
            white-space: pre-wrap;
            word-break: break-word;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 16px;
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.5;
            max-height: 420px;
            overflow: auto;
        }

        .loading {
            padding: 20px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 12px;
            color: #94a3b8;
        }

        .error {
            padding: 18px;
            background: #7f1d1d;
            border: 1px solid #ef4444;
            border-radius: 12px;
            color: #fecaca;
        }

        @media(max-width: 1000px) {
            .summary-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media(max-width: 700px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }

            .header,
            .toolbar,
            .container {
                padding-left: 18px;
                padding-right: 18px;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Node Provisioning Options</h1>
    <p>
        Admin-readable view of the node types, buildings, floors, rooms, and room IDs sent to LILYGO during node provisioning.
    </p>
</div>

<div class="toolbar">
    <button class="admin-btn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>

    <button onclick="loadProvisionOptions()">
        Refresh
    </button>

    <button class="json-btn" onclick="toggleRawJson()">
        Show / Hide Raw JSON
    </button>
    
    <button class="admin-btn" style="background:#10b981;" onclick="openBulkImport()">
        Bulk Import CSV
    </button>
</div>

<div class="container">

    <div class="summary-grid">
        <div class="summary-card">
            <div class="label">Node Types</div>
            <div class="value" id="nodeTypeCount">--</div>
            <div class="hint">Available LILYGO firmware profiles</div>
        </div>

        <div class="summary-card">
            <div class="label">Buildings</div>
            <div class="value" id="buildingCount">--</div>
            <div class="hint">Provisionable building names</div>
        </div>

        <div class="summary-card">
            <div class="label">Floors</div>
            <div class="value" id="floorCount">--</div>
            <div class="hint">Floors with rooms configured</div>
        </div>

        <div class="summary-card">
            <div class="label">Rooms</div>
            <div class="value" id="roomCount">--</div>
            <div class="hint">Rooms with room_id values</div>
        </div>
    </div>

    <div class="card">
        <h2>Available Node Types</h2>
        <div class="muted">
            These are the node profiles the LILYGO can register as.
        </div>
        <div id="nodeTypes" class="node-types">
            Loading...
        </div>
    </div>

    <div class="card">
        <h2>Provisioning Hierarchy</h2>
        <div class="muted">
            The room_id is the most important value for new node assignment. LILYGO should send the selected room_id during provisioning.
        </div>

        <div id="hierarchy">
            <div class="loading">Loading provisioning options...</div>
        </div>
    </div>

    <div class="card">
        <h2>Raw API Data</h2>
        <div class="muted">
            This is the original JSON still used by the LILYGO provisioning flow.
        </div>
        <pre id="rawJson"></pre>
    </div>

</div>

<script>
let latestData = null;

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function countProvisionData(data) {
    const buildings = data.buildings || {};

    let buildingCount = 0;
    let floorCount = 0;
    let roomCount = 0;

    Object.entries(buildings).forEach(([buildingName, floors]) => {
        buildingCount += 1;

        Object.entries(floors || {}).forEach(([floorName, rooms]) => {
            floorCount += 1;
            roomCount += Object.keys(rooms || {}).length;
        });
    });

    return {
        nodeTypeCount: (data.node_types || []).length,
        buildingCount,
        floorCount,
        roomCount
    };
}

function renderNodeTypes(data) {
    const container = document.getElementById("nodeTypes");
    const nodeTypes = data.node_types || [];

    if (nodeTypes.length === 0) {
        container.innerHTML = `<div class="empty">No node types found.</div>`;
        return;
    }

    container.innerHTML = "";

    nodeTypes.forEach(type => {
        container.innerHTML += `
            <span class="node-type">${escapeHtml(type)}</span>
        `;
    });
}

function renderHierarchy(data) {
    const container = document.getElementById("hierarchy");
    const buildings = data.buildings || {};
    const buildingEntries = Object.entries(buildings);

    if (buildingEntries.length === 0) {
        container.innerHTML = `
            <div class="empty">
                No rooms found. Add rooms in Floor Editor first, then refresh this page.
            </div>
        `;
        return;
    }

    let html = "";

    buildingEntries.forEach(([buildingName, floors]) => {
        let buildingRoomCount = 0;

        Object.values(floors || {}).forEach(rooms => {
            buildingRoomCount += Object.keys(rooms || {}).length;
        });

        html += `
            <div class="building">
                <div class="building-header">
                    <div class="building-title">${escapeHtml(buildingName)}</div>
                    <div class="building-count">${buildingRoomCount} room(s)</div>
                </div>
        `;

        Object.entries(floors || {}).forEach(([floorName, rooms]) => {
            const roomEntries = Object.entries(rooms || {});

            html += `
                <div class="floor">
                    <div class="floor-title">
                        ${escapeHtml(floorName)} · ${roomEntries.length} room(s)
                    </div>
            `;

            if (roomEntries.length === 0) {
                html += `<div class="empty">No rooms configured on this floor.</div>`;
            } else {
                html += `
                    <table>
                        <thead>
                            <tr>
                                <th>Room</th>
                                <th>room_id</th>
                                <th>floor_id</th>
                                <th>Default Position</th>
                                <th>LILYGO Meaning</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                roomEntries.forEach(([roomName, room]) => {
                    html += `
                        <tr>
                            <td>
                                <span class="room-badge">${escapeHtml(roomName)}</span>
                            </td>
                            <td>
                                <span class="id-badge">${escapeHtml(room.room_id)}</span>
                            </td>
                            <td>${escapeHtml(room.floor_id || "--")}</td>
                            <td class="coord">
                                x=${escapeHtml(room.x ?? "--")}, y=${escapeHtml(room.y ?? "--")}
                            </td>
                            <td class="muted">
                                New node will be assigned to this room when this room_id is selected.
                            </td>
                        </tr>
                    `;
                });

                html += `
                        </tbody>
                    </table>
                `;
            }

            html += `</div>`;
        });

        html += `</div>`;
    });

    container.innerHTML = html;
}

async function loadProvisionOptions() {
    const hierarchy = document.getElementById("hierarchy");
    hierarchy.innerHTML = `<div class="loading">Loading provisioning options...</div>`;

    try {
        const res = await fetch("/provision-options", {
            headers: {
                "Accept": "application/json"
            }
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to load provisioning options");
        }

        latestData = data;

        const counts = countProvisionData(data);

        document.getElementById("nodeTypeCount").innerText = counts.nodeTypeCount;
        document.getElementById("buildingCount").innerText = counts.buildingCount;
        document.getElementById("floorCount").innerText = counts.floorCount;
        document.getElementById("roomCount").innerText = counts.roomCount;

        renderNodeTypes(data);
        renderHierarchy(data);

        document.getElementById("rawJson").innerText = JSON.stringify(data, null, 2);

    } catch (err) {
        hierarchy.innerHTML = `
            <div class="error">
                ${escapeHtml(err.message)}
            </div>
        `;
    }
}

function toggleRawJson() {
    const raw = document.getElementById("rawJson");

    if (raw.style.display === "block") {
        raw.style.display = "none";
    } else {
        raw.style.display = "block";
    }
}

loadProvisionOptions();
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""
    return HTMLResponse(html)

@router.get("/admin/alarms", response_class=HTMLResponse)
def admin_alarms_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Alarm History</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        .header {
            padding: 24px 34px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 30px;
        }

        .header p {
            margin: 8px 0 0;
            color: #94a3b8;
        }

        .toolbar {
            padding: 20px 34px;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        select, button {
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #334155;
            font-size: 14px;
        }

        select {
            background: #1e293b;
            color: white;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #1d4ed8;
        }

        button.export {
            background: #7c3aed;
        }

        button.export:hover {
            background: #6d28d9;
        }

        button.resolve {
            background: #16a34a;
        }

        button.resolve:hover {
            background: #15803d;
        }

        button.ack {
            background: #f59e0b;
        }

        button.ack:hover {
            background: #d97706;
        }

        .no-action {
            display: inline-block;
            padding: 8px 10px;
            border-radius: 8px;
            background: #334155;
            color: #94a3b8;
            font-size: 13px;
            font-weight: bold;
        }

        .content {
            padding: 0 34px 34px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 14px;
            overflow: hidden;
        }

        th, td {
            padding: 13px;
            border-bottom: 1px solid #334155;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
        }

        th {
            background: #111827;
            color: #cbd5e1;
        }

        tr:hover {
            background: #273449;
        }

        .badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
        }

        .active {
            background: #7f1d1d;
            color: #fecaca;
        }

        .acknowledged {
            background: #78350f;
            color: #fde68a;
        }

        .resolved {
            background: #14532d;
            color: #86efac;
        }

        .muted {
            color: #94a3b8;
            font-size: 13px;
        }

        .error {
            color: #fecaca;
            padding: 20px;
            background: #7f1d1d;
            border-radius: 10px;
        }

        .empty {
            color: #94a3b8;
            padding: 24px;
            background: #1e293b;
            border-radius: 12px;
        }

        .telemetry {
            font-family: monospace;
            font-size: 12px;
            color: #cbd5e1;
            white-space: pre-wrap;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

    <div class="header">
        <h1>Alarm History</h1>
        <p>View active, acknowledged, and resolved alarms from smart building nodes.</p>
    </div>

    <div class="toolbar">
        <label>Status:</label>

        <select id="statusFilter">
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
        </select>

        <button onclick="loadAlarms()">Refresh</button>
        <button class="export" onclick="exportAlarmCsv()">Export CSV</button>
        <button onclick="window.open('/admin', '_self')">Back to Admin Home</button>
    </div>

    <div class="content" id="content">
        Loading alarms.
    </div>

<script>
function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function alarmStatus(alarm) {
    if (alarm.resolved === 1 || alarm.resolved === true) {
        return "resolved";
    }

    if (alarm.acknowledged === 1 || alarm.acknowledged === true) {
        return "acknowledged";
    }

    return "active";
}

function statusBadge(alarm) {
    const status = alarmStatus(alarm);

    return `<span class="badge ${status}">${status.toUpperCase()}</span>`;
}

function buildAlarmExportQuery() {
    const status = document.getElementById("statusFilter").value;
    const query = new URLSearchParams();

    query.set("limit", "5000");

    if (status === "active") {
        query.set("acknowledged", "0");
        query.set("resolved", "0");
    }

    if (status === "acknowledged") {
        query.set("acknowledged", "1");
        query.set("resolved", "0");
    }

    if (status === "resolved") {
        query.set("resolved", "1");
    }

    return query.toString();
}

function exportAlarmCsv() {
    const query = buildAlarmExportQuery();
    window.location.href = "/alarms/export.csv?" + query;
}

async function loadAlarms() {
    const content = document.getElementById("content");
    const status = document.getElementById("statusFilter").value;

    content.innerHTML = "Loading alarms.";

    let url = "/alarms";

    if (status) {
        url += "?status=" + encodeURIComponent(status);
    }

    try {
        const res = await fetch(url);
        const alarms = await res.json();

        if (!res.ok) {
            throw new Error(alarms.detail || "Failed to load alarms");
        }

        if (!alarms.length) {
            content.innerHTML = `<div class="empty">No alarms found for this filter.</div>`;
            return;
        }

        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Alarm</th>
                        <th>Location</th>
                        <th>Device</th>
                        <th>Time</th>
                        <th>Telemetry</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        alarms.forEach(alarm => {
            const status = alarmStatus(alarm);
            const isAck = alarm.acknowledged === 1 || alarm.acknowledged === true;
            const isResolved = alarm.resolved === 1 || alarm.resolved === true;

            let actionButtons = "";

            if (isResolved) {
                actionButtons = `<span class="no-action">No actions needed</span>`;
            } else {
                if (!isAck) {
                    actionButtons += `
                        <button class="ack" onclick="ackAlarm(${alarm.id})">
                            Acknowledge
                        </button>
                        <br><br>
                    `;
                }

                actionButtons += `
                    <button class="resolve" onclick="resolveAlarm(${alarm.id})">
                        Resolve
                    </button>
                `;
            }

            html += `
                <tr>
                    <td>${statusBadge(alarm)}</td>

                    <td>
                        <b>${escapeHtml(alarm.alarm_message)}</b>
                        <div class="muted">${escapeHtml(alarm.alarm_type || "")}</div>
                    </td>

                    <td>
                        ${escapeHtml(alarm.building)}<br>
                        <span class="muted">
                            Floor ${escapeHtml(alarm.floor)} / ${escapeHtml(alarm.room)}
                        </span>
                    </td>

                    <td>
                        ${escapeHtml(alarm.device_id)}<br>
                        <span class="muted">${escapeHtml(alarm.node_type)}</span>
                    </td>

                    <td>
                        Triggered:<br>
                        <span class="muted">${escapeHtml(alarm.triggered_at)}</span><br><br>

                        ${isAck ? `
                            Ack by: ${escapeHtml(alarm.acknowledged_by)}<br>
                            <span class="muted">${escapeHtml(alarm.acknowledged_at)}</span><br><br>
                        ` : ""}

                        ${isResolved ? `
                            Resolved by: ${escapeHtml(alarm.resolved_by)}<br>
                            <span class="muted">${escapeHtml(alarm.resolved_at)}</span>
                        ` : ""}
                    </td>

                    <td>
                        <div class="telemetry">${escapeHtml(JSON.stringify(alarm.telemetry || {}, null, 2))}</div>
                    </td>

                    <td>
                        ${actionButtons}
                    </td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        content.innerHTML = html;

    } catch (err) {
        content.innerHTML = `<div class="error">Error: ${escapeHtml(err.message)}</div>`;
    }
}

async function ackAlarm(id) {
    const name = prompt("Acknowledged by:", "admin");

    if (!name) {
        return;
    }

    const res = await fetch(`/alarms/${id}/acknowledge`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            acknowledged_by: name
        })
    });

    if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to acknowledge alarm");
        return;
    }

    await loadAlarms();
}

async function resolveAlarm(id) {
    const name = prompt("Resolved by:", "admin");

    if (!name) {
        return;
    }

    const res = await fetch(`/alarms/${id}/resolve`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            resolved_by: name
        })
    });

    if (!res.ok) {
        const data = await res.json();
        alert(data.detail || "Failed to resolve alarm");
        return;
    }

    await loadAlarms();
}

document.getElementById("statusFilter").addEventListener("change", loadAlarms);
document.addEventListener("DOMContentLoaded", loadAlarms);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/floorplan-editor", response_class=HTMLResponse)
def floorplan_editor():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Floor Plan Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            font-family: Arial;
            margin: 20px;
            background: #f4f6f8;
        }

        #toolbar {
            background: white;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 12px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        }

        #container {
            position: relative;
            display: inline-block;
            border: 2px solid #333;
            background: white;
        }

        #floorImage {
            max-width: 1000px;
            display: block;
        }

        #overlay {
            position: absolute;
            left: 0;
            top: 0;
            pointer-events: none;
        }

        button, select, input {
            margin: 5px;
            padding: 8px;
        }

        .hint {
            font-size: 13px;
            color: #555;
            margin-top: 8px;
        }

        .legend {
            margin-top: 8px;
            font-size: 13px;
        }

        .box {
            display: inline-block;
            width: 14px;
            height: 14px;
            margin-right: 5px;
            vertical-align: middle;
        }

        .saved-box {
            background: rgba(0, 120, 255, 0.25);
            border: 2px solid #0078ff;
        }

        .new-box {
            background: rgba(255, 0, 0, 0.2);
            border: 2px solid red;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<h2>Floor Plan Room Editor</h2>

<div id="toolbar">

    <label>Floorplan:</label>
    <select id="floorplanSelect"></select>

    <button onclick="clearPoints()">Clear Current Points</button>
    <button onclick="saveRoom()">Save Room</button>

    <br>

    <label>Room Name:</label>
    <input id="roomName" placeholder="Room 101">

    <div class="hint">
        Click at least 3 corners of a NEW room, then press Save Room.
        Blue shaded areas are already saved rooms.
    </div>

    <div class="legend">
        <span class="box saved-box"></span> Saved room area
        &nbsp;&nbsp;
        <span class="box new-box"></span> New room being drawn
    </div>

</div>

<div id="container">
    <img id="floorImage">
    <canvas id="overlay"></canvas>
</div>

<script>
let floorplans = [];
let selectedFloorplan = null;
let points = [];
let savedRooms = [];

async function loadFloorplans() {
    const params = new URLSearchParams(window.location.search);
    const siteId = params.get("site_id");

    const apiUrl = siteId
        ? `/gateways/health?site_id=${siteId}`
        : "/gateways/health";

    const res = await fetch(apiUrl);
    floorplans = await res.json();

    const select = document.getElementById('floorplanSelect');
    select.innerHTML = '';

    floorplans.forEach(fp => {
        const opt = document.createElement('option');
        opt.value = fp.id;
        opt.textContent = fp.building + ' - Floor ' + fp.floor;
        select.appendChild(opt);
    });

    if (floorplans.length > 0) {
        selectedFloorplan = floorplans[0];
        await loadImage(selectedFloorplan);
        await loadSavedRooms();
    }

    select.onchange = async () => {
        selectedFloorplan = floorplans.find(fp => fp.id == select.value);
        points = [];
        await loadImage(selectedFloorplan);
        await loadSavedRooms();
    };
}

async function loadSavedRooms() {
    if (!selectedFloorplan) return;

    const res = await fetch('/rooms?floorplan_id=' + selectedFloorplan.id);
    savedRooms = await res.json();

    draw();
}

function loadImage(fp) {
    return new Promise(resolve => {
        const img = document.getElementById('floorImage');
        img.src = fp.image_path;

        img.onload = () => {
            const canvas = document.getElementById('overlay');
            canvas.width = img.clientWidth;
            canvas.height = img.clientHeight;
            draw();
            resolve();
        };
    });
}

document.getElementById('floorImage').addEventListener('click', function(e) {
    if (!selectedFloorplan) return;

    const rect = this.getBoundingClientRect();

    const displayX = e.clientX - rect.left;
    const displayY = e.clientY - rect.top;

    const originalX = Math.round(displayX * selectedFloorplan.image_width / this.clientWidth);
    const originalY = Math.round(displayY * selectedFloorplan.image_height / this.clientHeight);

    points.push({
        x: originalX,
        y: originalY
    });

    draw();
});

function toDisplayPoint(p, img) {
    return {
        x: p.x * img.clientWidth / selectedFloorplan.image_width,
        y: p.y * img.clientHeight / selectedFloorplan.image_height
    };
}

function drawPolygon(ctx, displayPoints, fillStyle, strokeStyle, lineWidth) {
    if (displayPoints.length === 0) return;

    ctx.beginPath();
    ctx.moveTo(displayPoints[0].x, displayPoints[0].y);

    for (let i = 1; i < displayPoints.length; i++) {
        ctx.lineTo(displayPoints[i].x, displayPoints[i].y);
    }

    if (displayPoints.length >= 3) {
        ctx.closePath();
        ctx.fillStyle = fillStyle;
        ctx.fill();
    }

    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
}

function drawRoomName(ctx, room, displayPoints) {
    if (displayPoints.length === 0) return;

    let sumX = 0;
    let sumY = 0;

    displayPoints.forEach(p => {
        sumX += p.x;
        sumY += p.y;
    });

    const cx = sumX / displayPoints.length;
    const cy = sumY / displayPoints.length;

    ctx.fillStyle = '#003b73';
    ctx.font = 'bold 13px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(room.room_name, cx, cy);
}

function draw() {
    const img = document.getElementById('floorImage');
    const canvas = document.getElementById('overlay');
    const ctx = canvas.getContext('2d');

    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!selectedFloorplan) return;

    // Draw already saved rooms first
    savedRooms.forEach(room => {
        const displayPoints = room.polygon_points.map(p => toDisplayPoint(p, img));

        drawPolygon(
            ctx,
            displayPoints,
            'rgba(0, 120, 255, 0.25)',
            '#0078ff',
            3
        );

        drawRoomName(ctx, room, displayPoints);
    });

    // Draw the new currently clicked polygon
    const newDisplayPoints = points.map(p => toDisplayPoint(p, img));

    drawPolygon(
        ctx,
        newDisplayPoints,
        'rgba(255, 0, 0, 0.2)',
        'red',
        3
    );

    // Draw clicked points
    newDisplayPoints.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'red';
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
}

function clearPoints() {
    points = [];
    draw();
}

async function saveRoom() {
    const roomName = document.getElementById('roomName').value.trim();

    if (!selectedFloorplan) {
        alert('No floorplan selected');
        return;
    }

    if (!roomName) {
        alert('Enter room name');
        return;
    }

    if (points.length < 3) {
        alert('Click at least 3 points');
        return;
    }

    const payload = {
        floorplan_id: selectedFloorplan.id,
        building: selectedFloorplan.building,
        floor: selectedFloorplan.floor,
        room_name: roomName,
        polygon_points: points
    };

    const res = await fetch('/rooms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
        alert('Error: ' + JSON.stringify(data));
        return;
    }

    alert(
        'Room saved: ' +
        data.room_name +
        ' at x=' +
        data.x +
        ', y=' +
        data.y
    );

    points = [];
    document.getElementById('roomName').value = '';

    await loadSavedRooms();
}

loadFloorplans();
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""

@router.get("/alarm-settings-page", response_class=HTMLResponse)
def alarm_settings_page():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Alarm Settings</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body{
            margin:0;
            font-family:Arial, sans-serif;
            background:#0f172a;
            color:#e5e7eb;
        }

        .header{
            padding:24px 34px;
            background:#111827;
            border-bottom:1px solid #334155;
        }

        .header h1{
            margin:0;
            font-size:28px;
            color:#f8fafc;
        }

        .header p{
            margin:8px 0 0;
            color:#94a3b8;
            font-size:15px;
        }

        .toolbar{
            padding:16px 34px;
            background:#0f172a;
            border-bottom:1px solid #1e293b;
            display:flex;
            gap:12px;
            align-items:center;
            flex-wrap:wrap;
        }

        .adminHomeBtn{
            display:inline-block;
            background:#334155;
            color:white;
            border:none;
            border-radius:8px;
            padding:10px 14px;
            cursor:pointer;
            font-weight:bold;
            text-decoration:none;
        }

        .adminHomeBtn:hover{
            background:#475569;
        }

        .container{
            padding:24px 34px 34px;
        }

        .grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:22px;
            align-items:start;
        }

        .card{
            background:#111827;
            border:1px solid #334155;
            border-radius:16px;
            padding:22px;
            box-shadow:0 16px 40px rgba(0,0,0,0.35);
            margin-bottom:22px;
        }

        .login-wrapper{
            max-width:480px;
            margin:40px auto;
        }

        h2{
            margin-top:0;
            color:#f8fafc;
            font-size:22px;
        }

        h3{
            margin-top:0;
            color:#93c5fd;
        }

        p{
            color:#94a3b8;
            line-height:1.5;
        }

        label{
            display:block;
            margin-top:14px;
            margin-bottom:6px;
            color:#cbd5e1;
            font-weight:bold;
            font-size:14px;
        }

        input,
        textarea,
        button{
            width:100%;
            padding:11px 12px;
            margin-top:6px;
            margin-bottom:14px;
            border-radius:8px;
            box-sizing:border-box;
            font-size:14px;
        }

        input,
        textarea{
            background:#020617;
            color:white;
            border:1px solid #334155;
            outline:none;
        }

        input:focus,
        textarea:focus{
            border-color:#60a5fa;
        }

        textarea{
            resize:vertical;
            min-height:250px;
            font-family:Consolas, monospace;
            line-height:1.45;
        }

        button{
            background:#2563eb;
            color:white;
            border:none;
            font-weight:bold;
            cursor:pointer;
        }

        button:hover{
            background:#1d4ed8;
        }

        .success-btn{
            background:#16a34a;
        }

        .success-btn:hover{
            background:#15803d;
        }

        .delete-btn{
            background:#dc2626;
            width:auto;
            margin:0;
            padding:8px 12px;
        }

        .delete-btn:hover{
            background:#b91c1c;
        }

        .recipient{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:12px;
            background:#020617;
            border:1px solid #334155;
            padding:12px;
            border-radius:10px;
            margin-bottom:10px;
        }

        .recipient-left{
            display:flex;
            align-items:center;
            gap:10px;
            min-width:0;
        }

        .recipient-left b{
            color:#e5e7eb;
            word-break:break-all;
        }

        .recipient input[type="checkbox"]{
            width:auto;
            margin:0;
            accent-color:#16a34a;
        }

        .hidden{
            display:none;
        }

        .hint{
            font-size:13px;
            color:#94a3b8;
            line-height:1.6;
            background:#020617;
            border:1px solid #334155;
            border-radius:10px;
            padding:12px;
            margin-top:10px;
        }

        .statusBox{
            display:none;
            margin-top:12px;
            padding:12px;
            border-radius:10px;
            font-size:14px;
        }

        .statusBox.good{
            display:block;
            background:#14532d;
            color:#bbf7d0;
            border:1px solid #22c55e;
        }

        .statusBox.bad{
            display:block;
            background:#7f1d1d;
            color:#fecaca;
            border:1px solid #ef4444;
        }

        .empty{
            padding:14px;
            background:#020617;
            border:1px solid #334155;
            border-radius:10px;
            color:#94a3b8;
        }

        @media(max-width:900px){
            .grid{
                grid-template-columns:1fr;
            }

            .container{
                padding:20px 18px;
            }

            .header{
                padding:22px 18px;
            }

            .toolbar{
                padding:14px 18px;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Alarm Settings</h1>
    <p>Manage alarm email recipients and customize the email template used when alarms are triggered.</p>
</div>

<div class="toolbar">
    <button class="adminHomeBtn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>
</div>

<div class="container">

    <div id="loginCard" class="card login-wrapper">
        <h2>Alarm Settings Access</h2>
        <p>Enter the admin password to unlock alarm email settings.</p>

        <label>Admin Password</label>
        <input type="password" id="adminPassword" placeholder="Enter admin password">

        <button class="success-btn" onclick="unlockPage()">Open Settings</button>

        <div id="loginStatus" class="statusBox"></div>

        <div class="hint">
            This protects alarm email recipients and email template editing.
        </div>
    </div>

    <div id="settingsArea" class="hidden">

        <div class="grid">

            <div class="card">
                <h2>Recipients</h2>
                <p>Add or remove emails that should receive alarm notifications.</p>

                <div id="recipientList">
                    <div class="empty">Unlock settings to load recipients.</div>
                </div>

                <label>Add Recipient Email</label>
                <input type="email" id="newEmail" placeholder="example@gmail.com">

                <button class="success-btn" onclick="addRecipient()">Add Recipient</button>

                <div id="recipientStatus" class="statusBox"></div>
            </div>

            <div class="card">
                <h2>Email Template</h2>
                <p>Customize the subject and body used for alarm notification emails.</p>

                <label>Subject Template</label>
                <input type="text" id="subjectTemplate">

                <label>Body Template</label>
                <textarea id="bodyTemplate" rows="14"></textarea>

                <button onclick="saveTemplate()">Save Template</button>

                <div id="templateStatus" class="statusBox"></div>

                <div class="hint">
                    Available variables:<br>
                    {device_id}, {node_type}, {room}, {alarms}, {telemetry}
                </div>
            </div>

        </div>

    </div>

</div>

<script>
let adminPassword = "";

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showStatus(id, message, good=true) {
    const box = document.getElementById(id);

    if (!box) {
        return;
    }

    box.className = good ? "statusBox good" : "statusBox bad";
    box.innerText = message;
}

function clearStatus(id) {
    const box = document.getElementById(id);

    if (!box) {
        return;
    }

    box.className = "statusBox";
    box.innerText = "";
}

async function unlockPage(){
    adminPassword = document.getElementById("adminPassword").value;

    clearStatus("loginStatus");

    if(!adminPassword){
        showStatus("loginStatus", "Enter admin password first.", false);
        return;
    }

    document.getElementById("loginCard").classList.add("hidden");
    document.getElementById("settingsArea").classList.remove("hidden");

    await loadSettings();
}

async function loadSettings(){
    const recipientList = document.getElementById("recipientList");
    recipientList.innerHTML = `<div class="empty">Loading alarm settings...</div>`;

    try {
        const res = await fetch("/alarm-settings");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to load alarm settings");
        }

        recipientList.innerHTML = "";

        if (!data.recipients || data.recipients.length === 0) {
            recipientList.innerHTML = `<div class="empty">No recipients added yet.</div>`;
        } else {
            data.recipients.forEach(r => {
                const div = document.createElement("div");
                div.className = "recipient";

                div.innerHTML = `
                    <div class="recipient-left">
                        <input type="checkbox" ${r.enabled ? "checked" : ""}
                            onchange="toggleRecipient(${r.id}, this.checked)">
                        <b>${escapeHtml(r.email)}</b>
                    </div>

                    <button class="delete-btn" onclick="deleteRecipient(${r.id})">
                        Delete
                    </button>
                `;

                recipientList.appendChild(div);
            });
        }

        if (data.template) {
            document.getElementById("subjectTemplate").value =
                data.template.subject_template || "";

            document.getElementById("bodyTemplate").value =
                data.template.body_template || "";
        }

    } catch (err) {
        recipientList.innerHTML = `
            <div class="statusBox bad" style="display:block;">
                ${escapeHtml(err.message)}
            </div>
        `;
    }
}

async function addRecipient(){
    const email = document.getElementById("newEmail").value.trim();

    clearStatus("recipientStatus");

    if (!email) {
        showStatus("recipientStatus", "Recipient email is required.", false);
        return;
    }

    const res = await fetch("/alarm-settings/recipients", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            admin_password:adminPassword,
            email:email
        })
    });

    const data = await res.json();

    if(!res.ok){
        showStatus("recipientStatus", data.detail || "Failed to add recipient.", false);
        return;
    }

    document.getElementById("newEmail").value = "";

    showStatus("recipientStatus", "Recipient added successfully.", true);
    await loadSettings();
}

async function deleteRecipient(id){
    if (!confirm("Delete this recipient?")) {
        return;
    }

    clearStatus("recipientStatus");

    const res = await fetch(
        "/alarm-settings/recipients/" + id +
        "?admin_password=" + encodeURIComponent(adminPassword),
        { method:"DELETE" }
    );

    const data = await res.json();

    if(!res.ok){
        showStatus("recipientStatus", data.detail || "Failed to delete recipient.", false);
        return;
    }

    showStatus("recipientStatus", "Recipient deleted.", true);
    await loadSettings();
}

async function toggleRecipient(id, enabled){
    clearStatus("recipientStatus");

    const res = await fetch("/alarm-settings/recipients/" + id + "/enabled", {
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            admin_password:adminPassword,
            enabled:enabled
        })
    });

    const data = await res.json();

    if(!res.ok){
        showStatus("recipientStatus", data.detail || "Failed to update recipient.", false);
        await loadSettings();
        return;
    }

    showStatus("recipientStatus", "Recipient status updated.", true);
}

async function saveTemplate(){
    const subject = document.getElementById("subjectTemplate").value.trim();
    const body = document.getElementById("bodyTemplate").value.trim();

    clearStatus("templateStatus");

    if (!subject || !body) {
        showStatus("templateStatus", "Subject and body template are required.", false);
        return;
    }

    const res = await fetch("/alarm-settings/template", {
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            admin_password:adminPassword,
            subject_template:subject,
            body_template:body
        })
    });

    const data = await res.json();

    if(!res.ok){
        showStatus("templateStatus", data.detail || "Failed to save template.", false);
        return;
    }

    showStatus("templateStatus", "Template updated successfully.", true);
}

document.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !document.getElementById("loginCard").classList.contains("hidden")) {
        unlockPage();
    }
});
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""

@router.get("/client-portal", response_class=HTMLResponse)
def client_portal_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Client Portal</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
        }

        header {
            padding: 22px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        header h1 {
            margin: 0;
            font-size: 26px;
        }

        header p {
            margin: 8px 0 0;
            color: #94a3b8;
        }

        .container {
            padding: 24px 30px;
            display: grid;
            grid-template-columns: 330px 1fr;
            gap: 22px;
        }

        .activity-container {
            padding: 0 30px 30px 30px;
        }

        .card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        }

        h2 {
            margin-top: 0;
            font-size: 19px;
        }

        .muted {
            color: #94a3b8;
            font-size: 13px;
        }

        .tree-client {
            margin-bottom: 18px;
        }

        .tree-title {
            font-weight: bold;
            color: #93c5fd;
            margin-bottom: 8px;
        }

        .tree-site {
            margin-left: 12px;
            margin-bottom: 8px;
            color: #cbd5e1;
        }

        .tree-building {
            margin-left: 24px;
            margin-bottom: 8px;
            color: #d1d5db;
        }

        .floor-btn {
            display: block;
            width: calc(100% - 36px);
            margin-left: 36px;
            margin-top: 6px;
            padding: 9px 10px;
            background: #020617;
            border: 1px solid #334155;
            color: white;
            border-radius: 8px;
            cursor: pointer;
            text-align: left;
        }

        .floor-btn:hover {
            background: #1e293b;
        }

        .floor-btn.active {
            background: #2563eb;
            border-color: #60a5fa;
        }

        .logout-btn {
            background: #dc2626;
            color: white;
            border: none;
            padding: 10px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
        }

        .logout-btn:hover {
            background: #b91c1c;
        }

        .permissions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 14px;
        }

        .perm {
            padding: 7px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: #334155;
            color: #e5e7eb;
        }

        .perm.on {
            background: #166534;
        }

        .perm.off {
            background: #7f1d1d;
        }

        .viewer {
            position: relative;
            display: inline-block;
            max-width: 100%;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
            background: #020617;
        }

        #floorImage {
            display: block;
            max-width: 100%;
            height: auto;
        }

        .node-marker {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #2563eb;
            color: white;
            border: 3px solid white;
            cursor: pointer;
            z-index: 15;
            box-shadow: 0 3px 12px rgba(0,0,0,.4);
            font-size: 15px;
        }

        .gateway-marker {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #64748b;
            color: white;
            border: 3px solid white;
            cursor: pointer;
            z-index: 20;
            box-shadow: 0 3px 12px rgba(0,0,0,.4);
            font-size: 18px;
        }

        .gateway-marker.online {
            background: #16a34a;
        }

        .gateway-marker.offline {
            background: #dc2626;
        }

        .gateway-marker.error {
            background: #f97316;
        }

        .gateway-marker.unknown {
            background: #64748b;
        }

        .details {
            margin-top: 18px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px;
        }

        .details h3 {
            margin-top: 0;
            color: #93c5fd;
        }

        .details p {
            margin: 7px 0;
        }

        .empty {
            padding: 30px;
            color: #94a3b8;
            text-align: center;
        }

        .activity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .activity-title {
            margin: 0;
        }

        .activity-subtitle {
            margin: 6px 0 0 0;
            color: #94a3b8;
            font-size: 14px;
        }

        .refresh-btn {
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            background: #2563eb;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }

        .refresh-btn:hover {
            background: #1d4ed8;
        }

        .activity-item {
            padding: 12px 14px;
            border: 1px solid #334155;
            border-radius: 8px;
            margin-bottom: 10px;
            background: #020617;
        }

        .activity-message {
            font-weight: 700;
            color: #f9fafb;
        }

        .activity-meta {
            margin-top: 6px;
            color: #94a3b8;
            font-size: 13px;
        }

        .activity-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            background: #1e3a8a;
            color: #bfdbfe;
            font-size: 12px;
            font-weight: bold;
        }

        .activity-empty {
            padding: 14px;
            background: #020617;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #94a3b8;
        }

        .activity-error {
            padding: 14px;
            background: #7f1d1d;
            border: 1px solid #ef4444;
            border-radius: 8px;
            color: white;
        }
        .export-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 14px;
            margin-top: 14px;
        }

        .export-card {
        display: block;
        text-decoration: none;
        background: #020617;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        color: #e5e7eb;
        transition: 0.2s;
        cursor: pointer;
    }

    .export-card:hover {
        background: #1e293b;
        border-color: #60a5fa;
        transform: translateY(-2px);
    }

    .export-card h3 {
        margin: 8px 0 6px 0;
        font-size: 17px;
        color: #bfdbfe;
    }

    .export-card p {
        margin: 0;
        color: #94a3b8;
        font-size: 13px;
        line-height: 1.4;
    }

    .export-badge {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        background: #7c3aed;
        color: white;
        font-size: 12px;
        font-weight: bold;
    }

        @media(max-width: 1000px) {
            .container {
                grid-template-columns: 1fr;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
<header>
    <h1>Client Portal</h1>
    <p id="clientSubtitle">Loading allowed sites, buildings, floors, devices, and gateways...</p>
    <button class="refresh-btn" onclick="window.location.href='/logout'">
        Logout
    </button>
</header>

<div class="container">
    <div class="card">
        <h2>Allowed Locations</h2>
        <div id="tree"></div>
    </div>

    <div class="card">
        <h2 id="floorTitle">Select a floor</h2>

        <div class="permissions" id="permissions"></div>

        <div id="viewerArea" class="empty">
            Choose a floor from the left side.
        </div>

        <div class="details" id="detailsBox" style="display:none;"></div>
    </div>
</div>

<div class="activity-container">
    <div class="card">
        <h2 style="margin:0;">Exports</h2>
        <p class="activity-subtitle">
            Download reports for your allowed areas only.
        </p>

        <div class="export-grid">
            <div class="export-card" onclick="exportClientFullStructureCsv()">
                <span class="export-badge">CSV</span>
                <h3>Full Structure Export</h3>
                <p>
                    Export your allowed clients, sites, buildings, floors, rooms, devices, and gateways.
                </p>
            </div>

            <div class="export-card" onclick="exportClientAlarmHistoryCsv()">
                <span class="export-badge">CSV</span>
                <h3>Alarm History Export</h3>
                <p>
                    Export alarm history for your allowed scope. If a floor is selected, only that floor is exported.
                </p>
            </div>
        </div>
    </div>
</div>

<div class="activity-container">
    <div class="card">
        <div class="activity-header">
            <div>
                <h2 class="activity-title">Activity Log</h2>
                <p class="activity-subtitle">
                    Recent alarm and device activity for your allowed areas.
                </p>
            </div>

            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <button class="refresh-btn" onclick="loadClientActivityLog()">
                Refresh
                </button>
            </div>

        <div id="clientActivityLog" style="margin-top:16px;">
            Loading activity...
        </div>
    </div>
</div>

<script>
const params = new URLSearchParams(window.location.search);
const userId = params.get("user_id") || "1";

let structureData = null;
let selectedFloorId = null;
let currentLiveData = null;

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showError(message) {
    document.getElementById("viewerArea").innerHTML = `
        <div class="empty">${escapeHtml(message)}</div>
    `;
}

async function loadStructure() {
    try {
        const res = await fetch(`/client-portal/${userId}/allowed-structure`);

        if (!res.ok) {
            showError("Could not load client access. Check user_id or permissions.");
            return;
        }

        structureData = await res.json();

        document.getElementById("clientSubtitle").innerText =
            `${structureData.user.name} - ${structureData.user.email}`;

        drawTree(structureData.structure);

    } catch (error) {
        showError("Could not load client portal data.");
    }
}

function drawTree(structure) {
    const tree = document.getElementById("tree");
    tree.innerHTML = "";

    if (!structure || structure.length === 0) {
        tree.innerHTML = `<div class="empty">No allowed locations for this user.</div>`;
        return;
    }

    structure.forEach(client => {
        const clientDiv = document.createElement("div");
        clientDiv.className = "tree-client";

        clientDiv.innerHTML = `<div class="tree-title">Client: ${escapeHtml(client.name)}</div>`;

        client.sites.forEach(site => {
            const siteDiv = document.createElement("div");
            siteDiv.className = "tree-site";
            siteDiv.innerHTML = `Site: ${escapeHtml(site.name)}`;

            site.buildings.forEach(building => {
                const buildingDiv = document.createElement("div");
                buildingDiv.className = "tree-building";
                buildingDiv.innerHTML = `Building: ${escapeHtml(building.name)}`;

                building.floors.forEach(floor => {
                    const btn = document.createElement("button");
                    btn.className = "floor-btn";
                    btn.id = "floorBtn_" + floor.id;

                    let floorLabel = floor.name || ("Floor " + floor.floor_number);

                    if (
                        floor.floor_number &&
                        floor.name &&
                        floor.name.toLowerCase() === ("floor " + floor.floor_number).toLowerCase()
                    ) {
                        floorLabel = floor.name;
                    }

                    btn.innerText = floorLabel;
                    btn.onclick = () => loadFloor(floor.id);
                    buildingDiv.appendChild(btn);
                });

                siteDiv.appendChild(buildingDiv);
            });

            clientDiv.appendChild(siteDiv);
        });

        tree.appendChild(clientDiv);
    });
}

function drawPermissions(permissions) {
    const box = document.getElementById("permissions");

    box.innerHTML = `
        <span class="perm on">Level: ${escapeHtml(permissions.access_level)}</span>
        <span class="perm ${permissions.can_view_devices ? "on" : "off"}">Devices</span>
        <span class="perm ${permissions.can_view_gateways ? "on" : "off"}">Gateways</span>
        <span class="perm ${permissions.can_view_alarms ? "on" : "off"}">Alarms</span>
        <span class="perm ${permissions.can_view_telemetry ? "on" : "off"}">Telemetry</span>
        <span class="perm ${permissions.can_manage_email_settings ? "on" : "off"}">Email Settings</span>
    `;
}

async function loadFloor(floorId) {
    selectedFloorId = floorId;

    document.querySelectorAll(".floor-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    const activeBtn = document.getElementById("floorBtn_" + floorId);

    if (activeBtn) {
        activeBtn.classList.add("active");
    }

    const res = await fetch(`/client-portal/${userId}/floors/${floorId}/live`);

    if (!res.ok) {
        showError("You do not have permission to open this floor.");
        return;
    }

    currentLiveData = await res.json();

    document.getElementById("floorTitle").innerText =
        currentLiveData.floor.name || ("Floor " + floorId);

    drawPermissions(currentLiveData.permissions);
    drawFloor();
}

function drawFloor() {
    const floor = currentLiveData.floor;

    if (!floor.image_path) {
        showError("This floor does not have an uploaded image.");
        return;
    }

    document.getElementById("viewerArea").innerHTML = `
        <div class="viewer" id="viewer">
            <img id="floorImage" src="${escapeHtml(floor.image_path)}">
        </div>
    `;

    const img = document.getElementById("floorImage");

    img.onload = function() {
        drawDevices();
        drawGateways();
    };

    img.onerror = function() {
        showError("Could not load floor image: " + floor.image_path);
    };
}

function drawDevices() {
    if (!currentLiveData.permissions.can_view_devices) {
        return;
    }

    const viewer = document.getElementById("viewer");
    const img = document.getElementById("floorImage");
    const floor = currentLiveData.floor;

    currentLiveData.rooms.forEach(room => {
        if (!room.devices) {
            return;
        }

        room.devices.forEach(device => {
            if (device.x === null || device.y === null) {
                return;
            }

            const marker = document.createElement("div");
            marker.className = "node-marker";
            marker.innerHTML = "●";
            marker.title = device.label || device.device_id;

            marker.style.left = (device.x * img.clientWidth / floor.image_width) + "px";
            marker.style.top = (device.y * img.clientHeight / floor.image_height) + "px";

            marker.onclick = async function(event) {
                event.stopPropagation();

                showDetails(`
                    <h3>Device Details</h3>
                    <p><strong>Label:</strong> ${escapeHtml(device.label || "--")}</p>
                    <p><strong>Device ID:</strong> ${escapeHtml(device.device_id)}</p>
                    <p><strong>Type:</strong> ${escapeHtml(device.node_type)}</p>
                    <p><strong>Room:</strong> ${escapeHtml(device.room || room.room_name || "--")}</p>
                    <p><strong>Position:</strong> X ${escapeHtml(device.x)} / Y ${escapeHtml(device.y)}</p>
                    <hr>
                    <p class="muted">Loading telemetry...</p>
                `);

                await loadDeviceTelemetry(device, room);
            };

            viewer.appendChild(marker);
        });
    });
}

async function loadDeviceTelemetry(device, room) {
    const box = document.getElementById("detailsBox");

    let baseHtml = `
        <h3>Device Details</h3>
        <p><strong>Label:</strong> ${escapeHtml(device.label || "--")}</p>
        <p><strong>Device ID:</strong> ${escapeHtml(device.device_id)}</p>
        <p><strong>Type:</strong> ${escapeHtml(device.node_type)}</p>
        <p><strong>Room:</strong> ${escapeHtml(device.room || room.room_name || "--")}</p>
        <p><strong>Position:</strong> X ${escapeHtml(device.x)} / Y ${escapeHtml(device.y)}</p>
    `;

    if (!currentLiveData.permissions.can_view_telemetry) {
        box.innerHTML = baseHtml + `
            <hr>
            <h3>Live Telemetry</h3>
            <p class="muted">Telemetry permission is disabled for this user.</p>
        `;
        return;
    }

    try {
        const res = await fetch(`/client-portal/${userId}/devices/${device.device_id}/latest-telemetry`);

        if (!res.ok) {
            box.innerHTML = baseHtml + `
                <hr>
                <h3>Live Telemetry</h3>
                <p class="muted">Could not load telemetry.</p>
            `;
            return;
        }

        const data = await res.json();
        const telemetry = data.telemetry || {};

        let telemetryHtml = `
            <hr>
            <h3>Live Telemetry</h3>
        `;

        if (Object.keys(telemetry).length === 0) {
            telemetryHtml += `<p class="muted">No telemetry received yet.</p>`;
        } else {
            Object.keys(telemetry).forEach(key => {
                const value = telemetry[key];

                if (
                    key === "alarm_active" ||
                    key === "alarm_message" ||
                    key === "received_by_gateways" ||
                    key === "gateway_id" ||
                    key === "rssi" ||
                    key === "snr" ||
                    key === "spreading_factor" ||
                    key === "bandwidth" ||
                    key === "frequency"
                ) {
                    return;
                }

                if (key === "temperature") {
                    telemetryHtml += `<p><strong>Temperature:</strong> ${escapeHtml(value)} °C</p>`;
                }

                else if (key === "humidity") {
                    telemetryHtml += `<p><strong>Humidity:</strong> ${escapeHtml(value)} %</p>`;
                }

                else if (key === "battery_percent") {
                    telemetryHtml += `<p><strong>Battery:</strong> 🔋 ${escapeHtml(value)}%</p>`;
                }

                else if (key === "battery_voltage") {
                    telemetryHtml += `<p><strong>Battery Voltage:</strong> ${escapeHtml(value)} V</p>`;
                }

                else if (key === "battery_status") {
                    let color = "#22c55e";

                    if (value === "low") color = "#f97316";
                    if (value === "critical") color = "#ef4444";

                    telemetryHtml += `
                        <p>
                            <strong>Battery Status:</strong>
                            <span style="color:${color};font-weight:bold;">
                                ${escapeHtml(String(value).toUpperCase())}
                            </span>
                        </p>
                    `;
                }

                else if (key === "signal_status") {
                    let color = "#22c55e";

                    if (value === "weak") color = "#f97316";
                    if (value === "poor") color = "#ef4444";

                    telemetryHtml += `
                        <p>
                            <strong>Connection Quality:</strong>
                            <span style="color:${color};font-weight:bold;">
                                ${escapeHtml(String(value).toUpperCase())}
                            </span>
                        </p>
                    `;
                }

                else if (key === "local_updated_at") {
                    return;
                }

                else {
                    telemetryHtml += `<p><strong>${escapeHtml(key)}:</strong> ${escapeHtml(value)}</p>`;
                }
            });
        }

        const alarmClass = data.alarm_active ? "color:#ef4444;font-weight:bold;" : "color:#22c55e;font-weight:bold;";

        telemetryHtml += `
            <p><strong>Alarm:</strong> <span style="${alarmClass}">${escapeHtml(data.alarm_message || "OK")}</span></p>
            <p><strong>Last Update:</strong> ${escapeHtml(data.updated_at || telemetry.local_updated_at || "--")}</p>
        `;

        box.innerHTML = baseHtml + telemetryHtml;

    } catch (e) {
        box.innerHTML = baseHtml + `
            <hr>
            <h3>Live Telemetry</h3>
            <p class="muted">Telemetry loading error.</p>
        `;
    }
}

function drawGateways() {
    if (!currentLiveData.permissions.can_view_gateways) {
        return;
    }

    const viewer = document.getElementById("viewer");
    const img = document.getElementById("floorImage");
    const floor = currentLiveData.floor;

    currentLiveData.gateways.forEach(gw => {
        if (gw.x === null || gw.y === null) {
            return;
        }

        const marker = document.createElement("div");
        const status = gw.status || "unknown";

        marker.className = "gateway-marker " + status;
        marker.innerHTML = "📡";
        marker.title = gw.label || gw.name || gw.gateway_id;

        marker.style.left = (gw.x * img.clientWidth / floor.image_width) + "px";
        marker.style.top = (gw.y * img.clientHeight / floor.image_height) + "px";

        marker.onclick = function(event) {
            event.stopPropagation();

            showDetails(`
                <h3>Gateway Details</h3>
                <p><strong>Name:</strong> ${escapeHtml(gw.name || "--")}</p>
                <p><strong>Label:</strong> ${escapeHtml(gw.label || "--")}</p>
                <p><strong>Gateway ID:</strong> ${escapeHtml(gw.gateway_id)}</p>
                <p><strong>Status:</strong> ${escapeHtml(status.toUpperCase())}</p>
                <p><strong>Last Seen:</strong> ${escapeHtml(gw.last_seen || "--")}</p>
                <p><strong>Position:</strong> X ${escapeHtml(gw.x || "--")} / Y ${escapeHtml(gw.y || "--")}</p>
                <p><strong>Note:</strong> ${escapeHtml(gw.location_note || "--")}</p>
            `);
        };

        viewer.appendChild(marker);
    });
}

function showDetails(html) {
    const box = document.getElementById("detailsBox");
    box.style.display = "block";
    box.innerHTML = html;
}

async function loadClientActivityLog() {
    const box = document.getElementById("clientActivityLog");

    if (!box) {
        console.log("clientActivityLog element not found");
        return;
    }

    box.innerHTML = "Loading activity...";

    try {
        const response = await fetch(`/client-portal/${userId}/activity-log?limit=50`);

        if (!response.ok) {
            throw new Error("Failed to load activity log");
        }

        const logs = await response.json();

        if (!logs || logs.length === 0) {
            box.innerHTML = `
                <div class="activity-empty">
                    No recent activity found.
                </div>
            `;
            return;
        }

        box.innerHTML = logs.map(function(log) {
            return `
                <div class="activity-item">
                    <div class="activity-message">
                        ${escapeHtml(log.message || "")}
                    </div>

                    <div class="activity-meta">
                        ${escapeHtml(log.timestamp || log.created_at || "")}
                        · <span class="activity-badge">${escapeHtml(log.action || "")}</span>
                    </div>
                </div>
            `;
        }).join("");

    } catch (error) {
        console.error("Activity log error:", error);

        box.innerHTML = `
            <div class="activity-error">
                Error loading activity log: ${escapeHtml(error.message)}
            </div>
        `;
    }
}

function exportClientAlarmHistoryCsv() {
    const query = new URLSearchParams();

    query.set("limit", "5000");

    if (selectedFloorId) {
        query.set("floor_id", selectedFloorId);
    }

    window.location.href = `/client-portal/${userId}/alarms/export.csv?` + query.toString();
}

function exportClientFullStructureCsv() {
    window.location.href = `/client-portal/${userId}/export/full-structure.csv`;
}

loadStructure();
loadClientActivityLog();
</script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""
    return HTMLResponse(html)

@router.get("/site-map-editor", response_class=HTMLResponse)
def site_map_editor():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Site Map Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
body{
    margin:0;
    font-family:Arial, sans-serif;
    background:#0f172a;
    color:#e5e7eb;
}

.header{
    padding:24px 34px;
    background:#111827;
    border-bottom:1px solid #334155;
}

.header h1{
    margin:0;
    font-size:28px;
    color:#f8fafc;
}

.header p{
    margin:8px 0 0;
    color:#94a3b8;
}

.toolbar{
    padding:16px 34px;
    background:#0f172a;
    border-bottom:1px solid #1e293b;
    display:flex;
    gap:12px;
    align-items:center;
    flex-wrap:wrap;
}

.toolbar label{
    color:#cbd5e1;
    font-weight:bold;
}

.toolbar input,
.toolbar select,
.toolbar button{
    width:auto;
    padding:10px 13px;
    border-radius:8px;
    border:1px solid #334155;
    font-size:14px;
}

.toolbar input,
.toolbar select{
    background:#020617;
    color:white;
}

.toolbar button{
    border:none;
    cursor:pointer;
    font-weight:bold;
    color:white;
    background:#2563eb;
}

.toolbar button:hover{
    background:#1d4ed8;
}

.adminHomeBtn{
    background:#334155 !important;
}

.adminHomeBtn:hover{
    background:#475569 !important;
}

.dangerBtn{
    background:#dc2626 !important;
}

.dangerBtn:hover{
    background:#b91c1c !important;
}

.clearBtn{
    background:#64748b !important;
}

.clearBtn:hover{
    background:#475569 !important;
}

.canvas-container{
    position:relative;
    display:block;
    width:calc(100vw - 68px);
    margin:24px 34px;
    background:#111827;
    border:1px solid #334155;
    border-radius:16px;
    padding:16px;
    box-shadow:0 16px 40px rgba(0,0,0,0.35);
    overflow:hidden;
}

#siteImage{
    display:block;
    width:100%;
    height:auto;
    border:1px solid #334155;
    border-radius:12px;
    background:#020617;
    opacity:0.92;
}

#overlay{
    position:absolute;
    top:16px;
    left:16px;
    width:calc(100% - 32px);
    height:calc(100% - 32px);
}

.point{
    fill:#ef4444;
    stroke:white;
    stroke-width:2;
}

.savedPolygon{
    fill:rgba(37,99,235,0.22);
    stroke:#60a5fa;
    stroke-width:3;
}

.activePolygon{
    fill:rgba(239,68,68,0.25);
    stroke:#ef4444;
    stroke-width:3;
}

.savedLabel{
    fill:#93c5fd;
    font-size:16px;
    font-weight:bold;
    paint-order:stroke;
    stroke:#020617;
    stroke-width:3px;
}
</style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Site Map Editor</h1>
    <p>Upload and manage the site/campus map, then draw building polygons.</p>
</div>

<div class="toolbar">
    <button class="adminHomeBtn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>

    <label>Site:</label>
    <select id="siteId" onchange="loadSite()"></select>

    <label>Building:</label>
    <select id="buildingSelect"></select>

    <button onclick="savePolygon()">Save Polygon</button>
    <button class="clearBtn" onclick="clearDrawing()">Clear Drawing</button>
    <button class="dangerBtn" onclick="deleteSavedPolygon()">Delete Saved Polygon</button>
</div>

<div class="canvas-container">
    <img id="siteImage">
    <svg id="overlay"></svg>
</div>

<script>
let siteData = null;
let currentPoints = [];

const image = document.getElementById("siteImage");
const overlay = document.getElementById("overlay");

async function loadSite() {
    const siteId = document.getElementById("siteId").value;

    if (!siteId) {
        return;
    }

    const response = await fetch(`/sites/${siteId}/map`);
    siteData = await response.json();

    image.src = siteData.site.campus_image_path;

    image.onload = () => {
        overlay.setAttribute("width", image.clientWidth);
        overlay.setAttribute("height", image.clientHeight);

        drawExistingBuildings();
    };

    loadBuildingsDropdown();
}

function loadBuildingsDropdown() {
    const select = document.getElementById("buildingSelect");
    select.innerHTML = "";

    siteData.buildings.forEach(b => {
        const option = document.createElement("option");
        option.value = b.id;
        option.textContent = b.name;
        select.appendChild(option);
    });
}

function originalToDisplay(p) {
    return {
        x: p.x * image.clientWidth / siteData.site.image_width,
        y: p.y * image.clientHeight / siteData.site.image_height
    };
}

function displayToOriginal(x, y) {
    return {
        x: Math.round(x * siteData.site.image_width / image.clientWidth),
        y: Math.round(y * siteData.site.image_height / image.clientHeight)
    };
}

function drawExistingBuildings() {
    overlay.innerHTML = "";

    siteData.buildings.forEach(building => {
        if (!building.polygon_points || building.polygon_points.length < 3) return;

        const displayPoints = building.polygon_points.map(originalToDisplay);

        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");

        polygon.setAttribute(
            "points",
            displayPoints.map(p => `${p.x},${p.y}`).join(" ")
        );

        polygon.setAttribute("class", "savedPolygon");

        polygon.style.cursor = "pointer";

        polygon.onclick = function() {
          window.location.href =
             "/building-overview?building_id=" + building.id;
};

        overlay.appendChild(polygon);

        const center = originalToDisplay({
            x: building.x,
            y: building.y
        });

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");

        text.setAttribute("x", center.x);
        text.setAttribute("y", center.y);
        text.setAttribute("class", "savedLabel");
        text.textContent = building.name;

        overlay.appendChild(text);
    });

    drawCurrentPolygon();
}

overlay.addEventListener("click", function(e){
    if (!siteData) return;

    const rect = overlay.getBoundingClientRect();

    const displayX = e.clientX - rect.left;
    const displayY = e.clientY - rect.top;

    const originalPoint = displayToOriginal(displayX, displayY);

    currentPoints.push(originalPoint);

    drawExistingBuildings();
});

function drawCurrentPolygon() {
    const displayPoints = currentPoints.map(originalToDisplay);

    displayPoints.forEach(p => {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");

        circle.setAttribute("cx", p.x);
        circle.setAttribute("cy", p.y);
        circle.setAttribute("r", 5);
        circle.setAttribute("class", "point");

        overlay.appendChild(circle);
    });

    if (displayPoints.length >= 3) {
        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");

        polygon.setAttribute(
            "points",
            displayPoints.map(p => `${p.x},${p.y}`).join(" ")
        );

        polygon.setAttribute("class", "activePolygon");

        overlay.appendChild(polygon);
    }
}

function clearDrawing() {
    currentPoints = [];
    drawExistingBuildings();
}

async function savePolygon() {
    if (currentPoints.length < 3) {
        alert("Need at least 3 points");
        return;
    }

    const buildingId = document.getElementById("buildingSelect").value;

    const res = await fetch(
        `/buildings/${buildingId}/polygon`,
        {
            method:"PUT",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                polygon_points:currentPoints
            })
        }
    );

    if (!res.ok) {
        const err = await res.json();
        alert(JSON.stringify(err));
        return;
    }

    alert("Building polygon saved");

    currentPoints = [];

    await loadSite();
}
async function deleteSavedPolygon() {
    const buildingId = document.getElementById("buildingSelect").value;

    if (!buildingId) {
        alert("Select a building first");
        return;
    }

    if (!confirm("Delete saved polygon for this building?")) {
        return;
    }

    const res = await fetch(
        `/buildings/${buildingId}/polygon`,
        {
            method: "DELETE"
        }
    );

    if (!res.ok) {
        const err = await res.json();
        alert(JSON.stringify(err));
        return;
    }

    alert("Saved polygon deleted");

    currentPoints = [];

    await loadSite();
}
window.onload = loadSite;
async function loadSiteDropdown() {
    const select = document.getElementById("siteId");

    try {
        const res = await fetch("/sites");
        const sites = await res.json();

        select.innerHTML = `<option value="">Select site</option>`;

        sites.forEach(site => {
            const label = `${site.name} / Client ID ${site.client_id} / ID ${site.id}`;

            select.innerHTML += `
                <option value="${site.id}">
                    ${label}
                </option>
            `;
        });

        const params = new URLSearchParams(window.location.search);
        const requestedSiteId = params.get("site_id");

        if (
            requestedSiteId &&
            sites.some(site => String(site.id) === String(requestedSiteId))
        ) {
            select.value = requestedSiteId;
            loadSite();
        }
        else if (sites.length > 0) {
            select.value = sites[0].id;
            loadSite();
        }

    } catch (err) {
        alert("Could not load sites: " + err.message);
    }
}

document.addEventListener("DOMContentLoaded", loadSiteDropdown);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""

@router.get("/floor-editor", response_class=HTMLResponse)
def floor_editor():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Floor Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

<style>
body{
    margin:0;
    font-family:Arial, sans-serif;
    background:#0f172a;
    color:#e5e7eb;
}

.header{
    padding:24px 34px;
    background:#111827;
    border-bottom:1px solid #334155;
}

.header h1{
    margin:0;
    font-size:28px;
    color:#f8fafc;
}

.header p{
    margin:8px 0 0;
    color:#94a3b8;
}

.toolbar{
    padding:16px 34px;
    background:#0f172a;
    border-bottom:1px solid #1e293b;
    display:flex;
    gap:12px;
    align-items:center;
    flex-wrap:wrap;
}

.toolbar label{
    color:#cbd5e1;
    font-weight:bold;
}

.toolbar input,
.toolbar button{
    width:auto;
    padding:10px 13px;
    border-radius:8px;
    border:1px solid #334155;
    font-size:14px;
}

.toolbar input{
    background:#020617;
    color:white;
}

.toolbar button{
    border:none;
    cursor:pointer;
    font-weight:bold;
    color:white;
    background:#2563eb;
}

.toolbar button:hover{
    background:#1d4ed8;
}

.adminHomeBtn{
    background:#334155 !important;
}

.adminHomeBtn:hover{
    background:#475569 !important;
}

.layout{
    display:flex;
    height:calc(100vh - 152px);
}

.editor{
    flex:1;
    position:relative;
    overflow:auto;
    padding:24px 34px;
}

.canvasBox{
    position:relative;
    display:block;
    width:calc(100vw - 430px);
    background:#111827;
    border:1px solid #334155;
    border-radius:16px;
    padding:14px;
    box-shadow:0 16px 40px rgba(0,0,0,0.35);
}

#floorImage{
    width:100%;
    height:auto;
    display:block;
    border:1px solid #334155;
    border-radius:12px;
    background:#020617;
    opacity:0.92;
}

#overlay{
    position:absolute;
    top:14px;
    left:14px;
    width:calc(100% - 28px);
    height:calc(100% - 28px);
}

.sidePanel{
    width:330px;
    background:#111827;
    border-left:1px solid #334155;
    padding:18px;
    overflow:auto;
    box-shadow:-8px 0 24px rgba(0,0,0,0.25);
}

.sidePanel h2{
    margin-top:0;
    color:#f8fafc;
}

.sidePanel h3{
    color:#93c5fd;
}

.roomItem{
    padding:10px;
    border-radius:8px;
    background:#020617;
    border:1px solid #334155;
    margin-bottom:8px;
    cursor:pointer;
    color:#e5e7eb;
}

.roomItem:hover{
    background:#1e293b;
}

.roomItem.active{
    background:#78350f;
    border-color:#f59e0b;
    font-weight:bold;
}

.sidePanel label{
    color:#cbd5e1;
    font-size:14px;
    font-weight:bold;
}

.sidePanel input,
.sidePanel button{
    width:100%;
    box-sizing:border-box;
    padding:10px;
    margin-top:8px;
    margin-bottom:10px;
    border-radius:8px;
}

.sidePanel input{
    border:1px solid #334155;
    background:#020617;
    color:white;
}

.sidePanel button{
    border:none;
    background:#2563eb;
    color:white;
    font-weight:bold;
    cursor:pointer;
}

.sidePanel button:hover{
    background:#1d4ed8;
}

.deleteBtn{
    background:#dc2626 !important;
}

.deleteBtn:hover{
    background:#b91c1c !important;
}

.clearBtn{
    background:#64748b !important;
}

.clearBtn:hover{
    background:#475569 !important;
}

.savedRoom{
    fill:rgba(37,99,235,0.20);
    stroke:#60a5fa;
    stroke-width:3;
}

.selectedRoom{
    fill:rgba(245,158,11,0.25);
    stroke:#f59e0b;
    stroke-width:4;
}

.newRoom{
    fill:rgba(239,68,68,0.25);
    stroke:#ef4444;
    stroke-width:3;
}

.point{
    fill:#ef4444;
    stroke:white;
    stroke-width:2;
}

.roomLabel{
    fill:#93c5fd;
    font-size:15px;
    font-weight:bold;
    paint-order:stroke;
    stroke:#020617;
    stroke-width:3px;
}

.hint{
    font-size:12px;
    color:#94a3b8;
    line-height:1.5;
}

hr{
    border:none;
    border-top:1px solid #334155;
    margin:16px 0;
}
</style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Floor Editor</h1>
    <p>Draw, edit, and delete room polygons on the selected floor plan.</p>
</div>

<div class="toolbar">
    <button class="adminHomeBtn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>

    <label>Floor:</label>
    
    <select id="floorId" onchange="loadFloor()"></select>
</div>

<div class="layout">

    <div class="editor">
        <div class="canvasBox">
            <img id="floorImage">
            <svg id="overlay"></svg>
        </div>
    </div>

    <div class="sidePanel">
        <h2>Room Editor</h2>

        <button onclick="newRoom()">+ New Room</button>

        <h3>Rooms</h3>
        <div id="roomList"></div>

        <hr>

        <label>Room Name</label>
        <input id="roomName" placeholder="Room name">

        <button onclick="saveRoom()">Save Room</button>
        <button class="clearBtn" onclick="clearDrawing()">Clear Drawing</button>
        <button class="deleteBtn" onclick="deleteRoom()">Delete Selected Room</button>

        <p class="hint">
            Blue = saved room<br>
            Orange = selected room<br>
            Red = current drawing
        </p>
    </div>

</div>

<script>
let floorData = null;
let selectedDeviceId = null;
let selectedRoomId = null;
let rooms = [];
let currentPoints = [];
let selectedRoom = null;
let mode = "new";

const image = document.getElementById("floorImage");
const overlay = document.getElementById("overlay");

function originalToDisplay(p){
    return {
        x: p.x * image.clientWidth / floorData.floor.image_width,
        y: p.y * image.clientHeight / floorData.floor.image_height
    };
}

function displayToOriginal(x, y){
    return {
        x: Math.round(x * floorData.floor.image_width / image.clientWidth),
        y: Math.round(y * floorData.floor.image_height / image.clientHeight)
    };
}

async function loadFloor(){
    const floorId = document.getElementById("floorId").value;

    if (!floorId) {
        
        return;
    }

    const res = await fetch(`/floors/${floorId}/details`);
    floorData = await res.json();

    const roomsRes = await fetch(`/floors/${floorId}/rooms`);
    rooms = await roomsRes.json();

    image.src = floorData.floor.image_path;

    image.onload = function(){
        overlay.setAttribute("width", image.clientWidth);
        overlay.setAttribute("height", image.clientHeight);
        draw();
    };

    renderRoomList();

    if(image.complete){
        draw();
    }
}

function renderRoomList(){
    const list = document.getElementById("roomList");
    list.innerHTML = "";

    rooms.forEach(room => {
        const div = document.createElement("div");
        div.className = "roomItem" + (selectedRoom && selectedRoom.id === room.id ? " active" : "");
        div.innerText = room.room_name;

        div.onclick = function(){
            selectRoom(room);
        };

        list.appendChild(div);
    });
}

function selectRoom(room){
    selectedRoom = room;
    mode = "edit";
    currentPoints = room.polygon_points ? [...room.polygon_points] : [];

    document.getElementById("roomName").value = room.room_name;

    renderRoomList();
    draw();
}

function newRoom(){
    selectedRoom = null;
    mode = "new";
    currentPoints = [];
    document.getElementById("roomName").value = "";
    renderRoomList();
    draw();
}

overlay.addEventListener("click", function(e){
    if(!floorData) return;

    const rect = overlay.getBoundingClientRect();
    const displayX = e.clientX - rect.left;
    const displayY = e.clientY - rect.top;

    const p = displayToOriginal(displayX, displayY);
    currentPoints.push(p);

    draw();
});

function draw(){
    overlay.innerHTML = "";

    rooms.forEach(room => {
        if(!room.polygon_points || room.polygon_points.length < 3) return;

        const pts = room.polygon_points.map(originalToDisplay);

        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        polygon.setAttribute("points", pts.map(p => `${p.x},${p.y}`).join(" "));
        polygon.setAttribute("class", selectedRoom && selectedRoom.id === room.id ? "selectedRoom" : "savedRoom");

        polygon.style.cursor = "pointer";
        polygon.onclick = function(e){
            e.stopPropagation();
            selectRoom(room);
        };

        overlay.appendChild(polygon);

        const center = originalToDisplay({x: room.x, y: room.y});

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", center.x);
        label.setAttribute("y", center.y);
        label.setAttribute("class", "roomLabel");
        label.textContent = room.room_name;

        overlay.appendChild(label);
    });

    drawCurrentPolygon();
}

function drawCurrentPolygon(){
    const displayPoints = currentPoints.map(originalToDisplay);

    displayPoints.forEach(p => {
        const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        c.setAttribute("cx", p.x);
        c.setAttribute("cy", p.y);
        c.setAttribute("r", 5);
        c.setAttribute("class", "point");
        overlay.appendChild(c);
    });

    if(displayPoints.length >= 3){
        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        polygon.setAttribute("points", displayPoints.map(p => `${p.x},${p.y}`).join(" "));
        polygon.setAttribute("class", "newRoom");
        overlay.appendChild(polygon);
    }
}

function clearDrawing(){
    currentPoints = [];
    draw();
}

async function saveRoom(){
    const floorId = document.getElementById("floorId").value;
    const roomName = document.getElementById("roomName").value.trim();

    if(!roomName){
        alert("Enter room name");
        return;
    }

    if(currentPoints.length < 3){
        alert("Click at least 3 points");
        return;
    }

    let url = "";
    let method = "";

    if(mode === "edit" && selectedRoom){
        url = `/rooms/${selectedRoom.id}`;
        method = "PUT";
    } else {
        url = `/floors/${floorId}/rooms`;
        method = "POST";
    }

    const res = await fetch(url, {
        method: method,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            room_name: roomName,
            polygon_points: currentPoints
        })
    });

    const data = await res.json();

    if(!res.ok){
        alert(JSON.stringify(data));
        return;
    }

    alert("Room saved");

    selectedRoom = null;
    currentPoints = [];
    document.getElementById("roomName").value = "";

    await loadFloor();
}

async function deleteRoom(){
    if(!selectedRoom){
        alert("Select a room first");
        return;
    }

    if(!confirm("Delete room: " + selectedRoom.room_name + "?")){
        return;
    }

    const res = await fetch(`/rooms/${selectedRoom.id}`, {
        method: "DELETE"
    });

    const data = await res.json();

    if(!res.ok){
        alert(JSON.stringify(data));
        return;
    }

    alert("Room deleted");

    selectedRoom = null;
    currentPoints = [];
    document.getElementById("roomName").value = "";

    await loadFloor();
}



window.onload = loadFloor;

async function loadFloorDropdown() {
    const select = document.getElementById("floorId");

    try {
        const res = await fetch("/floors");
        const floors = await res.json();

        select.innerHTML = `<option value="">Select floor</option>`;

        floors.forEach(floor => {
            const label = `${floor.name || "Floor"} / Building ID ${floor.building_id} / ID ${floor.id}`;

            select.innerHTML += `
                <option value="${floor.id}">
                    ${label}
                </option>
            `;
        });

        const params = new URLSearchParams(window.location.search);
        const requestedFloorId = params.get("floor_id");

        if (
            requestedFloorId &&
            floors.some(floor => String(floor.id) === String(requestedFloorId))
        ) {
            select.value = requestedFloorId;
            loadFloor();
        }

    } catch (err) {
        alert("Could not load floors: " + err.message);
    }
}

document.addEventListener("DOMContentLoaded", loadFloorDropdown);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""

@router.post("/devices/{device_id}/capabilities")
@router.get("/devices/{device_id}/capabilities")
@router.get("/device-capabilities-manager", response_class=HTMLResponse)
def device_capabilities_manager_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Device Capabilities Manager</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        .header {
            padding: 22px 30px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 28px;
        }

        .header p {
            margin: 8px 0 0;
            color: #94a3b8;
        }

        .container {
            padding: 30px;
        }

        .toolbar {
            margin-bottom: 20px;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #1d4ed8;
        }

        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
            gap: 18px;
        }

        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }

        .card h3 {
            margin: 0 0 6px;
            font-size: 21px;
        }

        .meta {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 14px;
            word-break: break-word;
        }

        .status-line {
            margin-bottom: 12px;
            color: #e5e7eb;
            font-size: 14px;
        }

        .capabilities {
            display: grid;
            gap: 10px;
            margin-top: 14px;
        }

        .cap-row {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #0f172a;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #334155;
        }

        .cap-row input {
            width: 18px;
            height: 18px;
        }

        .save-btn {
            margin-top: 16px;
            width: 100%;
        }

        .badge {
            display: inline-block;
            padding: 4px 9px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 6px;
        }

        .badge.multi {
            background: #075985;
            color: #bae6fd;
        }

        .badge.single {
            background: #14532d;
            color: #bbf7d0;
        }

        .message {
            margin-top: 12px;
            font-size: 13px;
        }

        .success {
            color: #86efac;
        }

        .error {
            color: #fecaca;
        }

        .loading {
            color: #94a3b8;
            padding: 30px;
        }

        .admin-home-btn {
            display: inline-block;
            background: #334155;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
        }

        .admin-home-btn:hover {
            background: #475569;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

    <div class="header">
        <h1>Device Capabilities Manager</h1>
        <p>Select what each node can measure or control. More than one capability automatically makes the node multi.</p>
    </div>

    <div class="container">
        <div class="toolbar">
            <button class="admin-home-btn" onclick="window.location.href='/admin'">
                ← Admin Home
            </button>

            <button onclick="loadDevices()">
                Refresh Devices
            </button>
        </div>

        <div id="devicesArea" class="loading">
            Loading devices...
        </div>
    </div>

    <script>
        const params = new URLSearchParams(window.location.search);
        const requestedDeviceId = params.get("device_id");
        const capabilityOptions = [
            { key: "environment", label: "Environment" },
            { key: "energy", label: "Energy" },
            { key: "safety", label: "Safety" },
            { key: "occupancy", label: "Occupancy" }
        ];

        function escapeHtml(value) {
            if(value === null || value === undefined) return "";
            return String(value)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#039;");
        }

        function getCapabilitiesFromDevice(device) {
            if(device.capabilities && Array.isArray(device.capabilities) && device.capabilities.length) {
                return device.capabilities;
            }

            if(["environment", "energy", "safety", "occupancy"].includes(device.node_type)) {
                return [device.node_type];
            }

            if(device.node_type === "multi") {
                return ["environment", "energy", "safety", "occupancy"];
            }

            return [];
        }

        function buildCapabilityCheckboxes(device) {
            const caps = getCapabilitiesFromDevice(device);

            return capabilityOptions.map(cap => {
                const checked = caps.includes(cap.key) ? "checked" : "";

                return `
                    <label class="cap-row">
                        <input 
                            type="checkbox" 
                            class="cap-check"
                            data-device-id="${escapeHtml(device.device_id)}"
                            value="${cap.key}"
                            ${checked}
                        >
                        <span>${cap.label}</span>
                    </label>
                `;
            }).join("");
        }

        function nodeTypeBadge(device) {
            const caps = getCapabilitiesFromDevice(device);

            if(caps.length > 1 || device.node_type === "multi") {
                return `<span class="badge multi">MULTI</span>`;
            }

            return `<span class="badge single">SINGLE</span>`;
        }

        async function loadDevices() {
            const area = document.getElementById("devicesArea");
            area.className = "loading";
            area.innerHTML = "Loading devices...";

            try {
                const res = await fetch("/devices-status");

                if(!res.ok) {
                    throw new Error("Failed to load devices");
                }

                const devices = await res.json();

                if(!devices.length) {
                    area.innerHTML = "No devices found.";
                    return;
                }

                area.className = "device-grid";
                area.innerHTML = "";

                devices.forEach(device => {
                    const card = document.createElement("div");
                    card.className = "card";

                    if (requestedDeviceId && String(device.device_id) === String(requestedDeviceId)) {
                        card.style.borderColor = "#60a5fa";
                        card.style.boxShadow = "0 0 0 2px rgba(96,165,250,0.45), 0 14px 34px rgba(0,0,0,0.35)";
                    }

                    const label = device.label || device.device_id;
                    const status = device.telemetry?.device_status || "unknown";

                    card.innerHTML = `
                        <h3>${escapeHtml(label)} ${nodeTypeBadge(device)}</h3>

                        <div class="meta">
                            Device ID: ${escapeHtml(device.device_id)}<br>
                            Current Type: ${escapeHtml(device.node_type || "--")}<br>
                            Room: ${escapeHtml(device.room || "--")}<br>
                            Floor: ${escapeHtml(device.floor || "--")}
                        </div>

                        <div class="status-line">
                            Live Status: <b>${escapeHtml(status)}</b>
                        </div>

                        <div class="capabilities">
                            ${buildCapabilityCheckboxes(device)}
                        </div>

                        <button class="save-btn" onclick="saveCapabilities('${escapeHtml(device.device_id)}')">
                            Save Capabilities & Sync Formatter
                        </button>
                        <button class="btn" style="background:#10b981; margin-top:8px;" onclick="openTelemetryGraph('${escapeHtml(device.device_id)}', '${escapeHtml(device.name || device.device_id)}')">
                            📉 View Device Graphs
                        </button>

                        <div id="msg-${escapeHtml(device.device_id)}" class="message"></div>
                    `;

                    area.appendChild(card);
                    if (requestedDeviceId && String(device.device_id) === String(requestedDeviceId)) {
                        setTimeout(() => {
                        card.scrollIntoView({ behavior: "smooth", block: "center" });
                        }, 200);
                    }
                });

            } catch(err) {
                area.className = "error";
                area.innerHTML = "Error loading devices: " + err.message;
            }
        }

        async function saveCapabilities(deviceId) {
            const msg = document.getElementById("msg-" + deviceId);

            const checks = document.querySelectorAll(
                `.cap-check[data-device-id="${deviceId}"]:checked`
            );

            const capabilities = Array.from(checks).map(c => c.value);

            if (!capabilities.length) {
                msg.className = "message error";
                msg.innerHTML = "Select at least one capability.";
                return;
            }

            try {

                msg.className = "message loading";
                msg.innerHTML = "Saving capabilities and syncing TTN formatter...";

                const res = await fetch(`/devices/${deviceId}/capabilities`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        capabilities: capabilities
                    })
                });

                const data = await res.json();

                if (!res.ok) {
                    throw new Error(data.detail || "Failed to save capabilities");
                }

                const syncRes = await fetch(`/devices/${deviceId}/sync-formatter`, {
                    method: "POST"
                });

                const syncData = await syncRes.json();

                if (!syncRes.ok) {
                    msg.className = "message error";
                    msg.innerHTML =
                        `Capabilities saved. Node type is now: ${data.node_type}. ` +
                        `But formatter sync failed: ${syncData.detail || "Unknown error"}`;
                    return;
                }

                msg.className = "message success";
                msg.innerHTML =
                    `Saved successfully. Node type is now: ${data.node_type}. ` +
                    `TTN formatter synced.`;

                

            } catch (err) {
                msg.className = "message error";
                msg.innerHTML = "Error: " + err.message;
            }
        }

        document.addEventListener("DOMContentLoaded", loadDevices);
    </script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/admin/audit-log", response_class=HTMLResponse)
def admin_audit_log_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Admin Audit Log</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            margin: 0;
            padding: 0;
            color: #1f2937;
        }

        .topbar {
            background: #111827;
            color: white;
            padding: 18px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .topbar h1 {
            margin: 0;
            font-size: 22px;
        }

        .topbar a {
            color: white;
            text-decoration: none;
            background: #374151;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
        }

        .container {
            padding: 24px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }

        .filters {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
        }

        label {
            font-size: 12px;
            font-weight: bold;
            color: #4b5563;
            display: block;
            margin-bottom: 4px;
        }

        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 13px;
            box-sizing: border-box;
        }

        .buttons {
            margin-top: 14px;
            display: flex;
            gap: 10px;
        }

        button {
            border: none;
            padding: 9px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }

        .btn-primary {
            background: #2563eb;
            color: white;
        }

        .btn-secondary {
            background: #e5e7eb;
            color: #111827;
        }

        .summary {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }

        .summary-box {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th {
            background: #f9fafb;
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 13px;
            color: #374151;
        }

        td {
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 13px;
            vertical-align: top;
        }

        tr:hover {
            background: #f9fafb;
        }

        .message {
            font-weight: 600;
            color: #111827;
        }

        .muted {
            color: #6b7280;
            font-size: 12px;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            background: #eef2ff;
            color: #3730a3;
            font-size: 12px;
            font-weight: bold;
        }

        .scope {
            font-size: 12px;
            line-height: 1.5;
            color: #374151;
        }

        .details-row {
            display: none;
            background: #111827;
            color: #e5e7eb;
        }

        .details-box {
            white-space: pre-wrap;
            font-family: Consolas, monospace;
            font-size: 12px;
            overflow-x: auto;
            padding: 14px;
            background: #111827;
            color: #e5e7eb;
            border-radius: 8px;
        }

        .small-btn {
            background: #111827;
            color: white;
            padding: 6px 10px;
            font-size: 12px;
        }

        .empty {
            text-align: center;
            padding: 30px;
            color: #6b7280;
        }

        @media (max-width: 1100px) {
            .filters {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 700px) {
            .filters {
                grid-template-columns: 1fr;
            }

            table {
                font-size: 12px;
            }

            th, td {
                padding: 8px;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>
    <div class="topbar">
        <h1>Admin Audit Log</h1>
        <a href="/admin">Back to Admin Home</a>
    </div>

    <div class="container">
        <div class="card">
            <h2 style="margin-top:0;">Filters</h2>

            <div class="filters">
                <div>
                    <label>Search</label>
                    <input id="search" placeholder="gateway, alarm, user...">
                </div>

                <div>
                    <label>Action</label>
                    <select id="action">
                        <option value="">All actions</option>
                        <option value="move_gateway">move_gateway</option>
                        <option value="update_gateway">update_gateway</option>
                        <option value="move_device">move_device</option>
                        <option value="acknowledge_alarm">acknowledge_alarm</option>
                        <option value="resolve_alarm">resolve_alarm</option>
                        <option value="update_user_access">update_user_access</option>
                        <option value="enable_user">enable_user</option>
                        <option value="disable_user">disable_user</option>
                        <option value="create_user">create_user</option>
                        <option value="update_user">update_user</option>
                        <option value="delete_user">delete_user</option>
                    </select>
                </div>

                <div>
                    <label>Target Type</label>
                    <select id="target_type">
                        <option value="">All targets</option>
                        <option value="gateway">gateway</option>
                        <option value="device">device</option>
                        <option value="alarm">alarm</option>
                        <option value="user">user</option>
                        <option value="user_access">user_access</option>
                    </select>
                </div>

                <div>
                    <label>Target ID</label>
                    <input id="target_id" placeholder="1 or node ID">
                </div>

                <div>
                    <label>Actor</label>
                    <input id="actor" placeholder="admin">
                </div>

                <div>
                    <label>Client ID</label>
                    <input id="client_id" type="number" placeholder="1">
                </div>

                <div>
                    <label>Site ID</label>
                    <input id="site_id" type="number" placeholder="1">
                </div>

                <div>
                    <label>Building ID</label>
                    <input id="building_id" type="number" placeholder="1">
                </div>

                <div>
                    <label>Floor ID</label>
                    <input id="floor_id" type="number" placeholder="1">
                </div>

                <div>
                    <label>Room ID</label>
                    <input id="room_id" type="number" placeholder="2">
                </div>

                <div>
                    <label>Device ID</label>
                    <input id="device_id" placeholder="node-f1e2d3c4b5a6">
                </div>

                <div>
                    <label>Gateway ID</label>
                    <input id="gateway_id" placeholder="test-gateway-001">
                </div>

                <div>
                    <label>User ID</label>
                    <input id="user_id" type="number" placeholder="1">
                </div>

                <div>
                    <label>From Date</label>
                    <input id="from_date" type="date">
                </div>

                <div>
                    <label>To Date</label>
                    <input id="to_date" type="date">
                </div>
            </div>

            <div class="buttons">
                    <button class="btn-primary" onclick="loadLogs()">Apply Filters</button>
                    <button class="btn-secondary" onclick="resetFilters()">Reset</button>
                    <button class="btn-secondary" onclick="exportCsv()">Export CSV</button>
            </div>

        <div class="card">
            <div class="summary">
                <div class="summary-box">
                    <b>Total shown:</b> <span id="totalCount">0</span>
                </div>
                <div class="summary-box">
                    <b>Last loaded:</b> <span id="lastLoaded">-</span>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:150px;">Timestamp</th>
                        <th>Message</th>
                        <th style="width:150px;">Action</th>
                        <th style="width:120px;">Target</th>
                        <th style="width:120px;">Actor</th>
                        <th style="width:220px;">Scope</th>
                        <th style="width:90px;">Details</th>
                    </tr>
                </thead>
                <tbody id="auditBody">
                    <tr>
                        <td colspan="7" class="empty">Loading audit logs...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

<script>
    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function getValue(id) {
        const element = document.getElementById(id);
        if (!element) {
            return "";
        }

        return element.value.trim();
    }

    function buildQuery(limitValue = "200") {
    const fields = [
        "search",
        "action",
        "target_type",
        "target_id",
        "actor",
        "client_id",
        "site_id",
        "building_id",
        "floor_id",
        "room_id",
        "device_id",
        "gateway_id",
        "user_id",
        "from_date",
        "to_date"
    ];

    const params = new URLSearchParams();

    params.set("limit", limitValue);

    fields.forEach(function(field) {
        const value = getValue(field);

        if (value !== "") {
            params.set(field, value);
        }
    });

    return params.toString();
    }

    function exportCsv() {
    const query = buildQuery("5000");
    window.location.href = "/audit-log/export.csv?" + query;
    }                                        

    async function loadLogs() {
        const tbody = document.getElementById("auditBody");

        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty">Loading audit logs...</td>
            </tr>
        `;

        try {
            const query = buildQuery("200");
            const response = await fetch("/audit-log?" + query);

            if (!response.ok) {
                throw new Error("Failed to load audit logs");
            }

            const logs = await response.json();

            document.getElementById("totalCount").innerText = logs.length;
            document.getElementById("lastLoaded").innerText = new Date().toLocaleString();

            if (logs.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty">No audit logs found for these filters.</td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = "";

            logs.forEach(function(log) {
                const scopeParts = [];

                if (log.client_id !== null && log.client_id !== undefined) {
                    scopeParts.push("Client: " + log.client_id);
                }

                if (log.site_id !== null && log.site_id !== undefined) {
                    scopeParts.push("Site: " + log.site_id);
                }

                if (log.building_id !== null && log.building_id !== undefined) {
                    scopeParts.push("Building: " + log.building_id);
                }

                if (log.floor_id !== null && log.floor_id !== undefined) {
                    scopeParts.push("Floor: " + log.floor_id);
                }

                if (log.room_id !== null && log.room_id !== undefined) {
                    scopeParts.push("Room: " + log.room_id);
                }

                if (log.device_id) {
                    scopeParts.push("Device: " + log.device_id);
                }

                if (log.gateway_id) {
                    scopeParts.push("Gateway: " + log.gateway_id);
                }

                if (log.user_id !== null && log.user_id !== undefined) {
                    scopeParts.push("User: " + log.user_id);
                }

                const scopeHtml = scopeParts.length
                    ? scopeParts.map(escapeHtml).join("<br>")
                    : "<span class='muted'>No scope</span>";

                const detailsId = "details-" + log.id;

                const mainRow = document.createElement("tr");

                mainRow.innerHTML = `
                    <td>
                        <div>${escapeHtml(log.timestamp || log.created_at || "")}</div>
                        <div class="muted">ID ${escapeHtml(log.id)}</div>
                    </td>
                    <td>
                        <div class="message">${escapeHtml(log.message || "")}</div>
                        <div class="muted">${escapeHtml(log.target_type || "")} ${escapeHtml(log.target_id || "")}</div>
                    </td>
                    <td><span class="badge">${escapeHtml(log.action || "")}</span></td>
                    <td>
                        ${escapeHtml(log.target_type || "")}
                        <br>
                        <span class="muted">${escapeHtml(log.target_id || "")}</span>
                    </td>
                    <td>${escapeHtml(log.actor || "")}</td>
                    <td class="scope">${scopeHtml}</td>
                    <td>
                        <button class="small-btn" onclick="toggleDetails('${detailsId}')">View</button>
                    </td>
                `;

                const detailsRow = document.createElement("tr");
                detailsRow.id = detailsId;
                detailsRow.className = "details-row";

                detailsRow.innerHTML = `
                    <td colspan="7">
                        <div class="details-box">${escapeHtml(JSON.stringify(log.details || {}, null, 2))}</div>
                    </td>
                `;

                tbody.appendChild(mainRow);
                tbody.appendChild(detailsRow);
            });

        } catch (error) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty">Error loading audit logs: ${escapeHtml(error.message)}</td>
                </tr>
            `;
        }
    }

    function toggleDetails(id) {
        const row = document.getElementById(id);

        if (!row) {
            return;
        }

        if (row.style.display === "table-row") {
            row.style.display = "none";
        } else {
            row.style.display = "table-row";
        }
    }

    function resetFilters() {
        const fields = [
            "search",
            "action",
            "target_type",
            "target_id",
            "actor",
            "client_id",
            "site_id",
            "building_id",
            "floor_id",
            "room_id",
            "device_id",
            "gateway_id",
            "user_id",
            "from_date",
            "to_date"
        ];

        fields.forEach(function(field) {
            const element = document.getElementById(field);

            if (element) {
                element.value = "";
            }
        });

        loadLogs();
    }

    loadLogs();
</script>
<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """)

@router.get("/admin/setup", response_class=HTMLResponse)
def admin_setup_asset_management_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Setup & Asset Management</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta charset="UTF-8">

    <style>
        :root {
            --bg: #0f172a;
            --panel: #111827;
            --panel-2: #020617;
            --border: #334155;
            --muted: #94a3b8;
            --text: #e5e7eb;
            --title: #f8fafc;
            --blue: #2563eb;
            --blue-2: #1d4ed8;
            --green: #16a34a;
            --green-2: #15803d;
            --red: #dc2626;
            --red-2: #b91c1c;
            --orange: #f97316;
            --orange-2: #ea580c;
            --purple: #7c3aed;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
        }

        .header {
            padding: 28px 38px;
            background:
                radial-gradient(circle at top right, rgba(37,99,235,0.30), transparent 34%),
                linear-gradient(135deg, #111827, #1e293b);
            border-bottom: 1px solid var(--border);
        }

        .top-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 18px;
            flex-wrap: wrap;
        }

        .eyebrow {
            display: inline-block;
            padding: 6px 11px;
            border-radius: 999px;
            background: rgba(37,99,235,0.18);
            border: 1px solid rgba(96,165,250,0.35);
            color: #bfdbfe;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 12px;
            letter-spacing: 0.04em;
        }

        .header h1 {
            margin: 0;
            font-size: 34px;
            color: var(--title);
        }

        .header p {
            margin: 10px 0 0;
            color: var(--muted);
            line-height: 1.55;
            max-width: 950px;
            font-size: 15px;
        }

        .header-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .container {
            padding: 26px 38px 46px;
        }

        .btn, button, .link-btn {
            display: inline-block;
            padding: 10px 13px;
            border: none;
            border-radius: 9px;
            cursor: pointer;
            font-weight: bold;
            background: var(--blue);
            color: white;
            text-decoration: none;
            font-size: 14px;
        }

        .btn:hover, button:hover, .link-btn:hover {
            background: var(--blue-2);
        }

        .secondary {
            background: #334155;
            border: 1px solid #475569;
        }

        .secondary:hover {
            background: #475569;
        }

        .success {
            background: var(--green);
        }

        .success:hover {
            background: var(--green-2);
        }

        .danger {
            background: var(--red);
        }

        .danger:hover {
            background: var(--red-2);
        }

        .warning {
            background: var(--orange);
        }

        .warning:hover {
            background: var(--orange-2);
        }

        .note-card {
            background: linear-gradient(135deg, #451a03, #7c2d12);
            border: 1px solid #f97316;
            color: #fed7aa;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 22px;
            box-shadow: 0 16px 38px rgba(0,0,0,0.28);
        }

        .note-card h2 {
            margin: 0 0 10px;
            color: #ffedd5;
            font-size: 22px;
        }

        .note-card ul {
            margin: 10px 0 0;
            padding-left: 22px;
            line-height: 1.7;
        }

        .note-card strong {
            color: #ffffff;
        }

        .progress-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(225px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }

        .step {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 10px 26px rgba(0,0,0,0.22);
        }

        .step .num {
            display: inline-block;
            background: linear-gradient(135deg, var(--blue), var(--purple));
            color: white;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 9px;
        }

        .step h3 {
            margin: 4px 0 6px;
            color: var(--title);
            font-size: 16px;
        }

        .step p {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.45;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(390px, 1fr));
            gap: 22px;
            align-items: start;
        }

        .card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(0,0,0,0.30);
        }

        .card.full {
            grid-column: 1 / -1;
        }

        .card h2 {
            margin: 0 0 8px;
            color: var(--title);
            font-size: 21px;
        }

        .card-header-line {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 8px;
        }

        .pill {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #020617;
            border: 1px solid var(--border);
            color: #93c5fd;
            font-size: 11px;
            font-weight: bold;
        }

        .muted {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.5;
            margin-bottom: 12px;
        }

        label {
            display: block;
            margin-top: 12px;
            margin-bottom: 6px;
            color: #cbd5e1;
            font-size: 14px;
            font-weight: bold;
        }

        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            border-radius: 9px;
            border: 1px solid var(--border);
            background: var(--panel-2);
            color: white;
            outline: none;
        }

        input:focus, select:focus, textarea:focus {
            border-color: #60a5fa;
        }

        textarea {
            min-height: 78px;
            resize: vertical;
        }

        .row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }

        .row button, .row .link-btn, .row .btn {
            width: auto;
            margin-top: 12px;
        }

        .status {
            display: none;
            margin-top: 12px;
            padding: 11px;
            border-radius: 10px;
            font-size: 13px;
            line-height: 1.45;
        }

        .status.good {
            display: block;
            background: #14532d;
            color: #bbf7d0;
            border: 1px solid #22c55e;
        }

        .status.bad {
            display: block;
            background: #7f1d1d;
            color: #fecaca;
            border: 1px solid #ef4444;
        }

        .status.info {
            display: block;
            background: #172554;
            color: #bfdbfe;
            border: 1px solid #3b82f6;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 14px;
            font-size: 13px;
        }

        th, td {
            padding: 10px;
            border-bottom: 1px solid var(--border);
            text-align: left;
            vertical-align: top;
        }

        th {
            background: var(--panel-2);
            color: #93c5fd;
            position: sticky;
            top: 0;
        }

        tr:hover {
            background: #1e293b;
        }

        .table-wrap {
            max-height: 460px;
            overflow: auto;
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-top: 12px;
        }

        .quick-links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }

        .quick-links a {
            background: var(--panel-2);
            border: 1px solid var(--border);
            color: white;
            text-decoration: none;
            border-radius: 14px;
            padding: 15px;
        }

        .quick-links a:hover {
            border-color: #60a5fa;
            background: #1e293b;
        }

        .quick-links strong {
            display: block;
            margin-bottom: 5px;
        }

        .quick-links span {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.45;
        }

        .readonly-box {
            background: #020617;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 13px;
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.5;
            margin-top: 12px;
        }

        .danger-zone {
            border-color: #7f1d1d;
        }

        .small-note {
            font-size: 12px;
            color: #64748b;
            margin-top: 8px;
            line-height: 1.45;
        }

        @media(max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .header, .container {
                padding-left: 18px;
                padding-right: 18px;
            }
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <div class="top-row">
        <div>
            <div class="eyebrow">ADMIN OPERATIONS WORKSPACE</div>
            <h1>Setup & Asset Management</h1>
            <p>
                Configure the complete smart building structure from one professional workspace:
                clients, sites, buildings, floors, maps, rooms, gateways, device assignment, and provisioning readiness.
            </p>
        </div>

        <div class="header-actions">
            <a class="btn secondary" href="/admin">← Back to Admin Home</a>
            <button onclick="refreshAll()">Refresh Data</button>
        </div>
    </div>
</div>

<div class="container">

    <div class="note-card">
        <h2>Provisioning Readiness Notes</h2>
        <ul>
            <li><strong>Network requirement:</strong> During LILYGO provisioning, the Raspberry Pi backend and the LILYGO must be connected to the same local network.</li>
            <li><strong>Arduino firmware:</strong> The Wi-Fi SSID and password inside the Arduino code must match the Wi-Fi network used by the Raspberry Pi.</li>
            <li><strong>Correct setup order:</strong> Create client → site → building → floor → upload maps → draw rooms → configure gateway → provision LILYGO.</li>
            <li><strong>Room requirement:</strong> Rooms should exist before provisioning, because the LILYGO receives a valid room_id from the backend.</li>
            <li><strong>Swagger policy:</strong> Swagger remains only for developer testing. Normal setup should be completed from the Admin UI.</li>
        </ul>
    </div>

    <div class="progress-grid">
        <div class="step">
            <div class="num">01</div>
            <h3>Organization Setup</h3>
            <p>Create the client and site that own the building structure.</p>
        </div>

        <div class="step">
            <div class="num">02</div>
            <h3>Building Setup</h3>
            <p>Create buildings and floors under the selected site.</p>
        </div>

        <div class="step">
            <div class="num">03</div>
            <h3>Maps & Rooms</h3>
            <p>Upload maps and draw rooms before device provisioning.</p>
        </div>

        <div class="step">
            <div class="num">04</div>
            <h3>Gateway Setup</h3>
            <p>Create gateways, assign them to floors, and place them visually.</p>
        </div>

        <div class="step">
            <div class="num">05</div>
            <h3>Device Assignment</h3>
            <p>Assign existing provisioned devices to the correct rooms if needed.</p>
        </div>

        <div class="step">
            <div class="num">06</div>
            <h3>Go Live Check</h3>
            <p>Verify live floor view, gateway health, client access, alarms, and exports.</p>
        </div>
    </div>

    <div class="grid">

        <div class="card">
            <div class="card-header-line">
                <h2>Clients</h2>
                <span class="pill">CREATE / UPDATE / DELETE</span>
            </div>
            <div class="muted">Manage the customer or organization that owns the smart building deployment.</div>

            <label>New Client Name</label>
            <input id="clientName" placeholder="Example: GIU Berlin Client">

            <div class="row">
                <button class="success" onclick="createClient()">Create Client</button>
            </div>

            <label>Edit Existing Client</label>
            <select id="clientEditSelect"></select>

            <label>Updated Client Name</label>
            <input id="clientEditName" placeholder="Updated client name">

            <div class="row">
                <button onclick="updateClient()">Update Client</button>
                <button class="danger" onclick="deleteClient()">Delete Client</button>
            </div>

            <div id="clientStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Sites</h2>
                <span class="pill">SITE MAP SUPPORTED</span>
            </div>
            <div class="muted">Create and manage sites/campuses under the selected client. Upload the site map used by the Site Map Editor.</div>

            <label>Client</label>
            <select id="siteClientSelect"></select>

            <label>New Site Name</label>
            <input id="siteName" placeholder="Example: GIU Campus">

            <div class="row">
                <button class="success" onclick="createSite()">Create Site</button>
            </div>

            <label>Edit Existing Site</label>
            <select id="siteEditSelect"></select>

            <label>Updated Site Name</label>
            <input id="siteEditName" placeholder="Updated site name">

            <div class="row">
                <button onclick="updateSite()">Update Site</button>
                <button class="danger" onclick="deleteSite()">Delete Site</button>
            </div>

            <label>Upload Site Map</label>
            <select id="siteMapSelect"></select>
            <input id="siteMapFile" type="file" accept="image/*">

            <div class="row">
                <button class="warning" onclick="uploadSiteMap()">Upload Site Map</button>
                <button class="secondary" onclick="openSelectedSiteMapEditor()">Open Site Map Editor</button>
            </div>

            <div id="siteStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Buildings</h2>
                <span class="pill">MAP POLYGON READY</span>
            </div>
            <div class="muted">Create buildings under a site. Building polygons are drawn later using the Site Map Editor.</div>

            <label>Site</label>
            <select id="buildingSiteSelect"></select>

            <label>New Building Name</label>
            <input id="buildingName" placeholder="Example: Main Building">

            <div class="row">
                <button class="success" onclick="createBuilding()">Create Building</button>
            </div>

            <label>Edit Existing Building</label>
            <select id="buildingEditSelect"></select>

            <label>Updated Building Name</label>
            <input id="buildingEditName" placeholder="Updated building name">

            <div class="row">
                <button onclick="updateBuilding()">Update Building</button>
                <button class="danger" onclick="deleteBuilding()">Delete Building</button>
                <button class="secondary" onclick="openSelectedSiteMapEditor()">Draw Building on Site Map</button>
            </div>

            <div id="buildingStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Floors</h2>
                <span class="pill">FLOOR PLAN REQUIRED</span>
            </div>
            <div class="muted">Create floors under buildings and upload floor plans. Rooms are drawn using the Floor Editor.</div>

            <label>Building</label>
            <select id="floorBuildingSelect"></select>

            <label>New Floor Name</label>
            <input id="floorName" placeholder="Example: Floor 1">

            <label>Floor Number</label>
            <input id="floorNumber" placeholder="Example: 1">

            <div class="row">
                <button class="success" onclick="createFloor()">Create Floor</button>
            </div>

            <label>Edit Existing Floor</label>
            <select id="floorEditSelect"></select>

            <label>Updated Floor Name</label>
            <input id="floorEditName" placeholder="Updated floor name">

            <label>Updated Floor Number</label>
            <input id="floorEditNumber" placeholder="Updated floor number">

            <div class="row">
                <button onclick="updateFloor()">Update Floor</button>
                <button class="danger" onclick="deleteFloor()">Delete Floor</button>
            </div>

            <label>Upload Floor Plan</label>
            <select id="floorImageSelect"></select>
            <input id="floorImageFile" type="file" accept="image/*">

            <div class="row">
                <button class="warning" onclick="uploadFloorImage()">Upload Floor Plan</button>
                <button class="secondary" onclick="openSelectedFloorEditor()">Open Floor Editor</button>
            </div>

            <div id="floorStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Gateways</h2>
                <span class="pill">ASSIGN / PLACE / MONITOR</span>
            </div>
            <div class="muted">Create or update gateway records, assign them to a floor, and place them visually on the map.</div>

            <label>Existing Gateway</label>
            <select id="gatewayEditSelect" onchange="fillGatewayForm()"></select>

            <label>Gateway ID</label>
            <input id="gatewayId" placeholder="Example: GIU-BERLIN-GATEWAY">

            <label>Name</label>
            <input id="gatewayName" placeholder="Example: GIU Berlin Gateway">

            <label>Client</label>
            <select id="gatewayClientSelect"></select>

            <label>Site</label>
            <select id="gatewaySiteSelect"></select>

            <label>Building</label>
            <select id="gatewayBuildingSelect"></select>

            <label>Floor</label>
            <select id="gatewayFloorSelect"></select>

            <label>Position X</label>
            <input id="gatewayX" type="number" placeholder="Example: 200">

            <label>Position Y</label>
            <input id="gatewayY" type="number" placeholder="Example: 120">

            <label>Map Label</label>
            <input id="gatewayLabel" placeholder="Example: Main Corridor Gateway">

            <label>Location Note</label>
            <textarea id="gatewayNote" placeholder="Example: Mounted near the ceiling in the main corridor"></textarea>

            <div class="row">
                <button class="success" onclick="saveGateway()">Create / Update Gateway</button>
                <button class="danger" onclick="deleteGateway()">Delete Gateway</button>
                <button class="secondary" onclick="openSelectedGatewayPlacement()">Place Gateway</button>
                <a class="link-btn secondary" href="/gateway-monitor">Monitor Gateway</a>
            </div>

            <div id="gatewayStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Device Assignment</h2>
                <span class="pill">AFTER PROVISIONING</span>
            </div>
            <div class="muted">
                If a device was provisioned before the room was ready, assign it to the correct room here without using Swagger.
            </div>

            <label>Provisioned Device</label>
            <select id="deviceAssignSelect"></select>

            <label>Floor</label>
            <select id="deviceFloorSelect" onchange="loadRoomsForSelectedFloor()"></select>

            <label>Room</label>
            <select id="deviceRoomSelect"></select>

           <div class="row">
               <button class="success" onclick="assignDeviceToRoom()">Assign Device to Room</button>
               <button class="secondary" onclick="openSelectedFloorLiveViewFromDeviceAssignment()">Open Admin Live Floor View</button>
               <button class="secondary" onclick="openSelectedNodePlacement()">Open Node Placement</button>
               <button class="secondary" onclick="openSelectedDeviceCapabilities()">Device Capabilities</button>
            </div>

            <div class="readonly-box">
                Recommended flow: provision after rooms exist. This section is mainly for correction or reassignment.
            </div>

            <div id="deviceAssignStatus" class="status"></div>
        </div>

        <div class="card">
            <div class="card-header-line">
                <h2>Operational Links</h2>
                <span class="pill">GO LIVE CHECK</span>
            </div>
            <div class="muted">Use these pages after structure setup to verify the system is ready for live operation.</div>

            <div class="quick-links">
                <a href="/site-map-editor">
                    <strong>Site Map Editor</strong>
                    <span>Upload/view the site map and draw building polygons.</span>
                </a>

                <a href="/floor-editor">
                    <strong>Floor Editor</strong>
                    <span>Draw, update, or delete rooms on the floor plan.</span>
                </a>

                <a href="/admin/provision-options">
                    <strong>Provisioning Options</strong>
                    <span>Check the room IDs and node types sent to the LILYGO provisioning flow.</span>
                </a>

                <a href="/device-capabilities-manager">
                    <strong>Device Capabilities</strong>
                    <span>Change node type/capabilities and sync TTN formatter.</span>
                </a>

                <a href="#" onclick="openClientAccessForSelectedScope(); return false;">
                    <strong>Client Access Manager</strong>
                    <span>Create client login credentials and assign access permissions for the selected scope.</span>
                </a>

                <a href="/floor-live-view">
                    <strong>Admin Floor Live View</strong>
                    <span>Verify devices, rooms, gateways, alarms, battery, signal, and telemetry.</span>
                </a>

                <a href="/admin/audit-log">
                    <strong>Audit Log</strong>
                    <span>Review admin actions, movements, alarm actions, and permission changes.</span>
                </a>

                <a href="/alarms">
                    <strong>Alarm History</strong>
                    <span>Acknowledge, resolve, and export alarm records.</span>
                </a>
            </div>
        </div>

        <div class="card full">
            <div class="card-header-line">
                <h2>Deployment Structure Summary</h2>
                <span class="pill">LIVE DATABASE VIEW</span>
            </div>
            <div class="muted">
                This table confirms the configured clients, sites, buildings, floors, gateways, and devices currently available in the system.
            </div>

            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Parent / Details</th>
                        </tr>
                    </thead>
                    <tbody id="summaryTable"></tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<script>
let clients = [];
let sites = [];
let buildings = [];
let floors = [];
let gateways = [];
let devices = [];
let currentRooms = [];

function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showStatus(id, message, type="good") {
    const box = document.getElementById(id);
    box.className = "status " + type;
    box.innerText = message;
}

async function fetchJson(url, options={}) {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

function fillSelect(id, items, emptyText, labelFn=null) {
    const select = document.getElementById(id);
    if (!select) return;

    select.innerHTML = `<option value="">${escapeHtml(emptyText)}</option>`;

    items.forEach(item => {
        const label = labelFn ? labelFn(item) : (item.name || item.label || item.gateway_id || item.device_id || item.room_name || ("ID " + item.id));

        select.innerHTML += `
            <option value="${escapeHtml(item.id !== undefined ? item.id : item.device_id)}">
                ${escapeHtml(label)}
            </option>
        `;
    });
}

function getById(list, id) {
    return list.find(item => String(item.id) === String(id));
}

function getGatewayByDbId(id) {
    return gateways.find(item => String(item.id) === String(id));
}

function getDeviceById(deviceId) {
    return devices.find(item => String(item.device_id) === String(deviceId));
}

async function refreshAll() {
    try {
        clients = await fetchJson("/clients");
        sites = await fetchJson("/sites");
        buildings = await fetchJson("/buildings");
        floors = await fetchJson("/floors");
        gateways = await fetchJson("/gateways");
        devices = await fetchJson("/devices-status");

        fillAllDropdowns();
        renderSummary();

        const selectedFloor = document.getElementById("deviceFloorSelect").value;
        if (selectedFloor) {
            await loadRoomsForSelectedFloor();
        }

    } catch (err) {
        alert("Failed to load setup data: " + err.message);
    }
}

function fillAllDropdowns() {
    fillSelect("clientEditSelect", clients, "Select client");
    fillSelect("siteClientSelect", clients, "Select client");
    fillSelect("gatewayClientSelect", clients, "No client");

    fillSelect("siteEditSelect", sites, "Select site", s => {
        const client = getById(clients, s.client_id);
        return `${s.name} / Client: ${client ? client.name : s.client_id}`;
    });

    fillSelect("siteMapSelect", sites, "Select site");
    fillSelect("buildingSiteSelect", sites, "Select site");
    fillSelect("gatewaySiteSelect", sites, "No site");

    fillSelect("buildingEditSelect", buildings, "Select building", b => {
        const site = getById(sites, b.site_id);
        return `${b.name} / Site: ${site ? site.name : b.site_id}`;
    });

    fillSelect("floorBuildingSelect", buildings, "Select building");
    fillSelect("gatewayBuildingSelect", buildings, "No building");

    fillSelect("floorEditSelect", floors, "Select floor", f => {
        const building = getById(buildings, f.building_id);
        return `${f.name} / Building: ${building ? building.name : f.building_id}`;
    });

    fillSelect("floorImageSelect", floors, "Select floor");
    fillSelect("gatewayFloorSelect", floors, "No floor");

    fillSelect("gatewayEditSelect", gateways, "Create new gateway", g => {
        return `${g.name || g.gateway_id} / ${g.gateway_id}`;
    });

    fillSelect("deviceAssignSelect", devices, "Select provisioned device", d => {
        return `${d.label || d.device_id} / ${d.device_id}`;
    });

    fillSelect("deviceFloorSelect", floors, "Select floor", f => {
        const building = getById(buildings, f.building_id);
        return `${f.name} / ${building ? building.name : "Building " + f.building_id}`;
    });
}

function renderSummary() {
    const tbody = document.getElementById("summaryTable");
    tbody.innerHTML = "";

    if (!clients.length && !sites.length && !buildings.length && !floors.length && !gateways.length && !devices.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">No structure records found yet. Start by creating a client.</td>
            </tr>
        `;
        return;
    }

    clients.forEach(c => {
        tbody.innerHTML += `
            <tr>
                <td>Client</td>
                <td>${escapeHtml(c.id)}</td>
                <td>${escapeHtml(c.name)}</td>
                <td>Created: ${escapeHtml(c.created_at || "--")}</td>
            </tr>
        `;
    });

    sites.forEach(s => {
        const c = getById(clients, s.client_id);
        tbody.innerHTML += `
            <tr>
                <td>Site</td>
                <td>${escapeHtml(s.id)}</td>
                <td>${escapeHtml(s.name)}</td>
                <td>Client: ${escapeHtml(c ? c.name : s.client_id)} / Map: ${escapeHtml(s.campus_image_path || s.image_path || "--")}</td>
            </tr>
        `;
    });

    buildings.forEach(b => {
        const s = getById(sites, b.site_id);
        tbody.innerHTML += `
            <tr>
                <td>Building</td>
                <td>${escapeHtml(b.id)}</td>
                <td>${escapeHtml(b.name)}</td>
                <td>Site: ${escapeHtml(s ? s.name : b.site_id)} / Polygon: ${b.polygon_points && b.polygon_points.length ? "Configured" : "Not configured"}</td>
            </tr>
        `;
    });

    floors.forEach(f => {
        const b = getById(buildings, f.building_id);
        tbody.innerHTML += `
            <tr>
                <td>Floor</td>
                <td>${escapeHtml(f.id)}</td>
                <td>${escapeHtml(f.name)}</td>
                <td>Building: ${escapeHtml(b ? b.name : f.building_id)} / Floor No: ${escapeHtml(f.floor_number || "--")} / Image: ${escapeHtml(f.image_path || "--")}</td>
            </tr>
        `;
    });

    gateways.forEach(g => {
        tbody.innerHTML += `
            <tr>
                <td>Gateway</td>
                <td>${escapeHtml(g.id)}</td>
                <td>${escapeHtml(g.name || g.gateway_id)}</td>
                <td>Gateway ID: ${escapeHtml(g.gateway_id)} / Floor: ${escapeHtml(g.floor_id || "--")} / Position: ${escapeHtml(g.x || "--")}, ${escapeHtml(g.y || "--")}</td>
            </tr>
        `;
    });

    devices.forEach(d => {
        tbody.innerHTML += `
            <tr>
                <td>Device</td>
                <td>${escapeHtml(d.device_id)}</td>
                <td>${escapeHtml(d.label || d.device_id)}</td>
                <td>Type: ${escapeHtml(d.node_type)} / Room ID: ${escapeHtml(d.room_id || "--")} / Floor ID: ${escapeHtml(d.floor_id || "--")}</td>
                <td>
                    <button class="btn" style="background:#10b981; padding:4px 8px; font-size:12px;" onclick="openTelemetryGraph('${escapeHtml(d.device_id)}', '${escapeHtml(d.label || d.device_id)}')">
                        📉 Graphs
                    </button>
                </td>
            </tr>
        `;
    });
}

async function createClient() {
    const name = document.getElementById("clientName").value.trim();

    if (!name) {
        showStatus("clientStatus", "Client name is required.", "bad");
        return;
    }

    try {
        await fetchJson("/clients", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name})
        });

        document.getElementById("clientName").value = "";
        showStatus("clientStatus", "Client created successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("clientStatus", err.message, "bad");
    }
}

async function updateClient() {
    const id = document.getElementById("clientEditSelect").value;
    const name = document.getElementById("clientEditName").value.trim();

    if (!id || !name) {
        showStatus("clientStatus", "Select a client and enter the updated name.", "bad");
        return;
    }

    try {
        await fetchJson(`/clients/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name})
        });

        document.getElementById("clientEditName").value = "";
        showStatus("clientStatus", "Client updated successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("clientStatus", err.message, "bad");
    }
}

async function deleteClient() {
    const id = document.getElementById("clientEditSelect").value;

    if (!id) {
        showStatus("clientStatus", "Select a client first.", "bad");
        return;
    }

    if (!confirm("Delete this client? Related sites/buildings may become orphaned if they are not deleted first.")) {
        return;
    }

    try {
        await fetchJson(`/clients/${id}`, {method: "DELETE"});
        showStatus("clientStatus", "Client deleted.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("clientStatus", err.message, "bad");
    }
}

async function createSite() {
    const client_id = Number(document.getElementById("siteClientSelect").value);
    const name = document.getElementById("siteName").value.trim();

    if (!client_id || !name) {
        showStatus("siteStatus", "Select a client and enter the site name.", "bad");
        return;
    }

    try {
        await fetchJson("/sites", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({client_id, name})
        });

        document.getElementById("siteName").value = "";
        showStatus("siteStatus", "Site created successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("siteStatus", err.message, "bad");
    }
}

async function updateSite() {
    const id = document.getElementById("siteEditSelect").value;
    const name = document.getElementById("siteEditName").value.trim();

    if (!id || !name) {
        showStatus("siteStatus", "Select a site and enter the updated name.", "bad");
        return;
    }

    try {
        await fetchJson(`/sites/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name})
        });

        document.getElementById("siteEditName").value = "";
        showStatus("siteStatus", "Site updated successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("siteStatus", err.message, "bad");
    }
}

async function deleteSite() {
    const id = document.getElementById("siteEditSelect").value;

    if (!id) {
        showStatus("siteStatus", "Select a site first.", "bad");
        return;
    }

    if (!confirm("Delete this site? Delete or reassign buildings first if needed.")) {
        return;
    }

    try {
        await fetchJson(`/sites/${id}`, {method: "DELETE"});
        showStatus("siteStatus", "Site deleted.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("siteStatus", err.message, "bad");
    }
}

async function uploadSiteMap() {
    const siteId = document.getElementById("siteMapSelect").value;
    const file = document.getElementById("siteMapFile").files[0];

    if (!siteId || !file) {
        showStatus("siteStatus", "Select a site and choose a site map image.", "bad");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    try {
        const res = await fetch(`/sites/${siteId}/upload-site-map`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Site map upload failed");
        }

        document.getElementById("siteMapFile").value = "";
        showStatus("siteStatus", "Site map uploaded successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("siteStatus", err.message, "bad");
    }
}

async function createBuilding() {
    const site_id = Number(document.getElementById("buildingSiteSelect").value);
    const name = document.getElementById("buildingName").value.trim();

    if (!site_id || !name) {
        showStatus("buildingStatus", "Select a site and enter the building name.", "bad");
        return;
    }

    try {
        await fetchJson("/buildings", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({site_id, name})
        });

        document.getElementById("buildingName").value = "";
        showStatus("buildingStatus", "Building created successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("buildingStatus", err.message, "bad");
    }
}

async function updateBuilding() {
    const id = document.getElementById("buildingEditSelect").value;
    const name = document.getElementById("buildingEditName").value.trim();

    if (!id || !name) {
        showStatus("buildingStatus", "Select a building and enter the updated name.", "bad");
        return;
    }

    try {
        await fetchJson(`/buildings/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name})
        });

        document.getElementById("buildingEditName").value = "";
        showStatus("buildingStatus", "Building updated successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("buildingStatus", err.message, "bad");
    }
}

async function deleteBuilding() {
    const id = document.getElementById("buildingEditSelect").value;

    if (!id) {
        showStatus("buildingStatus", "Select a building first.", "bad");
        return;
    }

    if (!confirm("Delete this building? Delete or reassign floors first if needed.")) {
        return;
    }

    try {
        await fetchJson(`/buildings/${id}`, {method: "DELETE"});
        showStatus("buildingStatus", "Building deleted.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("buildingStatus", err.message, "bad");
    }
}

async function createFloor() {
    const building_id = Number(document.getElementById("floorBuildingSelect").value);
    const name = document.getElementById("floorName").value.trim();
    const floor_number = document.getElementById("floorNumber").value.trim();

    if (!building_id || !name) {
        showStatus("floorStatus", "Select a building and enter the floor name.", "bad");
        return;
    }

    try {
        await fetchJson("/floors", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({building_id, name, floor_number})
        });

        document.getElementById("floorName").value = "";
        document.getElementById("floorNumber").value = "";
        showStatus("floorStatus", "Floor created successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("floorStatus", err.message, "bad");
    }
}

async function updateFloor() {
    const id = document.getElementById("floorEditSelect").value;
    const name = document.getElementById("floorEditName").value.trim();
    const floor_number = document.getElementById("floorEditNumber").value.trim();

    if (!id || !name) {
        showStatus("floorStatus", "Select a floor and enter the updated name.", "bad");
        return;
    }

    try {
        await fetchJson(`/floors/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, floor_number})
        });

        document.getElementById("floorEditName").value = "";
        document.getElementById("floorEditNumber").value = "";
        showStatus("floorStatus", "Floor updated successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("floorStatus", err.message, "bad");
    }
}

async function deleteFloor() {
    const id = document.getElementById("floorEditSelect").value;

    if (!id) {
        showStatus("floorStatus", "Select a floor first.", "bad");
        return;
    }

    if (!confirm("Delete this floor? Delete or reassign rooms/devices first if needed.")) {
        return;
    }

    try {
        await fetchJson(`/floors/${id}`, {method: "DELETE"});
        showStatus("floorStatus", "Floor deleted.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("floorStatus", err.message, "bad");
    }
}

async function uploadFloorImage() {
    const floorId = document.getElementById("floorImageSelect").value;
    const file = document.getElementById("floorImageFile").files[0];

    if (!floorId || !file) {
        showStatus("floorStatus", "Select a floor and choose a floor plan image.", "bad");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    try {
        const res = await fetch(`/floors/${floorId}/upload-image`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Floor image upload failed");
        }

        document.getElementById("floorImageFile").value = "";
        showStatus("floorStatus", "Floor plan uploaded successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("floorStatus", err.message, "bad");
    }
}

function fillGatewayForm() {
    const id = document.getElementById("gatewayEditSelect").value;

    if (!id) {
        document.getElementById("gatewayId").value = "";
        document.getElementById("gatewayName").value = "";
        document.getElementById("gatewayClientSelect").value = "";
        document.getElementById("gatewaySiteSelect").value = "";
        document.getElementById("gatewayBuildingSelect").value = "";
        document.getElementById("gatewayFloorSelect").value = "";
        document.getElementById("gatewayX").value = "";
        document.getElementById("gatewayY").value = "";
        document.getElementById("gatewayLabel").value = "";
        document.getElementById("gatewayNote").value = "";
        return;
    }

    const gw = getGatewayByDbId(id);

    if (!gw) return;

    document.getElementById("gatewayId").value = gw.gateway_id || "";
    document.getElementById("gatewayName").value = gw.name || "";
    document.getElementById("gatewayClientSelect").value = gw.client_id || "";
    document.getElementById("gatewaySiteSelect").value = gw.site_id || "";
    document.getElementById("gatewayBuildingSelect").value = gw.building_id || "";
    document.getElementById("gatewayFloorSelect").value = gw.floor_id || "";
    document.getElementById("gatewayX").value = gw.x || "";
    document.getElementById("gatewayY").value = gw.y || "";
    document.getElementById("gatewayLabel").value = gw.label || "";
    document.getElementById("gatewayNote").value = gw.location_note || "";
}

async function saveGateway() {
    const gateway_id = document.getElementById("gatewayId").value.trim();
    const name = document.getElementById("gatewayName").value.trim();

    if (!gateway_id) {
        showStatus("gatewayStatus", "Gateway ID is required.", "bad");
        return;
    }

    const payload = {
        gateway_id,
        name: name || gateway_id,
        client_id: document.getElementById("gatewayClientSelect").value ? Number(document.getElementById("gatewayClientSelect").value) : null,
        site_id: document.getElementById("gatewaySiteSelect").value ? Number(document.getElementById("gatewaySiteSelect").value) : null,
        building_id: document.getElementById("gatewayBuildingSelect").value ? Number(document.getElementById("gatewayBuildingSelect").value) : null,
        floor_id: document.getElementById("gatewayFloorSelect").value ? Number(document.getElementById("gatewayFloorSelect").value) : null,
        x: document.getElementById("gatewayX").value ? Number(document.getElementById("gatewayX").value) : null,
        y: document.getElementById("gatewayY").value ? Number(document.getElementById("gatewayY").value) : null,
        label: document.getElementById("gatewayLabel").value.trim(),
        location_note: document.getElementById("gatewayNote").value.trim()
    };

    try {
        await fetchJson("/gateways", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        showStatus("gatewayStatus", "Gateway saved successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("gatewayStatus", err.message, "bad");
    }
}

async function deleteGateway() {
    const dbId = document.getElementById("gatewayEditSelect").value;

    if (!dbId) {
        showStatus("gatewayStatus", "Select an existing gateway first.", "bad");
        return;
    }

    const gw = getGatewayByDbId(dbId);

    if (!gw) {
        showStatus("gatewayStatus", "Gateway not found in loaded data.", "bad");
        return;
    }

    if (!confirm("Delete gateway: " + gw.gateway_id + "?")) {
        return;
    }

    try {
        await fetchJson(`/gateways/${encodeURIComponent(gw.gateway_id)}`, {
            method: "DELETE"
        });

        showStatus("gatewayStatus", "Gateway deleted.", "good");
        await refreshAll();
        fillGatewayForm();

    } catch (err) {
        showStatus("gatewayStatus", err.message, "bad");
    }
}

async function loadRoomsForSelectedFloor() {
    const floorId = document.getElementById("deviceFloorSelect").value;

    currentRooms = [];
    fillSelect("deviceRoomSelect", [], "Select room");

    if (!floorId) {
        showStatus("deviceAssignStatus", "Select a floor to load rooms.", "info");
        return;
    }

    try {
        currentRooms = await fetchJson(`/floors/${floorId}/rooms`);

        fillSelect("deviceRoomSelect", currentRooms, "Select room", r => {
            return `${r.room_name} / Room ID ${r.id}`;
        });

        if (!currentRooms.length) {
            showStatus("deviceAssignStatus", "No rooms found on this floor. Open Floor Editor and draw rooms first.", "info");
        } else {
            showStatus("deviceAssignStatus", `${currentRooms.length} room(s) loaded for selected floor.`, "good");
        }

    } catch (err) {
        showStatus("deviceAssignStatus", err.message, "bad");
    }
}

async function assignDeviceToRoom() {
    const deviceId = document.getElementById("deviceAssignSelect").value;
    const roomId = document.getElementById("deviceRoomSelect").value;

    if (!deviceId || !roomId) {
        showStatus("deviceAssignStatus", "Select a device and a room first.", "bad");
        return;
    }

    try {
        await fetchJson(`/rooms/${roomId}/devices`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({device_id: deviceId})
        });

        showStatus("deviceAssignStatus", "Device assigned to room successfully.", "good");
        await refreshAll();

    } catch (err) {
        showStatus("deviceAssignStatus", err.message, "bad");
    }
}

function openSelectedFloorEditor() {
    const floorId =
        document.getElementById("floorImageSelect").value ||
        document.getElementById("floorEditSelect").value ||
        document.getElementById("deviceFloorSelect").value;

    if (!floorId) {
        showStatus("floorStatus", "Select a floor first, then open Floor Editor.", "bad");
        return;
    }

    window.location.href = `/floor-editor?floor_id=${encodeURIComponent(floorId)}`;
}
function openSelectedSiteMapEditor() {
    const siteId =
        document.getElementById("siteMapSelect").value ||
        document.getElementById("siteEditSelect").value ||
        document.getElementById("buildingSiteSelect").value ||
        document.getElementById("gatewaySiteSelect").value;

    if (!siteId) {
        showStatus("siteStatus", "Select a site first, then open Site Map Editor.", "bad");
        return;
    }

    window.location.href = `/site-map-editor?site_id=${encodeURIComponent(siteId)}`;
}
function openSelectedGatewayPlacement() {
    const floorId =
        document.getElementById("gatewayFloorSelect").value ||
        document.getElementById("floorImageSelect").value ||
        document.getElementById("floorEditSelect").value ||
        document.getElementById("deviceFloorSelect").value;

    if (!floorId) {
        showStatus("gatewayStatus", "Select a floor first, then open Gateway Placement.", "bad");
        return;
    }

    window.location.href = `/admin/gateway-placement?floor_id=${encodeURIComponent(floorId)}`;
}
function openSelectedNodePlacement() {
    const floorId =
        document.getElementById("deviceFloorSelect").value ||
        document.getElementById("floorImageSelect").value ||
        document.getElementById("floorEditSelect").value ||
        document.getElementById("gatewayFloorSelect").value;

    if (!floorId) {
        showStatus("deviceAssignStatus", "Select a floor first, then open Node Placement.", "bad");
        return;
    }

    window.location.href = `/node-placement-editor?floor_id=${encodeURIComponent(floorId)}`;
}
function openSelectedFloorLiveViewFromDeviceAssignment() {
    const floorId = document.getElementById("deviceFloorSelect").value;

    if (!floorId) {
        showStatus("deviceAssignStatus", "Select a floor first, then open Admin Live Floor View.", "bad");
        return;
    }

    window.location.href = `/floor-live-view?floor_id=${encodeURIComponent(floorId)}`;
}
function openSelectedDeviceCapabilities() {
    const deviceId = document.getElementById("deviceAssignSelect").value;

    if (!deviceId) {
        showStatus("deviceAssignStatus", "Select a device first, then open Device Capabilities.", "bad");
        return;
    }

    window.location.href = `/device-capabilities-manager?device_id=${encodeURIComponent(deviceId)}`;
}

function openClientAccessForSelectedScope() {
    let clientId =
        document.getElementById("gatewayClientSelect").value ||
        document.getElementById("siteClientSelect").value ||
        document.getElementById("clientEditSelect").value;

    let siteId =
        document.getElementById("gatewaySiteSelect").value ||
        document.getElementById("buildingSiteSelect").value ||
        document.getElementById("siteMapSelect").value ||
        document.getElementById("siteEditSelect").value;

    let buildingId =
        document.getElementById("gatewayBuildingSelect").value ||
        document.getElementById("floorBuildingSelect").value ||
        document.getElementById("buildingEditSelect").value;

    let floorId =
        document.getElementById("deviceFloorSelect").value ||
        document.getElementById("gatewayFloorSelect").value ||
        document.getElementById("floorImageSelect").value ||
        document.getElementById("floorEditSelect").value;

    // If floor selected, derive building/site/client automatically.
    if (floorId) {
        const floor = getById(floors, floorId);

        if (floor) {
            buildingId = floor.building_id || buildingId;

            const building = getById(buildings, buildingId);

            if (building) {
                siteId = building.site_id || siteId;

                const site = getById(sites, siteId);

                if (site) {
                    clientId = site.client_id || clientId;
                }
            }
        }
    }

    // If building selected, derive site/client automatically.
    else if (buildingId) {
        const building = getById(buildings, buildingId);

        if (building) {
            siteId = building.site_id || siteId;

            const site = getById(sites, siteId);

            if (site) {
                clientId = site.client_id || clientId;
            }
        }
    }

    // If site selected, derive client automatically.
    else if (siteId) {
        const site = getById(sites, siteId);

        if (site) {
            clientId = site.client_id || clientId;
        }
    }

    const query = new URLSearchParams();

    if (clientId) query.set("client_id", clientId);
    if (siteId) query.set("site_id", siteId);
    if (buildingId) query.set("building_id", buildingId);
    if (floorId) query.set("floor_id", floorId);

    window.location.href = "/admin/client-access" + (query.toString() ? "?" + query.toString() : "");
}

document.addEventListener("DOMContentLoaded", refreshAll);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""
    return HTMLResponse(html)

@router.get("/admin", response_class=HTMLResponse)
def admin_home_page():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Building Admin</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
        }

        .header {
            padding: 28px 36px;
            background: #111827;
            border-bottom: 1px solid #334155;
        }

        .header h1 {
            margin: 0;
            font-size: 32px;
        }

        .header p {
            margin: 10px 0 0;
            color: #94a3b8;
            font-size: 16px;
        }

        .section {
            padding: 30px 36px 10px;
        }

        .section h2 {
            margin: 0 0 18px;
            font-size: 22px;
            color: #e5e7eb;
        }
        .summary-grid {
           display: grid;
           grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
           gap: 16px;
           padding: 28px 36px 5px;
}

.summary-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.22);
}

        .summary-title {
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 8px;
}

        .summary-value {
    font-size: 30px;
    font-weight: bold;
}

        .summary-sub {
    margin-top: 6px;
    font-size: 12px;
    color: #94a3b8;
}

        .good {
    color: #86efac;
}

        .bad {
    color: #fecaca;
}

        .warn {
    color: #fde68a;
}

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
        }

        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 22px;
            text-decoration: none;
            color: white;
            box-shadow: 0 10px 24px rgba(0,0,0,0.25);
            transition: 0.15s ease;
        }

        .card:hover {
            transform: translateY(-3px);
            border-color: #38bdf8;
            background: #243247;
        }

        .card h3 {
            margin: 0 0 10px;
            font-size: 21px;
        }

        .card p {
            margin: 0;
            color: #94a3b8;
            line-height: 1.45;
        }

        .badge {
            display: inline-block;
            margin-bottom: 12px;
            padding: 5px 10px;
            border-radius: 20px;
            background: #0f172a;
            color: #93c5fd;
            font-size: 12px;
            font-weight: bold;
        }

        .tools {
            padding: 10px 36px 36px;
        }

        .quick-box {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 22px;
            margin-top: 18px;
        }

        .quick-box h3 {
            margin: 0 0 14px;
        }

        .row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }

        input {
            background: #0f172a;
            color: white;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 12px;
            min-width: 180px;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: bold;
        }

        button:hover {
            background: #1d4ed8;
        }

        .logout-btn {
            display: inline-block;
            margin-top: 16px;
            padding: 10px 15px;
            border-radius: 8px;
            background: #dc2626;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }

        .logout-btn:hover {
            background: #b91c1c;
        }
    </style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

    <div class="header">
        <h1>Smart Building Management Admin</h1>
        <p>Central control page for provisioning, monitoring, maps, gateways, devices, and alarms.</p>
        <a class="logout-btn" href="/logout">Logout</a>
    </div>
    <div class="summary-grid">
    <div class="summary-card">
        <div class="summary-title">Clients</div>
        <div class="summary-value" id="sumClients">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Sites</div>
        <div class="summary-value" id="sumSites">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Buildings</div>
        <div class="summary-value" id="sumBuildings">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Rooms</div>
        <div class="summary-value" id="sumRooms">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Devices Online</div>
        <div class="summary-value good" id="sumDevicesOnline">--</div>
        <div class="summary-sub" id="sumDevicesTotal">Total: --</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Devices Offline</div>
        <div class="summary-value bad" id="sumDevicesOffline">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Active Alarms</div>
        <div class="summary-value warn" id="sumAlarms">--</div>
    </div>

    <div class="summary-card">
        <div class="summary-title">Gateways Online</div>
        <div class="summary-value good" id="sumGatewaysOnline">--</div>
        <div class="summary-sub" id="sumGatewaysTotal">Total: --</div>
    </div>
</div>

    <div class="section">
        <h2>Live Monitoring</h2>

        <div class="grid">
            <a class="card" href="/floor-live-view">
                <span class="badge">LIVE</span>
                <h3>Floor Live View</h3>
                <p>View rooms, devices, live telemetry, alarms, and online/offline status.</p>
            </a>

            <a class="card" href="/gateway-monitor">
                <span class="badge">LIVE</span>
                <h3>Gateway Monitor</h3>
                <p>Monitor TTN gateway connection status, last uplink, protocol, and IP.</p>
            </a>

            <a class="card" href="/admin/setup">
                <span class="badge">SETUP</span>
                <h3>Admin Setup Manager</h3>
                <p>Create clients, sites, buildings, floors, upload maps, create gateways, and prepare the system before provisioning LILYGO nodes.</p>
            </a>

            <a class="card" href="/admin/gateway-placement">
                <span class="badge">GATEWAYS</span>
                <h3>Gateway Placement</h3>
                <p>Place gateways on floor maps, edit their location, and view online/offline status.</p>
            </a>

            <a class="card" href="/admin/alarms">

                <span class="badge">ALARMS</span>
                <h3>Alarm History</h3>
                <p>View active, acknowledged, and resolved alarms with timestamps and telemetry.</p>
            </a>

            <a class="card" href="/admin/client-access">
                <span class="badge">ACCESS</span>
                <h3>Client Access Manager</h3>
                <p>Create client users and control which client, site, building, or floor they can view.</p>
            </a>

            <a class="card" href="/device-capabilities-manager">
                <span class="badge">DEVICES</span>
                <h3>Device Capabilities</h3>
                <p>Set environment, energy, safety, and occupancy capabilities for each node.</p>
            </a>

            <a class="card" href="/admin/audit-log">
                <div class="card-icon">📜</div>
                <h3>Audit Log</h3>
                <p>View admin actions, alarm actions, gateway/device movements, access changes, and system activity.</p>
                <span class="card-link">Open Audit Log →</span>
            </a>
        </div>
    </div>

        <div class="section">
        <h2>Exports & Reports</h2>

        <div class="grid">
            <a class="card" href="/admin/export/full-structure.csv">
                <span class="badge">CSV</span>
                <h3>Full Structure Export</h3>
                <p>Export all clients, sites, buildings, floors, rooms, devices, and gateways in one organized hierarchy CSV.</p>
            </a>

            <a class="card" href="/admin/export/device-inventory.csv">
                <span class="badge">CSV</span>
                <h3>Device Inventory Export</h3>
                <p>Export all nodes with DevEUI, type, location, battery, signal, alarm state, telemetry source, and latest telemetry.</p>
            </a>

            <a class="card" href="/alarms/export.csv?limit=5000">
                <span class="badge">CSV</span>
                <h3>Alarm History Export</h3>
                <p>Export alarm history including active, acknowledged, resolved alarms, timestamps, and telemetry.</p>
            </a>

            <a class="card" href="/audit-log/export.csv?limit=5000">
                <span class="badge">CSV</span>
                <h3>Audit Log Export</h3>
                <p>Export admin actions, alarm actions, device/gateway movement logs, and access permission changes.</p>
            </a>
        </div>
    </div>

    <div class="section">
        <h2>Map & Layout Tools</h2>

        <div class="grid">
            <a class="card" href="/site-map-editor">
                <span class="badge">SITE</span>
                <h3>Site Map Editor</h3>
                <p>Upload site/campus map and draw building polygons.</p>
            </a>

            <a class="card" href="/floor-editor">
                <span class="badge">FLOOR</span>
                <h3>Floor Editor</h3>
                <p>Upload floor images and draw room polygons.</p>
            </a>

            <a class="card" href="/node-placement-editor">
                <span class="badge">NODES</span>
                <h3>Node Placement</h3>
                <p>Drag and position devices on the floor map.</p>
            </a>
        </div>
    </div>

    <div class="section">
        <h2>System & Configuration</h2>

        <div class="grid">
            <a class="card" href="/sensor-profile-manager">
                <span class="badge">SENSORS</span>
                <h3>Sensor Profiles</h3>
                <p>Create, clone, enable, disable, and manage supported sensor profiles.</p>
            </a>

            <a class="card" href="/sensor-catalog-manager">
                <span class="badge">CATALOG</span>
                <h3>Sensor Catalog</h3>
                <p>Register and manage physical sensor models available to firmware profiles.</p>
            </a>

            <a class="card" href="/firmware-module-manager">
                <span class="badge">FIRMWARE</span>
                <h3>Firmware Modules</h3>
                <p>Register and manage sensor drivers already compiled into LILYGO firmware.</p>
            </a>

            <a class="card" href="/alarm-settings-page">
                <span class="badge">ALARMS</span>
                <h3>Alarm Settings</h3>
                <p>Manage alert email recipients and alarm email templates.</p>
            </a>

            <a class="card" href="/docs">
                <span class="badge">API</span>
                <h3>Swagger API</h3>
                <p>Open backend API documentation and test endpoints.</p>
            </a>

            <a class="card" href="/admin/provision-options">
                <span class="badge">PROVISION</span>
                <h3>Node Provisioning Options</h3>
                <p>Check node types, buildings, floors, rooms, and room IDs sent to LILYGO.</p>
            </a>
        </div>
    </div>

   

    <script>
    
    async function loadAdminSummary() {
    try {
        const res = await fetch("/admin/summary");

        if (!res.ok) {
            throw new Error("Failed to load summary");
        }

        const data = await res.json();

        document.getElementById("sumClients").innerText = data.clients;
        document.getElementById("sumSites").innerText = data.sites;
        document.getElementById("sumBuildings").innerText = data.buildings;
        document.getElementById("sumRooms").innerText = data.rooms;

        document.getElementById("sumDevicesOnline").innerText = data.devices.online;
        document.getElementById("sumDevicesOffline").innerText = data.devices.offline;
        document.getElementById("sumDevicesTotal").innerText = "Total: " + data.devices.total;

        document.getElementById("sumAlarms").innerText = data.devices.active_alarms;

        document.getElementById("sumGatewaysOnline").innerText = data.gateways.online;
        document.getElementById("sumGatewaysTotal").innerText = "Total: " + data.gateways.total;

    } catch (err) {
        console.error("Admin summary error:", err);
    }
}
    
        
        
        loadAdminSummary();
        setInterval(loadAdminSummary, 10000);
    </script>
    

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
    """

    return HTMLResponse(html)

@router.get("/node-placement-editor", response_class=HTMLResponse)
def node_placement_editor():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Node Placement Editor</title>
    <link rel="manifest" href="/uploads/manifest.json">
    <meta name="theme-color" content="#08111f">
    <meta name="apple-mobile-web-app-capable" content="yes">

<style>
body{
    margin:0;
    font-family:Arial, sans-serif;
    background:#0f172a;
    color:#e5e7eb;
}

.header{
    padding:24px 34px;
    background:#111827;
    border-bottom:1px solid #334155;
}

.header h1{
    margin:0;
    font-size:28px;
    color:#f8fafc;
}

.header p{
    margin:8px 0 0;
    color:#94a3b8;
}

.toolbar{
    padding:16px 34px;
    background:#0f172a;
    border-bottom:1px solid #1e293b;
    display:flex;
    gap:12px;
    align-items:center;
    flex-wrap:wrap;
}

.toolbar label{
    color:#cbd5e1;
    font-weight:bold;
}

.toolbar input,
.toolbar button{
    width:auto;
    padding:10px 13px;
    border-radius:8px;
    border:1px solid #334155;
    font-size:14px;
}

.toolbar input{
    background:#020617;
    color:white;
}

.toolbar button{
    border:none;
    cursor:pointer;
    font-weight:bold;
    color:white;
    background:#2563eb;
}

.toolbar button:hover{
    background:#1d4ed8;
}

.adminHomeBtn{
    background:#334155 !important;
}

.adminHomeBtn:hover{
    background:#475569 !important;
}

.layout{
    display:flex;
    height:calc(100vh - 152px);
}

.mapArea{
    flex:1;
    position:relative;
    overflow:auto;
    padding:24px 34px;
}

.canvasBox{
    position:relative;
    width:calc(100vw - 430px);
    background:#111827;
    border:1px solid #334155;
    border-radius:16px;
    padding:14px;
    box-shadow:0 16px 40px rgba(0,0,0,0.35);
}

#floorImage{
    width:100%;
    height:auto;
    display:block;
    border:1px solid #334155;
    border-radius:12px;
    background:#020617;
    opacity:0.92;
}

#overlay{
    position:absolute;
    top:14px;
    left:14px;
    width:calc(100% - 28px);
    height:calc(100% - 28px);
}

#nodesLayer{
    position:absolute;
    top:14px;
    left:14px;
    width:calc(100% - 28px);
    height:calc(100% - 28px);
}

.roomPolygon{
    fill:rgba(37,99,235,0.18);
    stroke:#60a5fa;
    stroke-width:3;
}

.roomLabel{
    fill:#93c5fd;
    font-size:15px;
    font-weight:bold;
    paint-order:stroke;
    stroke:#020617;
    stroke-width:3px;
}

.node{
    position:absolute;
    transform:translate(-50%, -50%);
    padding:8px 12px;
    border-radius:999px;
    background:#16a34a;
    color:white;
    font-weight:bold;
    font-size:12px;
    cursor:grab;
    z-index:20;
    white-space:nowrap;
    box-shadow:0 8px 20px rgba(0,0,0,.45);
    border:1px solid rgba(255,255,255,0.25);
}

.node.selected{
    outline:4px solid #f59e0b;
}

.sidePanel{
    width:330px;
    background:#111827;
    border-left:1px solid #334155;
    padding:18px;
    overflow:auto;
    box-shadow:-8px 0 24px rgba(0,0,0,0.25);
}

.sidePanel h2{
    margin-top:0;
    color:#f8fafc;
}

.sidePanel h3{
    color:#93c5fd;
}

.deviceItem{
    padding:10px;
    border-radius:8px;
    background:#020617;
    border:1px solid #334155;
    margin-bottom:8px;
    cursor:pointer;
    color:#e5e7eb;
}

.deviceItem:hover{
    background:#1e293b;
}

.deviceItem.active{
    background:#78350f;
    border-color:#f59e0b;
    font-weight:bold;
}

.sidePanel label{
    color:#cbd5e1;
    font-size:14px;
    font-weight:bold;
}

.sidePanel input,
.sidePanel select,
.sidePanel button{
    width:100%;
    box-sizing:border-box;
    padding:10px;
    margin-top:8px;
    margin-bottom:10px;
    border-radius:8px;
}

.sidePanel input,
.sidePanel select{
    border:1px solid #334155;
    background:#020617;
    color:white;
}

.sidePanel button{
    border:none;
    background:#2563eb;
    color:white;
    font-weight:bold;
    cursor:pointer;
}

.sidePanel button:hover{
    background:#1d4ed8;
}

.saveBtn{
    background:#16a34a !important;
}

.saveBtn:hover{
    background:#15803d !important;
}

.resetBtn{
    background:#64748b !important;
}

.resetBtn:hover{
    background:#475569 !important;
}

.hint{
    font-size:12px;
    color:#94a3b8;
    line-height:1.5;
}

hr{
    border:none;
    border-top:1px solid #334155;
    margin:16px 0;
}
</style>
<link rel="stylesheet" href="/uploads/bright_theme.css">
</head>

<body>

<div class="header">
    <h1>Node Placement Editor</h1>
    <p>Drag devices on the floor map, assign them to rooms, and save their final positions.</p>
</div>

<div class="toolbar">
    <button class="adminHomeBtn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>

    <label>Floor:</label>
    <select id="floorId" onchange="loadFloor()"></select>
</div>
<div class="layout">

    <div class="mapArea">
        <div class="canvasBox" id="canvasBox">
            <img id="floorImage">
            <svg id="overlay"></svg>
            <div id="nodesLayer"></div>
        </div>
    </div>

    <div class="sidePanel">
        <h2>Node Placement</h2>

        <h3>Devices</h3>
        <div id="deviceList"></div>

        <hr>

        <label>Selected Device</label>
        <input id="selectedDeviceName" readonly>

        <label>Assign To Room</label>
        <select id="roomSelect"></select>

        <button onclick="assignToRoom()">Assign To Room Center</button>
        <button class="saveBtn" onclick="savePosition()">Save Current Position</button>
        <button class="resetBtn" onclick="resetToRoomCenter()">Reset To Room Center</button>

        <p class="hint">
            Drag node on the map, then press Save Current Position.
            If no position exists, node appears at room center.
        </p>
    </div>

</div>

<script>
let floorData = null;
let selectedDevice = null;
let selectedNodeEl = null;
let dragging = false;
let dragDevice = null;

const image = document.getElementById("floorImage");
const overlay = document.getElementById("overlay");
const nodesLayer = document.getElementById("nodesLayer");

function iconFor(type){
    if(type === "environment") return "🌡";
    if(type === "occupancy") return "👤";
    if(type === "safety") return "🔥";
    if(type === "energy") return "⚡";
    return "📡";
}

function originalToDisplay(p){
    return {
        x: p.x * image.clientWidth / floorData.floor.image_width,
        y: p.y * image.clientHeight / floorData.floor.image_height
    };
}

function displayToOriginal(x, y){
    return {
        x: Math.round(x * floorData.floor.image_width / image.clientWidth),
        y: Math.round(y * floorData.floor.image_height / image.clientHeight)
    };
}

async function loadFloor(){
    const floorId = document.getElementById("floorId").value;

    if (!floorId) {
        return;
    }

    selectedDevice = null;
    selectedNodeEl = null;
    dragDevice = null;

    document.getElementById("selectedDeviceName").value = "";
    document.getElementById("deviceList").innerHTML = "";
    document.getElementById("roomSelect").innerHTML = "";
    nodesLayer.innerHTML = "";
    overlay.innerHTML = "";

    const res = await fetch(`/floors/${floorId}/live`);
    floorData = await res.json();

    image.src = floorData.floor.image_path;

    image.onload = function(){
        overlay.setAttribute("width", image.clientWidth);
        overlay.setAttribute("height", image.clientHeight);

        drawRooms();
        drawNodes();
        renderDeviceList();
        renderRoomSelect();
    };

    if(image.complete){
        drawRooms();
        drawNodes();
        renderDeviceList();
        renderRoomSelect();
    }
}

function allDevices(){
    let devices = [];

    floorData.rooms.forEach(room => {
        room.devices.forEach(device => {
            device._room = room;
            devices.push(device);
        });
    });

    return devices;
}

function drawRooms(){
    overlay.innerHTML = "";

    floorData.rooms.forEach(room => {
        if(!room.polygon_points || room.polygon_points.length < 3) return;

        const pts = room.polygon_points.map(originalToDisplay);

        const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        poly.setAttribute("points", pts.map(p => `${p.x},${p.y}`).join(" "));
        poly.setAttribute("class", "roomPolygon");
        overlay.appendChild(poly);

        const center = originalToDisplay({x: room.x, y: room.y});

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", center.x);
        label.setAttribute("y", center.y);
        label.setAttribute("class", "roomLabel");
        label.textContent = room.room_name;
        overlay.appendChild(label);
    });
}

function drawNodes(){
    nodesLayer.innerHTML = "";

    allDevices().forEach(device => {
        const node = document.createElement("div");

        const room = device._room;

        const px = device.x || room.x;
        const py = device.y || room.y;

        const pos = originalToDisplay({x:px, y:py});

        node.className = "node";
        node.style.left = pos.x + "px";
        node.style.top = pos.y + "px";

        node.innerText =
            iconFor(device.node_type) + " " + (device.label || device.device_id);

        node.onmousedown = function(e){
            e.preventDefault();
            selectDevice(device, node);
            dragging = true;
            dragDevice = device;
            node.style.cursor = "grabbing";
        };

        node.onclick = function(e){
            e.stopPropagation();
            selectDevice(device, node);
        };

        nodesLayer.appendChild(node);
    });
}

document.addEventListener("mousemove", function(e){
    if(!dragging || !dragDevice || !selectedNodeEl) return;

    const rect = nodesLayer.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    selectedNodeEl.style.left = x + "px";
    selectedNodeEl.style.top = y + "px";

    const original = displayToOriginal(x, y);

    dragDevice.x = original.x;
    dragDevice.y = original.y;
});

document.addEventListener("mouseup", function(){
    if(selectedNodeEl){
        selectedNodeEl.style.cursor = "grab";
    }

    dragging = false;
    dragDevice = null;
});

function selectDevice(device, nodeEl){
    selectedDevice = device;

    if(selectedNodeEl){
        selectedNodeEl.classList.remove("selected");
    }

    selectedNodeEl = nodeEl;

    if(selectedNodeEl){
        selectedNodeEl.classList.add("selected");
    }

    document.getElementById("selectedDeviceName").value =
        device.label || device.device_id;

    document.getElementById("roomSelect").value =
        device.room_id || "";
        
    renderDeviceList();
}

function renderDeviceList(){
    const list = document.getElementById("deviceList");
    list.innerHTML = "";

    allDevices().forEach(device => {
        const div = document.createElement("div");

        div.className =
            "deviceItem" +
            (selectedDevice && selectedDevice.device_id === device.device_id ? " active" : "");

        div.innerText =
            iconFor(device.node_type) + " " + (device.label || device.device_id);

        div.onclick = function(){
            selectedDevice = device;
            document.getElementById("selectedDeviceName").value =
                device.label || device.device_id;
            document.getElementById("roomSelect").value =
                device.room_id || "";
            renderDeviceList();
        };

        list.appendChild(div);
    });
}

function renderRoomSelect(){
    const select = document.getElementById("roomSelect");
    select.innerHTML = "";

    floorData.rooms.forEach(room => {
        const opt = document.createElement("option");
        opt.value = room.id;
        opt.textContent = room.room_name;
        select.appendChild(opt);
    });
}

async function savePosition(){
    if(!selectedDevice){
        alert("Select a device first");
        return;
    }

    const roomId = document.getElementById("roomSelect").value;

    const res = await fetch(`/devices/${selectedDevice.device_id}/position`, {
        method:"PUT",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            x:selectedDevice.x,
            y:selectedDevice.y,
            room_id: roomId ? Number(roomId) : null
        })
    });

    const data = await res.json();

    if(!res.ok){
        alert(JSON.stringify(data));
        return;
    }

    alert("Device position saved");

    await loadFloor();
}

function getRoomById(roomId){
    return floorData.rooms.find(r => Number(r.id) === Number(roomId));
}

async function assignToRoom(){
    if(!selectedDevice){
        alert("Select a device first");
        return;
    }

    const roomId = document.getElementById("roomSelect").value;
    const room = getRoomById(roomId);

    if(!room){
        alert("Select room");
        return;
    }

    selectedDevice.x = room.x;
    selectedDevice.y = room.y;
    selectedDevice.room_id = room.id;

    await savePosition();
}

async function resetToRoomCenter(){
    await assignToRoom();
}

window.onload = loadFloor;
async function loadFloorDropdown() {
    const select = document.getElementById("floorId");

    try {
        const res = await fetch("/floors");
        const floors = await res.json();

        select.innerHTML = `<option value="">Select floor</option>`;

        floors.forEach(floor => {
            const label = `${floor.name || "Floor"} / Building ID ${floor.building_id} / ID ${floor.id}`;

            select.innerHTML += `
                <option value="${floor.id}">
                    ${label}
                </option>
            `;
        });

        const params = new URLSearchParams(window.location.search);
        const requestedFloorId = params.get("floor_id");

        if (
            requestedFloorId &&
            floors.some(floor => String(floor.id) === String(requestedFloorId))
        ) {
            select.value = requestedFloorId;
            loadFloor();
        }

        else if (floors.length > 0) {
            select.value = floors[0].id;
            loadFloor();
        }

    } catch (err) {
        console.error("Could not load floors:", err);
    }
}

document.addEventListener("DOMContentLoaded", loadFloorDropdown);
</script>

<script src="/uploads/help_system.js"></script>

<!-- UX Systems -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/introjs.min.css" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/intro.js/7.2.0/intro.min.js"></script>
<script src="/uploads/onboarding_tour.js"></script>
<script src="/uploads/search_system.js"></script>
<script src="/uploads/realtime_toasts.js"></script>

<!-- Chart.js & Graphs System -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="/uploads/graphs.js"></script>
<script src="/uploads/generate_firmware.js"></script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/uploads/service-worker.js');
  });
}
</script>
<script src="/uploads/analytics_widget.js"></script>
</body>


</html>
"""