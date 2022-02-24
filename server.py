import base64
import numpy as np
import websockets
import asyncio
from websockets import WebSocketServerProtocol
from pipeline import RingDetector, chreader
from threading import Thread
from urllib.parse import urlparse, unquote
from http import HTTPStatus


async def handle_connection(ws: WebSocketServerProtocol):
    url = urlparse(ws.path)
    path = unquote(url.path)

    if path.startswith('/analyze/'):
        fname_template = path[len('/analyze/'):]
        chread = chreader(fname_template)

        def cb(step, state, finished, error, step_index, **kwargs):
            from io import BytesIO
            import imageio

            def to_data_url(image, fmt='png'):
                buf = BytesIO()
                imageio.imwrite(buf, image, format=fmt)
                buf.seek(0)
                buf.getvalue()
                return f"data:image/{fmt};base64,{base64.b64encode(buf.getvalue()).decode()}"

            def to_info(name, data):
                if isinstance(data, np.ndarray):
                    return f"+ IMAGE {name} {to_data_url(data)}"
                if isinstance(data, list):
                    joined = '\n'.join(map(repr, data))
                    return f"+ LIST {name} {joined}"
                else:
                    return f"+ UNKNOWN {name} {repr(data)}"

            if not finished:
                msgs_to_send = [f"> Step#{step_index} ({step.name})"] + \
                    [to_info(name, state[name]) for name in step.inputs]
            elif error is not None:
                msgs_to_send = [f"ERROR {repr(error)}"]
            else:  # completed
                msgs_to_send = [f"COMPLETED took {step._last_profile_duration}s"] + \
                    [to_info(name, data) for name, data in step.last_output.items()]

            # print(msg_to_send)
            async def send_msgs():
                for message in msgs_to_send:
                    await ws.send(message)

            asyncio.run_coroutine_threadsafe(send_msgs(), mainloop)
            # TODO use queue

        ring_detector = RingDetector(chread)
        thread = Thread(target=ring_detector.run, kwargs={'cb': cb})
        mainloop = asyncio.get_running_loop()

        thread.start()
        async for msg in ws:
            print(msg)

    else:
        await ws.close(4001)


async def serve(host="0.0.0.0", port=8080):
    async def process_request(path, request_headers):
        if path == '/':
            return (HTTPStatus.OK, [('Content-Type', "text/html, charset=UTF-8")], b'''<!DOCTYPE HTML>
<head>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const fnameTemplate = prompt("Enter a TIF file template with {}-s at channel ID",
                localStorage.getItem('fname_template') || "");
            const wsUrl = new URL('/analyze/' + fnameTemplate, location.href);
            wsUrl.protocol = 'ws';
            const ws = new WebSocket(wsUrl.toString());
            ws.addEventListener('error', e => console.error(e));
            ws.addEventListener('message', msg => console.log(msg));
            ws.addEventListener('close', reason => console.log("Connection closed", reason))
            
            ws.addEventListener('message', ({data: msg}) => {
                const ev = /^\S+/.exec(msg)[0];
                const ul = document.getElementById('ul');
                const li = document.createElement('li');
                // li.dataset['message'] = msg;
                li.dataset['event'] = ev;
            
                switch (ev) {
                    case '>':
                    case 'COMPLETED':
                        li.innerHTML = `<details><summary>${msg}</summary></details>`;
                        break;
                        
                    case '+':
                        const [msg_, dataType, name, data] = /^\+ ([A-Z]+) (\S+) (.*)$/.exec(msg)
                        const details = document.createElement('details');
                        details.innerHTML = `<summary>${name}</summary>`;
                        details.open = true;
                        // details.dataset['message'] = msg;
                        details.dataset['event'] = ev;
                        details.dataset['dataType'] = dataType;
                        details.dataset['name'] = name;
                        // details.dataset['data'] = data;
                        switch (dataType) {
                            case 'IMAGE':
                                const img = document.createElement('img');
                                img.src = data;
                                details.appendChild(img);
                                break;
                                
                            case 'UNKNOWN':
                            case 'LIST':
                                const pre = document.createElement('pre');
                                pre.innerText = data;
                                details.appendChild(pre);
                                break;
                                
                            default:
                                details.innerHTML += `<pre>${msg_}</pre>`;
                        }
                        ul.lastChild.lastChild.appendChild(details);
                        return
                
                    default:
                        console.warn("Unknown message", msg);
                        li.innerHTML = `<pre>${msg}</pre>`;
                }
                
                ul.appendChild(li);
            })
        })
    </script>
    <style>
        body > ul {
            list-style: none;
            margin-left: 0;
        }
        
        img {
            width: 500px;
        }
        
        li > details {
            margin-left: 1em;
        }
        
        li[data-event="COMPLETED"] > details {
            margin-bottom: 1em;
        }
        
        details > details {
            display: inline-block;
        }
        
        details[data-name="DsRed"] img {
            filter: grayscale(100%) hue-rotate(0deg);
        }
        
        details[data-name="GFP"] img {
            filter: grayscale(100%) hue-rotate(100deg);
        }
        
        details[data-name="DAPI"] img {
            filter: grayscale(100%) hue-rotate(215deg);
        }
    </style>
</head>
<body>
    <ul id="ul"></ul>
</body>
''')

    async with websockets.serve(handle_connection, host, port, process_request=process_request):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(serve())
