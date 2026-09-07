from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from app.main import *
templates = Jinja2Templates(directory='templates')
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from app.main import *
router = APIRouter()


@router.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, 'login_page.html', {})


@router.get('/admin-login', response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse(request, 'admin_login_page.html', {})


@router.get('/admin/gateway-placement', response_class=HTMLResponse)
def gateway_placement_editor(request: Request):
    return templates.TemplateResponse(request,
        'gateway_placement_editor.html', {})


@router.get('/admin/client-access', response_class=HTMLResponse)
def admin_client_access_page(request: Request):
    return templates.TemplateResponse(request,
        'admin_client_access_page.html', {})


@router.get('/sensor-catalog-manager', response_class=HTMLResponse)
def sensor_catalog_manager_page(request: Request):
    return templates.TemplateResponse(request,
        'sensor_catalog_manager_page.html', {})


@router.get('/firmware-module-manager', response_class=HTMLResponse)
def firmware_module_manager_page(request: Request):
    return templates.TemplateResponse(request,
        'firmware_module_manager_page.html', {})


@router.get('/sensor-profile-manager', response_class=HTMLResponse)
def sensor_profile_manager_page(request: Request):
    return templates.TemplateResponse(request,
        'sensor_profile_manager_page.html', {})


@router.get('/sensor-profile-editor', response_class=HTMLResponse)
def simple_sensor_profile_editor_page(request: Request):
    return templates.TemplateResponse(request,
        'simple_sensor_profile_editor_page.html', {})


@router.get('/sensor-profile-editor/advanced', response_class=HTMLResponse)
def sensor_profile_advanced_editor_page(request: Request):
    return templates.TemplateResponse(request,
        'sensor_profile_advanced_editor_page.html', {})


@router.get('/admin/provision-options', response_class=HTMLResponse)
def admin_provision_options_page(request: Request):
    return templates.TemplateResponse(request,
        'admin_provision_options_page.html', {})


@router.get('/admin/alarms', response_class=HTMLResponse)
def admin_alarms_page(request: Request):
    return templates.TemplateResponse(request, 'admin_alarms_page.html', {})


@router.get('/floorplan-editor', response_class=HTMLResponse)
def floorplan_editor(request: Request):
    return templates.TemplateResponse(request, 'floorplan_editor.html', {})


@router.get('/site-map-editor', response_class=HTMLResponse)
def site_map_editor(request: Request):
    return templates.TemplateResponse(request, 'site_map_editor.html', {})


@router.get('/admin/audit-log', response_class=HTMLResponse)
def admin_audit_log_page(request: Request):
    return templates.TemplateResponse(request, 'admin_audit_log_page.html', {})


@router.get('/admin', response_class=HTMLResponse)
def admin_home_page(request: Request):
    return templates.TemplateResponse(request, 'admin_home_page.html', {})


@router.get('/node-placement-editor', response_class=HTMLResponse)
def node_placement_editor(request: Request):
    return templates.TemplateResponse(request, 'node_placement_editor.html', {}
        )


@router.get('/client-login', response_class=HTMLResponse)
def client_login_page(request: Request):
    return templates.TemplateResponse(request, 'client_login_page.html', {})


@router.get('/floor-live-view', response_class=HTMLResponse)
def floor_live_view(request: Request):
    return templates.TemplateResponse(request, 'floor_live_view.html', {})


@router.get('/admin/setup', response_class=HTMLResponse)
def admin_setup_asset_management_page(request: Request):
    return templates.TemplateResponse(request,
        'admin_setup_asset_management_page.html', {})


@router.get('/alarm-settings-page', response_class=HTMLResponse)
def alarm_settings_page(request: Request):
    return templates.TemplateResponse(request, 'alarm_settings_page.html', {})


@router.get('/client-portal', response_class=HTMLResponse)
def client_portal_page(request: Request):
    return templates.TemplateResponse(request, 'client_portal_page.html', {})


@router.get('/building-overview', response_class=HTMLResponse)
def building_overview(request: Request):
    return templates.TemplateResponse(request, 'building_overview.html', {})


@router.get('/floor-editor', response_class=HTMLResponse)
def floor_editor(request: Request):
    return templates.TemplateResponse(request, 'floor_editor.html', {})


@router.get('/device-capabilities-manager', response_class=HTMLResponse)
@app.post('/devices/{device_id}/capabilities')
def device_capabilities_manager_page(request: Request):
    return templates.TemplateResponse(request,
        'device_capabilities_manager_page.html', {})
