import base64
import codecs
import html
import mimetypes
import os
import pickle
import traceback
import warnings

import numpy as np
import websockets
from sanic import Sanic, Request, HTTPResponse
import asyncio
from sanic.response import json

from list_targets import CustomTarget
from pipeline import RingDetector
from threading import Thread
from urllib.parse import urlparse, unquote
from http import HTTPStatus
from queue import Queue
import inspect

app = Sanic("gfp-ring-detector")


@app.websocket('/analyze/<target_str>')
async def analyze(request, ws, target_str):
    msgq = Queue()

    async def send_msg(block=False, timeout=None):
        msg = msgq.get(block, timeout)
        try:
            from json import dumps
            msg = dumps(msg)
        except Exception as e:
            msg = dumps({
                'event': 'error',
                'description': f'Dump error: {e}\n{repr(msg)}',
            })
        await ws.send(msg)
        msgq.task_done()

    async def send_msgs(block=False):
        while True:
            await send_msg(block)
            await asyncio.sleep(0)

    def cb(step, state, finished, error, step_index, **kwargs):
        from io import BytesIO
        import imageio

        def to_data_url(image, fmt='png'):
            from skimage.util import img_as_ubyte
            image = img_as_ubyte(image)
            buf = BytesIO()
            imageio.imwrite(buf, image, format=fmt)
            buf.seek(0)
            buf.getvalue()
            return f"data:image/{fmt};base64,{base64.b64encode(buf.getvalue()).decode()}"

        def to_info(data):
            if isinstance(data, np.ndarray):
                if data.dtype == 'bool':
                    img = np.zeros_like(data, dtype=float)
                    img[data] = 1
                    data = img
                min = np.min(data)
                max = np.max(data)
                return {
                    'class': 'image',
                    'url': to_data_url((data - min) / (max - min)),
                    'min': float(min),
                    'max': float(max),
                }
            if isinstance(data, list):
                return {
                    'class': 'list',
                    'elements': [str(d).strip() for d in data]
                }
            else:
                return {
                    'data': str(data)
                }

        if not finished:
            msgq.put({
                'event': 'started',
                'id': step_index,
                'name': step.name,
                'details': step.details,
            })
            for name in step.inputs:
                msgq.put({'event': 'plane', 'name': name} | to_info(state[name]))
        elif error is not None:
            msgq.put({
                'event': 'error',
                'description': repr(error),
            })
        else:  # completed
            msgq.put({
                'event': 'completed',
                'id': step_index,
                'name': step.name,
                'details': step.details,
                'duration': step._last_profile_duration,
                'step_count': len(ring_detector.steps)
            })
            for name, data in step.last_output.items():
                msgq.put({'event': 'plane', 'name': name} | to_info(data))

        # needed if receiving messages
        asyncio.run_coroutine_threadsafe(send_msgs(), mainloop)

    if '{}' in target_str:
        target = CustomTarget(target_str)
    else:
        target = pickle.loads(codecs.decode(target_str.encode(), "base64"))
    ring_detector = RingDetector(target, interactive=True)
    thread = Thread(target=ring_detector.run, kwargs={'hook': cb})
    mainloop = asyncio.get_running_loop()

    thread.start()
    async for msg in ws:
        if str(msg).startswith('Open in editor #'):
            n = int(msg[len("Open in editor# "):])
            file = inspect.getsourcefile(ring_detector.steps[n]._func)
            code, line = inspect.getsourcelines(ring_detector.steps[n]._func)
            os.system(f"pycharm --line {line} {file}")

        elif msg.startswith('View in 5D'):
            try:
                ring_detector.view_in_5d(msg[len('View in 5D '):])
            except:
                traceback.print_exc()

        else:
            print(msg)


@app.websocket('/list')
async def list(request, ws):
    from list_targets import walk
    from json import dumps

    for image in walk():
        json = dumps({
            'fnameTemplate': image.fname_template,
            'name': image.name,
            'path': image.path,
            'title': str(image),
            'stats': image.stats,
            'dump': codecs.encode(pickle.dumps(image), 'base64').decode(),
        })
        await ws.send(json)


@app.websocket('/reload')
async def elm_reload_proxy(request, ws):
    try:
        async with websockets.connect("ws://localhost:8000/reload") as server:
            async for message in server:
                await ws.send(message)
    except ConnectionRefusedError:
        pass
    except OSError as e:
        if "Connect call failed" in str(e):
            pass
        else:
            raise


@app.route('/dash/<path_info:path>', methods=['GET', 'POST'])
def dash_handler(request: Request, path_info):
    import plot
    from io import BytesIO

    wsgi_app = plot.get_app().server.wsgi_app

    http_response = None
    body_bytes = bytearray()

    def _start_response(status, headers, *args, **kwargs):
        """The start_response callback as required by the wsgi spec. This sets up a response including the
        status code and the headers, but doesn't write a body."""
        nonlocal http_response
        nonlocal body_bytes
        if isinstance(status, int):
            code = status
        elif isinstance(status, str):
            code = int(status.split(" ")[0])
        else:
            raise RuntimeError("status cannot be turned into a code.")
        sanic_headers = dict(headers)
        response_constructor_args = {'status': code,  'headers': sanic_headers}
        if 'content_type' in kwargs:
            response_constructor_args['content_type'] = kwargs['content_type']
        elif 'Content-Type' in sanic_headers:
            response_constructor_args['content_type'] = str(sanic_headers['Content-Type']).split(";")[0].strip()
        http_response = HTTPResponse(**response_constructor_args)

        def _write_body(body_data):
            """This doesn't seem to be used, but it is part of the wsgi spec, so need to have it."""
            nonlocal body_bytes
            nonlocal http_response
            if isinstance(body_data, bytes):
                pass
            else:
                try:
                    # Try to encode it regularly
                    body_data = body_data.encode()
                except AttributeError:
                    # Convert it to a str if you can't
                    body_data = str(body_data).encode()
            body_bytes.extend(body_data)
        return _write_body

    environ = {}
    environ['SCRIPT_NAME'] = ''
    environ['PATH_INFO'] = request.path
    if request.host is not None:
        host = request.host
    elif 'host' in request.headers:
        host = request.headers['host']
    else:
        host = 'localhost:80'
    if 'content-type' in request.headers:
        content_type = request.headers['content-type']
    else:
        content_type = 'text/plain'
    environ['CONTENT_TYPE'] = content_type
    if 'content-length' in request.headers:
        content_length = request.headers['content-length']
        environ['CONTENT_LENGTH'] = content_length

    split_host = host.split(':', 1)
    host_has_port = len(split_host) > 1
    server_name = split_host[0]
    if request.port is not None:
        server_port = str(request.port)
    elif host_has_port:
        server_port = split_host[1]
    else:
        server_port = '80'
    if (not host_has_port) and (server_port != '80'):
        host = ":".join((host, server_port))
    environ['SERVER_PORT'] = server_port
    environ['SERVER_NAME'] = server_name
    environ['SERVER_PROTOCOL'] = 'HTTP/1.1' if request.version == "1.1" else 'HTTP/1.0'
    environ['HTTP_HOST'] = host
    environ['QUERY_STRING'] = request.query_string or ''
    environ['REQUEST_METHOD'] = request.method
    environ['wsgi.url_scheme'] = 'http'
    environ['wsgi.input'] = BytesIO(request.body) if request.body is not None and len(request.body) > 0\
        else BytesIO(b'')
    try:
        wsgi_return = wsgi_app(environ, _start_response)
    except Exception as e:
        print(e)
        raise e
    if http_response is None:
        http_response = HTTPResponse("WSGI call error.", 500)
    else:
        for body_part in wsgi_return:
            if body_part is not None:
                if isinstance(body_part, bytes):
                    pass
                else:
                    try:
                        # Try to encode it regularly
                        body_part = body_part.encode()
                    except AttributeError:
                        # Convert it to a str if you can't
                        body_part = str(body_part).encode()
                body_bytes.extend(body_part)
        http_response.body = bytes(body_bytes)
    return http_response

app.static("/", os.path.dirname(__file__) + "/frontend", name='frontend')

app.static("/képek", ".", name='data')

app.static("/", "frontend/Main.html", name='frontend_index_html')


async def serve(host="0.0.0.0", port=8080):
    warnings.warn("server.serve is deprecated, use app.run instead")
    return app.run(host, port)

if __name__ == "__main__":
    app.run('localhost', 8080)
