import base64
import os
import numpy as np
import websockets
import asyncio
from websockets import WebSocketServerProtocol
from pipeline import RingDetector
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
                    joined = '\n'.join(map(lambda d: str(d).strip(), data))
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

        ring_detector = RingDetector(fname_template, interactive=True)
        thread = Thread(target=ring_detector.run, kwargs={'hook': cb})
        mainloop = asyncio.get_running_loop()

        thread.start()
        async for msg in ws:
            if str(msg).startswith('Open in editor #'):
                n = int(msg[len("Open in editor# "):])
                file = inspect.getsourcefile(ring_detector.steps[n]._func)
                code, line = inspect.getsourcelines(ring_detector.steps[n]._func)
                os.system(f"pycharm --line {line} {file}")

            elif msg == 'View in 5D':
                ring_detector.view_in_5d()

            else:
                print(msg)

    else:
        await ws.close(4001)


async def serve(host="0.0.0.0", port=8080):
    async def process_request(path, request_headers):
        if 'Upgrade' in request_headers and request_headers['Upgrade'] == 'websocket':
            return None

        if path == '/':
            return (HTTPStatus.OK, [('Content-Type', "text/html, charset=UTF-8")], '''<!DOCTYPE HTML>
<head>
    <script>
        function setUrl({page, fnameTemplate, step, section, plane, x, y, zoom}) {
            let hash = '';
            function add(fragment = null, params = null) {
                if (fragment !== null) {
                    hash += '#' + encodeURIComponent(fragment);
                }
                
                if (params) {
                    let search;
                    if (hash) {
                        [, hash, search] = /^(.*)(\?[^#]*)?$/.exec(hash)
                        search = new URLSearchParams(search)
                    } else {
                        search = new URLSearchParams(location.search)
                    }
                    
                    for (const [k, v] of Object.entries(params)) {
                        if (v !== undefined) {
                            search.set(k, v);
                        }
                    }

                    if (hash) {
                        if (search.toString()) {
                            hash += '?' + search.toString()
                        }
                    } else {
                        location.replace('?' + search.toString())
                    }
                }
            }
            
            if (page) {
                add(page);
                
                switch (page) {
                    case 'analyze':
                        add(null, {x, y, zoom});
                        if (fnameTemplate) add(fnameTemplate); else break;
                        if (step) add(step); else break;
                        if (section) add(section); else break;
                        if (plane) add(plane); else break;
                        break;
                }
            }
            
            hash = hash || '#';
            const oldUrl = parseURL();
            if (oldUrl.page === page && oldUrl.fnameTemplate === fnameTemplate) {
                location.replace(hash);
            } else {
                location.assign(hash);
            }
            
            const css = [...document.styleSheets].find(css => css.ownerNode.id === 'urlFeedbackCss');
            css.rules[0].selectorText = `li[data-step=${JSON.stringify(step)}]`;
            css.rules[1].selectorText = `details[data-step=${JSON.stringify(step)}][data-section=${JSON.stringify(section)}]`;
            css.rules[2].selectorText = `details[data-plane=${JSON.stringify(plane)}]`;
        }
        
        function parseURL() {
            const o = {};
            let hash = location.hash;
            let search = location.search;
            function next() {
                (new URLSearchParams(search)).forEach((v, k) => {
                    switch (k) {
                        case 'x':
                        case 'y':
                            v = parseInt(v);
                            break;
                            
                        case 'zoom':
                            v = parseFloat(v);
                            break;
                    }
                    
                    o[k] = v;
                });

                let part;
                if (hash) {
                    [, part, search, hash] = /#([^#?]*)(\?[^#]*)?(#.*)?/.exec(hash);
                    return decodeURIComponent(part)
                } else {
                    part = null;
                    search = undefined;
                    return null
                }
            }
            
            switch (o.page = next()) {
                case 'analyze':
                    // #analyze#myFile_c{}.tif#calc#inputs#GFP
                    o.fnameTemplate = next();
                    o.step = next();
                    o.section = next();
                    o.plane = next();
                    break;
            }
            
            next();
            return o;
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            const url = new Proxy(parseURL(), {
                set(target, p, value, receiver) {
                    target[p] = value;
                    setUrl(target);
                }
            });
            
            function handleUrl(url) {
                console.log(">", url);
                
                switch (url.page) {
                    case 'analyze':
                        if (!url.fnameTemplate) {
                            url.fnameTemplate = prompt("Enter a TIF file template with {}-s at channel ID",
                                localStorage.getItem('fname_template') ||
                                "képek/2021-07-15_GlueRab7_ctrl_-2h/GlueRab7_ctrl_-2h-0021.tif_Files/GlueRab7_ctrl_-2h-0021_c{}.tif")
                        }

                        analyze(url, document.getElementById('ul'));
                        break;

                    default:
                        url.page = 'analyze';
                        handleUrl(url);
                }
            }
        
            function analyze(url, ul) {
                const wsUrl = new URL('analyze/' + url.fnameTemplate, location.href);
                wsUrl.protocol = 'ws';
                const ws = new WebSocket(wsUrl.toString());
                ws.addEventListener('error', e => console.error(e));
                ws.addEventListener('message', msg => console.log(msg));
                ws.addEventListener('close', reason => console.warn(reason))
                
                ws.addEventListener('message', ({data: msg}) => {
                    const [msg_, ev, det] = /^(\S+) (.*)$/s.exec(msg);
                    const li = document.createElement('li');
                    li.dataset['source'] = 'ws-message';
                    // li.dataset['message'] = msg;
                    li.dataset['event'] = ev;
                
                    switch (ev) {
                        case '>':
                        case 'COMPLETED': {
                            const [msg_, ev_, no, step, det] = /(>|COMPLETED) [sS]tep#(\d+) \((\S+)\)(?:, (.*))?$/s.exec(msg)
                            const section = ev_ === 'COMPLETED' ? 'outputs' : 'inputs';
                                
                            const details = document.createElement('details');
                            details.dataset['source'] = 'ws-message';
                            details.dataset['event'] = ev_;
                            details.dataset['step'] = step;
                            details.dataset['section'] = section;
                            li.dataset['step'] = step;
                            
                            details.innerHTML = `<summary>
                                ${ev_ !== '>' ? ev_ : ""}
                                <b>${step}</b>${det ? ", " + det : ""}
                                <button class="open-in-editor">Open in editor</button>
                            </summary>`;
                            details.querySelector('summary > .open-in-editor').addEventListener('click', (event) => {
                                ws.send(`Open in editor #${no}`);
                                event.preventDefault();
                            });
                            if ((det && det.match('debug')) || (url.step === step && url.section === section)) details.open = true;
                            details.addEventListener('toggle', event => {
                                if (details.open) {
                                    url.step = step;
                                    url.section = section;
                                }
                            })
                            li.appendChild(details);
                            break;
                        }
                            
                        case '+': {
                            const [msg_, dataType, plane, data] = /^\+ ([A-Z]+) (\S+) (.*)$/s.exec(msg)
                            const details = document.createElement('details');
                            details.innerHTML = `<summary>${plane}</summary>`;
                            details.open = true;
                            details.dataset["source"] = 'ws-message'
                            // details.dataset['message'] = msg;
                            details.dataset['event'] = ev;
                            details.dataset['type'] = dataType;
                            details.dataset['plane'] = plane;
                            // details.dataset['data'] = data;
                            switch (dataType) {
                                case 'IMAGE':
                                    const img = document.createElement('img');
                                    let dragStarted;
                                    let dragHandled;
                                    img.src = data;
                                    img.addEventListener('mousemove', updateCrosshairs);
                                    img.addEventListener('mouseenter', showCrosshairs);
                                    img.addEventListener('mouseleave', hideCrosshairs);
                                    img.addEventListener('mousewheel', zoomImages);
                                    img.addEventListener('dragstart', event => event.preventDefault());
                                    img.addEventListener('mousedown', (event) => {
                                        dragStarted = event;
                                        // dragHandled = setDefaultCrosshairs(event, false);
                                        dragHandled = false;
                                    });
                                    img.addEventListener('mousemove', (event) => {
                                        if (dragStarted) {
                                            moveImages(dragStarted, event);
                                            dragStarted = event;
                                            dragHandled = true;
                                        }
                                    });
                                    img.addEventListener('mouseup', (event) => {
                                        if (dragStarted) {
                                            moveImages(dragStarted, event);
                                            if (!dragHandled) {
                                                setDefaultCrosshairs(event, true);
                                            }
                                            dragStarted = undefined;
                                        }
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
                    const li = document.createElement('li');
                    li.dataset["source"] = 'ws-error';
                    const pre = document.createElement('pre');
                    pre.innerText = e;
                    li.appendChild(pre);
                    ul.appendChild(li);
                });
                ws.addEventListener('close', event => {
                    const li = document.createElement('li');
                    li.dataset["source"] = 'ws-close';
                    const span = document.createElement('span');
                    span.style.color = event.wasClean ? 'green' : 'red';
                    span.innerText = `Connection closed (code: ${event.code})`;
                    li.appendChild(span);
                    ul.appendChild(li);
                    
                    for (const button of ul.getElementsByTagName('button')) {
                        button.disabled = true;
                    }
                    viewButton.disabled = true;
                });
                
                const viewButton = document.createElement('button');
                viewButton.innerText = "View in 5D Viewer";
                viewButton.addEventListener('click', (event) => {
                    ws.send("View in 5D");
                    event.preventDefault();
                });
                ul.parentElement.insertBefore(viewButton, ul.nextSibling);
            }
        
            const zoomRule = [...document.styleSheets].find(css => css.ownerNode.id === 'zoomCss').cssRules[0];
            let imageZoom = parseFloat(zoomRule.style.zoom);
            let imageX = 0;
            let imageY = 0;
            const defaultZoom = imageZoom;
            const realImageW = parseInt(zoomRule.style.width) * defaultZoom;
            const realImageH = parseInt(zoomRule.style.height) * defaultZoom;
            
            if (url.zoom) {
                const diff = url.zoom - imageZoom;
                const deltaY = diff / -0.01;
                zoomImages({deltaY});
            }
            
            if (url.x && url.y) {
                const from = {
                    offsetX: url.x * imageZoom,
                    offsetY: url.y * imageZoom,
                };
                const to = {
                    offsetX: realImageW / 2,
                    offsetY: realImageH / 2,
                };
                
                moveImages(from, to);
                hideCrosshairs();
            }
            
            function updateCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                const imgFilterDefCross = document.getElementById('imgFilterDefCross');
                
                imgFilterCrossV.x.baseVal.value = event.offsetX / imageZoom - imgFilterCrossV.width.baseVal.value / 2;
                imgFilterCrossH.y.baseVal.value = event.offsetY / imageZoom - imgFilterCrossH.height.baseVal.value / 2;
                if (url.x && url.y) {
                    imgFilterDefCross.x.baseVal.value = url.x + imageX - imgFilterDefCross.width.baseVal.value / 2;
                    imgFilterDefCross.y.baseVal.value = url.y + imageY - imgFilterDefCross.height.baseVal.value / 2;
                    imgFilterDefCross.result.baseVal = 'imgFilterDefCross';
                } else {
                    imgFilterDefCross.result.baseVal = 'none';
                }
            }
            
            function showCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                const imgFilterDefCross = document.getElementById('imgFilterDefCross');
                
                imgFilterCrossV.result.baseVal = 'imgFilterCrossV';
                imgFilterCrossH.result.baseVal = 'imgFilterCrossH';
                imgFilterDefCross.result.baseVal = (url.x && url.y) ? 'imgFilterDefCross' : 'none';
            }
            
            function hideCrosshairs(event) {
                const imgFilterCrossV = document.getElementById('imgFilterCrossV');
                const imgFilterCrossH = document.getElementById('imgFilterCrossH');
                const imgFilterDefCross = document.getElementById('imgFilterDefCross');
                
                if (url.x && url.y) {
                    updateCrosshairs({
                        offsetX: (url.x + imageX) * imageZoom,
                        offsetY: (url.y + imageY) * imageZoom,
                    });
                } else {
                    imgFilterCrossV.result.baseVal = 'none';
                    imgFilterCrossH.result.baseVal = 'none';
                }
                imgFilterDefCross.result.baseVal = 'none';
                
                if (url.zoom !== imageZoom) {
                    url.zoom = imageZoom;
                }
            }
            
            function setDefaultCrosshairs(event, permitReset = true) {
                const x = Math.round(event.offsetX / imageZoom - imageX);
                const y = Math.round(event.offsetY / imageZoom - imageY);
                let wasHandled = false;
                
                if (url.x != x || url.y != y) {
                    url.step = event.target.parentElement.parentElement.dataset['step'];
                    url.section = event.target.parentElement.parentElement.dataset['section'];
                    url.plane = event.target.parentElement.dataset['plane'];
                    url.x = x;
                    url.y = y;
                    wasHandled = true;
                } else if (permitReset) {
                    url.plane = undefined;
                    url.x = undefined;
                    url.y = undefined;
                }
                
                updateCrosshairs(event);
                
                return wasHandled;
            }
            
            function zoomImages(event) {
                const oldZoom = imageZoom;
                imageZoom += event.deltaY * -0.01;
                if (imageZoom < 0.1) imageZoom = 0.1;
                const width = realImageW / imageZoom;
                const height = realImageH / imageZoom;
                
                zoomRule.style.zoom = imageZoom;
                zoomRule.style.width = width + 'px';
                zoomRule.style.height = height + 'px';
                zoomRule.style.borderWidth = 5 / imageZoom + 'px';
                document.getElementById('imgFilterCrossV').width.baseVal.value = 1 / imageZoom;
                document.getElementById('imgFilterCrossH').height.baseVal.value = 1 / imageZoom;
                
                if (event.preventDefault) {
                    event.preventDefault();
                }
                
                if (event.offsetX && event.offsetY) {
                    moveImages({
                        offsetX: event.offsetX / oldZoom * imageZoom,
                        offsetY: event.offsetY / oldZoom * imageZoom,
                    }, event);

                    updateCrosshairs(event);
                }
            }
            
            function moveImages(from, to) {
                imageX += (to.offsetX - from.offsetX) / imageZoom;
                imageY += (to.offsetY - from.offsetY) / imageZoom;
                zoomRule.style.objectPosition = `${imageX}px ${imageY}px`;
            }
            
            handleUrl(url);
        })
    </script>
    <style>
        body, button {
            background: black;
            color: white;
        }
        
        svg {
            display: none;
        }
        
        #ul {
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
    
        details[data-type="IMAGE"] > img {
            filter: url(#imgFilter);
            object-fit: none;
            background: #222;
            border: 20px solid black;
        }
        
        details[data-type="IMAGE"] > img:hover {
            cursor: none;
            border-color: blue;
        }
        
        button {
            cursor: pointer;
            background: darkgreen;
        }
    </style>
    
    <style id="zoomCss">
        details[data-type="IMAGE"] > img {
            width: 1388px;
            height: 1040px;
            zoom: 0.25;
            object-position: 0 0;
        }
    </style>
    
    <style id="urlFeedbackCss">
        li[data-step=""] {
            background: rgba(0, 0, 64, 0.75);
        }
        
        details[data-step=""][data-section=""] {
            background: rgba(16, 16, 128, 0.5);
        }
        
        details[data-plane=""] {
            background: rgba(64, 64, 128, 0.5);
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
                <feColorMatrix in="SourceGraphic" type="matrix"
                               id="imgFilterDefCross" result="imgFilterDefCross"
                               width="1" height="1" x="0" y="0"
                               values="-1 0 0 0 1 
                                       0 -1 0 0 1 
                                       0 0 -1 0 1
                                       0 0 0 1 0"/>
                <feMerge/>
                <feMerge>
                    <feMergeNode in="SourceGraphic"/>
                    <feMergeNode in="imgFilterCrossV"/>
                    <feMergeNode in="imgFilterCrossH"/>
                    <feMergeNode in="imgFilterDefCross"/>
                </feMerge>
            </filter>
        </defs>
    </svg>
</body>
'''.encode('utf-8'))

        else:
            return (HTTPStatus.NOT_FOUND, [('Content-Type', "text/html, charset=UTF-8")],
                    '''
                    Error: Document not found on the server
                    '''.encode('utf-8'))

    async with websockets.serve(handle_connection, host, port, process_request=process_request):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(serve())
