import os
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, FileResponse, RedirectResponse
import json
import sqlite3
import csv
import io
import re
from app.main import *
router = APIRouter()

@router.get("/")
def root():
    return {
        "status": "ok",
        "service": "LILYGO Provisioning Server",
        "app_id": APP_ID,
        "ttn_host": TTN_HOST,
        "thingsboard_url": THINGSBOARD_URL,
    }