from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from redis_service import RedisService
from worker import Worker



RedisService.check_connection()


app = FastAPI()


@app.websocket("/worker/start")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = Worker.start()
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass


@app.websocket("/worker/stop")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = Worker.stop()
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass


@app.websocket("/worker/status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = 'UP' if Worker.running() else 'DOWN'
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass
