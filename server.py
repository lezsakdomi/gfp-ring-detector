import base64
import codecs
import html
import mimetypes
import os
import pickle
import traceback

import numpy as np
import websockets
import asyncio
from websockets import WebSocketServerProtocol

from list_targets import CustomTarget
from pipeline import RingDetector
from threading import Thread
from urllib.parse import urlparse, unquote
from http import HTTPStatus
from queue import Queue
import inspect
import webbrowser


async def handle_connection(ws: WebSocketServerProtocol):
    url = urlparse(ws.path)
    path = unquote(url.path)

    if path.startswith('/analyze/'):
        target_str = path[len('/analyze/'):]
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

    if path == '/list':
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

    if path == '/reload':
        try:
            async with websockets.connect("ws://localhost:8000/reload") as server:
                async for message in server:
                    await ws.send(message)
        except ConnectionRefusedError:
            pass

    else:
        await ws.close(4001)


async def serve(host="0.0.0.0", port=8080):
    async def process_request(path, request_headers):
        if 'Upgrade' in request_headers and request_headers['Upgrade'] == 'websocket':
            return None

        path = unquote(path)

        frontend_dir = os.path.dirname(__file__) + '/frontend'
        frontend_path = frontend_dir + path
        if not os.path.abspath(frontend_path).startswith(os.path.abspath(frontend_dir)):
            return HTTPStatus.FORBIDDEN, [('Content-Type', "text/plain, charset=UTF-8")], \
                   b"Hacky URLs are not allowed"

        if os.path.isdir(path):
            if os.path.exists(frontend_path + '/index.html'):
                frontend_path = frontend_path + '/index.html'
            else:
                try:
                    result = "<ul>\n"
                    for entry in os.scandir(path):
                        result += f'<li><a href="{html.escape(entry.name)}">'
                        if entry.is_symlink():
                            result += html.escape(entry.name) + '@'
                        elif entry.is_file():
                            result += html.escape(entry.name)
                        elif entry.is_dir():
                            result += html.escape(entry.name) + '/'
                        else:
                            result += html.escape(entry.name)
                        result += "</a></li>\n"
                    result += "</ul>\n"
                except PermissionError:
                    return HTTPStatus.FORBIDDEN, [('Content-Type', "text/plain, charset=UTF-8")], \
                           b'Not permitted to open this location'
                except Exception:
                    traceback.print_exc()
                    return HTTPStatus.INTERNAL_SERVER_ERROR, [('Content-Type', "text/plain, charset=UTF-8")], \
                           b'Server error'

        if not os.path.isfile(frontend_path) and os.path.exists(frontend_path + '/../default.html'):
            frontend_path = frontend_path + '/../default.html'

        try:
            with open(frontend_path, 'rb') as f:
                data = f.read()
            response_headers = []
            mime, encoding = mimetypes.guess_type(frontend_path)

            if mime is not None:
                response_headers.append(('Content-Type', mime))
            if encoding is not None:
                response_headers.append(('Content-Encoding', encoding))

            return HTTPStatus.OK, response_headers, data
        except FileNotFoundError:
            pass
        except PermissionError:
            return HTTPStatus.FORBIDDEN, [('Content-Type', "text/plain, charset=UTF-8")], \
                   b'Not permitted to open this location'
        except Exception:
            traceback.print_exc()
            return HTTPStatus.INTERNAL_SERVER_ERROR, [('Content-Type', "text/plain, charset=UTF-8")], \
                   b'Server error'

        if path.startswith('/képek/') and '..' not in path:
            try:
                with open('./' + path, 'rb') as f:
                    data = f.read()
                response_headers = []
                mime, encoding = mimetypes.guess_type(frontend_path)

                if mime is not None:
                    response_headers.append(('Content-Type', mime))
                if encoding is not None:
                    response_headers.append(('Content-Encoding', encoding))

                return HTTPStatus.OK, response_headers, data
            except FileNotFoundError:
                return HTTPStatus.NOT_FOUND, [('Content-Type', "text/plain, charset=UTF-8")], \
                       b'The requested data file was not found on the server'
            except PermissionError:
                return HTTPStatus.FORBIDDEN, [('Content-Type', "text/plain, charset=UTF-8")], \
                       b'Not permitted to open this location'
            except Exception:
                traceback.print_exc()
                return HTTPStatus.INTERNAL_SERVER_ERROR, [('Content-Type', "text/plain, charset=UTF-8")], \
                       b'Server error'

        try:
            with open("frontend/Main.html", 'rb') as f:
                data = f.read()
            response_headers = []
            mime, encoding = mimetypes.guess_type("frontend/Main.html")

            if mime is not None:
                response_headers.append(('Content-Type', mime))
            if encoding is not None:
                response_headers.append(('Content-Encoding', encoding))

            return HTTPStatus.OK, response_headers, data
        except FileNotFoundError:
            pass
        except PermissionError:
            return HTTPStatus.FORBIDDEN, [('Content-Type', "text/plain, charset=UTF-8")], \
                   b'Not permitted to open this location'
        except Exception:
            traceback.print_exc()
            return HTTPStatus.INTERNAL_SERVER_ERROR, [('Content-Type', "text/plain, charset=UTF-8")], \
                   b'Server error'

    async with websockets.serve(handle_connection, host, port, process_request=process_request):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(serve())
