import base64
import os
import numpy as np
import websockets
import asyncio
from websockets import WebSocketServerProtocol
from pipeline import RingDetector, chreader
from threading import Thread
from urllib.parse import urlparse, unquote
from http import HTTPStatus
from queue import Queue
import inspect


async def handle_connection(ws: WebSocketServerProtocol):
    url = urlparse(ws.path)
    path = unquote(url.path)

    if path.startswith('/analyze/'):
        fname_template = path[len('/analyze/'):]
        msgq = Queue()

        async def send_msg(block=False, timeout=None):
            msg = msgq.get(block, timeout)
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
                buf = BytesIO()
                imageio.imwrite(buf, image, format=fmt)
                buf.seek(0)
                buf.getvalue()
                return f"data:image/{fmt};base64,{base64.b64encode(buf.getvalue()).decode()}"

            def to_info(name, data):
                if isinstance(data, np.ndarray):
                    return f"+ IMAGE {name} {to_data_url(data)}"
                if isinstance(data, list):
                    joined = '\n'.join(map(str, data))
                    return f"+ LIST {name} {joined}"
                else:
                    return f"+ UNKNOWN {name} {repr(data)}"

            if not finished:
                msgq.put(f"> Step#{step_index} ({step.name})" + (", " + step.details if step.details else ""))
                for name in step.inputs:
                    msgq.put(to_info(name, state[name]))
            elif error is not None:
                msgq.put(f"ERROR {repr(error)}")
            else:  # completed
                msgq.put(f"COMPLETED step#{step_index} ({step.name}), took {step._last_profile_duration:.03}s" +
                         (", " + step.details if step.details else ""))
                for name, data in step.last_output.items():
                    msgq.put(to_info(name, data))

            # needed if receiving messages
            asyncio.run_coroutine_threadsafe(send_msgs(), mainloop)

        ring_detector = RingDetector(fname_template)
        thread = Thread(target=ring_detector.run, kwargs={'cb': cb})
        mainloop = asyncio.get_running_loop()

        thread.start()
        async for msg in ws:
            if str(msg).startswith('Open in editor #'):
                n = int(msg[len("Open in editor# "):])
                file = inspect.getsourcefile(ring_detector.steps[n]._func)
                code, line = inspect.getsourcelines(ring_detector.steps[n]._func)
                os.system(f"pycharm --line {line} {file}")
            else:
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
            // if (location.hash === '') return
            const fnameTemplate = prompt("Enter a TIF file template with {}-s at channel ID",
                localStorage.getItem('fname_template') || "");
            const wsUrl = new URL('analyze/' + fnameTemplate, location.href);
            wsUrl.protocol = 'ws';
            const ws = new WebSocket(wsUrl.toString());
            ws.addEventListener('error', e => console.error(e));
            ws.addEventListener('message', msg => console.log(msg));
            ws.addEventListener('close', reason => console.warn(reason))
            
            ws.addEventListener('message', ({data: msg}) => {
                const [msg_, ev, det] = /^(\S+) (.*)$/s.exec(msg);
                const ul = document.getElementById('ul');
                const li = document.createElement('li');
                li.dataset['source'] = 'ws-message';
                // li.dataset['message'] = msg;
                li.dataset['event'] = ev;
            
                switch (ev) {
                    case '>':
                    case 'COMPLETED': {
                        const [msg_, ev_, no, name, det] = /(>|COMPLETED) [sS]tep#(\d+) \((\S+)\)(?:, (.*))?$/s.exec(msg)
                        const details = document.createElement('details');
                        details.innerHTML = `<summary>
                            ${ev_ !== '>' ? ev_ : ""}
                            <b>${name}</b>${det ? ", " + det : ""},
                            <a href="#" class="open-in-editor">Open in editor</a>
                        </summary>`;
                        details.querySelector('summary > .open-in-editor').addEventListener('click', () => {
                            ws.send(`Open in editor #${no}`);
                        });
                        if (det && det.match('debug')) details.open = true;
                        li.appendChild(details);
                        break;
                    }
                        
                    case '+': {
                        const [msg_, dataType, name, data] = /^\+ ([A-Z]+) (\S+) (.*)$/s.exec(msg)
                        const details = document.createElement('details');
                        details.innerHTML = `<summary>${name}</summary>`;
                        details.open = true;
                        details.dataset["source"] = 'ws-message'
                        // details.dataset['message'] = msg;
                        details.dataset['event'] = ev;
                        details.dataset['dataType'] = dataType;
                        details.dataset['name'] = name;
                        // details.dataset['data'] = data;
                        switch (dataType) {
                            case 'IMAGE':
                                const img = document.createElement('img');
                                let dragStarted;
                                img.src = data;
                                img.addEventListener('mousemove', updateCrosshairs);
                                img.addEventListener('mouseenter', showCrosshairs);
                                img.addEventListener('mouseleave', hideCrosshairs);
                                img.addEventListener('mousewheel', zoomImages);
                                img.addEventListener('mousedown', (event) => {
                                    dragStarted = event;
                                });
                                img.addEventListener('dragstart', event => event.preventDefault());
                                img.addEventListener('mousemove', (event) => {
                                    if (dragStarted) {
                                        moveImages(dragStarted, event);
                                        dragStarted = event;
                                    }
                                });
                                img.addEventListener('mouseup', (event) => {
                                    if (dragStarted) moveImages(dragStarted, event);
                                    dragStarted = undefined;
                                });
                                img.addEventListener('mouseleave', () => {
                                    dragStarted = undefined;
                                });
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
                    }
                
                    default: {
                        console.warn("Unknown message", msg);
                        li.innerHTML = `<pre>${msg}</pre>`;
                    }
                }
                
                ul.appendChild(li);
            });
            ws.addEventListener('error', e => {
                const ul = document.getElementById('ul');
                const li = document.createElement('li');
                li.dataset["source"] = 'ws-error';
                const pre = document.createElement('pre');
                pre.innerText = e;
                li.appendChild(pre);
                ul.appendChild(li);
            });
            ws.addEventListener('close', event => {
                const ul = document.getElementById('ul');
                const li = document.createElement('li');
                li.dataset["source"] = 'ws-close';
                const span = document.createElement('span');
                span.style.color = event.wasClean ? 'green' : 'red';
                span.innerText = `Connection closed (code: ${event.code})`;
                li.appendChild(span);
                ul.appendChild(li);
            });
            
            const zoomRule = [...document.styleSheets].find(css => css.ownerNode.id === 'zoomCss').cssRules[0];
            let imageZoom = parseFloat(zoomRule.style.zoom);
            let imageX = 0;
            let imageY = 0;
            const defaultZoom = imageZoom;
            const realImageW = parseInt(zoomRule.style.width) * defaultZoom;
            const realImageH = parseInt(zoomRule.style.height) * defaultZoom;
            
            function updateCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                
                imgFilterCrossV.x.baseVal.value = event.offsetX / imageZoom - imgFilterCrossV.width.baseVal.value / 2;
                imgFilterCrossH.y.baseVal.value = event.offsetY / imageZoom - imgFilterCrossH.height.baseVal.value / 2;
            }
            
            function showCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                
                imgFilterCrossV.result.baseVal = 'imgFilterCrossV';
                imgFilterCrossH.result.baseVal = 'imgFilterCrossH';
            }
            
            function hideCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                
                imgFilterCrossV.result.baseVal = 'none';
                imgFilterCrossH.result.baseVal = 'none';
            }
            
            function zoomImages(event) {
                const oldZoom = imageZoom;
                imageZoom += event.deltaY * -0.01;
                const width = realImageW / imageZoom;
                const height = realImageH / imageZoom;
                
                zoomRule.style.zoom = imageZoom;
                zoomRule.style.width = width + 'px';
                zoomRule.style.height = height + 'px';
                
                event.preventDefault();
                
                moveImages({
                    offsetX: event.offsetX / oldZoom * imageZoom,
                    offsetY: event.offsetY / oldZoom * imageZoom,
                }, event);

                updateCrosshairs(event);
            }
            
            function moveImages(from, to) {
                imageX += (to.offsetX - from.offsetX) / imageZoom;
                imageY += (to.offsetY - from.offsetY) / imageZoom;
                zoomRule.style.objectPosition = `${imageX}px ${imageY}px`;
            }
        })
    </script>
    <style>
        body > ul {
            list-style: none;
            margin-left: 0;
        }
        
        li[data-source='ws-message']:not([data-event=">"]) {
            padding-left: 0.25em;
            margin-left: 0.25em;
            border-left: 1px solid gray;
        }
        
        li[data-event="COMPLETED"] > details {
            margin-bottom: 1em;
        }
        
        li > pre {
            margin-top: 0;
            margin-bottom: 0;
        }
        
        li > details {
            padding-left: 1em;
        }
        
        li > details > summary {
            margin-left: -1em;
        }
        
        details > details {
            display: inline-block;
            vertical-align: top;
        }
        
        details > details:not([open]) {
            writing-mode: vertical-lr;
            margin-top: 4px;
            margin-left: -4px;
            margin-right: 4px;
        }
    
        details[data-data-type="IMAGE"] > img {
            cursor: none;
            filter: url(#imgFilter);
            object-fit: none;
            background: gray;
        }
    </style>
    
    <style id="zoomCss">
        details[data-data-type="IMAGE"] > img {
            width: 1388px;
            height: 1040px;
            zoom: 0.25;
            object-position: 0 0;
        }
    </style>
</head>
<body>
    <ul id="ul"></ul>
    <svg>
        <defs>
            <filter id="imgFilter">
                <feColorMatrix in="SourceGraphic" type="matrix"
                               id="imgFilterCrossV" result="imgFilterCrossV"
                               width="1" x="-10"
                               values="-1 0 0 0 1 
                                       0 -1 0 0 1 
                                       0 0 -1 0 1
                                       0 0 0 1 0"/>
                <feColorMatrix in="SourceGraphic" type="matrix"
                               id="imgFilterCrossH" result="imgFilterCrossH"
                               height="1" y="-10"
                               values="-1 0 0 0 1 
                                       0 -1 0 0 1 
                                       0 0 -1 0 1
                                       0 0 0 1 0"/>
                <feComposite in2="SourceGraphic"
                             in="imgFilterCrossV" operator="atop"/>
                <feComposite in="imgFilterCrossH" operator="atop"/>
                <feMerge>
                    <feMergeNode in="SourceGraphic"/>
                    <feMergeNode in="imgFilterCrossV"/>
                    <feMergeNode in="imgFilterCrossH"/>
                </feMerge>
            </filter>
        </defs>
    </svg>
</body>
''')

    async with websockets.serve(handle_connection, host, port, process_request=process_request):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(serve())
