import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import auth, input_ctrl

logger = logging.getLogger("eve-mouse")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="EVE Mouse")


@app.get("/status")
async def status():
    return {"ok": True}


@app.get("/login")
async def login_page():
    html = (STATIC_DIR / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.post("/auth/login")
async def login(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid json"})

    password = body.get("password", "")
    if not auth.verify_password(password):
        return JSONResponse(status_code=401, content={"error": "invalid password"})

    token = auth.create_session()
    response = JSONResponse(content={"ok": True})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=86400,
    )
    return response


@app.get("/auth/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        auth.invalidate_session(token)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@app.get("/")
async def index(request: Request):
    token = request.cookies.get("session_token")
    if not auth.is_valid_session(token):
        return RedirectResponse(url="/login", status_code=302)
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.cookies.get("session_token")
    if not auth.is_valid_session(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "mousemove":
                dx = msg.get("dx", 0)
                dy = msg.get("dy", 0)
                input_ctrl.move_mouse(dx, dy)

            elif msg_type == "click":
                button = msg.get("button", "left")
                input_ctrl.click(button)

            elif msg_type == "dblclick":
                button = msg.get("button", "left")
                input_ctrl.click(button)
                import asyncio
                await asyncio.sleep(0.05)
                input_ctrl.click(button)

            elif msg_type == "scroll":
                dy = msg.get("dy", 0)
                input_ctrl.scroll(int(dy))

            elif msg_type == "keydown":
                text = msg.get("text", "")
                if text:
                    logger.info(f"type_text: {repr(text)}")
                    input_ctrl.type_text(text)

            elif msg_type == "special_key":
                key = msg.get("key", "")
                if key:
                    logger.info(f"special_key: {key}")
                    input_ctrl.special_key(key)

    except WebSocketDisconnect:
        pass
    except Exception as ex:
        logger.error(f"WebSocket error: {ex}")
