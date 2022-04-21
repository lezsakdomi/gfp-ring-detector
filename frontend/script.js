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
    } else {
        add('', {x, y, zoom});
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

const url = new Proxy(parseURL(), {
    set(target, p, value, receiver) {
        target[p] = value;
        setUrl(target);
    }
});

document.addEventListener('DOMContentLoaded', () => {
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

    handleUrl(url);
})

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

        case null:
        case '':
            listTargets(url, document.getElementById('ul'));
            break;

        default:
            console.log(url.page);
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
                details.addEventListener('defaultCrosshairsSet', event => {
                    url.step = step;
                    url.section = section;
                })
                li.dataset['step'] = step;

                details.innerHTML = `<summary>
                    ${ev_ !== '>' ? ev_ : ""}
                    <b>${step}</b>${det ? ", " + det : ""}
                </summary>`;
                const summary = details.querySelector('summary');
                if (section == 'inputs') {
                    const editorButton = summary.appendChild(document.createElement('button'));
                    editorButton.innerText = "Open in editor";
                    editorButton.addEventListener('click', (event) => {
                        ws.send(`Open in editor #${no}`);
                        event.preventDefault();
                    });

                    const viewerButton = summary.appendChild(document.createElement('button'));
                    viewerButton.innerText = "Open viewer";
                    viewerButton.addEventListener('click', (event) => {
                        ws.send(`View in 5D ${step}`);
                        event.preventDefault();
                    });
                }
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
                details.addEventListener('defaultCrosshairsSet', () => {
                    url.plane = plane;
                })
                // details.dataset['data'] = data;
                switch (dataType) {
                    case 'IMAGE':
                        createImg(details, data);
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

function listTargets(url, ul) {
    const wsUrl = new URL('list', location.href);
    wsUrl.protocol = 'ws';
    const ws = new WebSocket(wsUrl.toString());
    ws.addEventListener('error', e => console.error(e));
    // ws.addEventListener('message', msg => console.log(msg));
    ws.addEventListener('close', reason => console.warn(reason));
    
    const fuse = new Fuse([], {
        useExtendedSearch: true,
        keys: ['path'],
    });

    const input = ul.parentElement.insertBefore(document.createElement('input'), ul);
    input.placeholder = 'Search';
    input.addEventListener('input', runSearch);

    const span = ul.parentElement.insertBefore(document.createElement('span'), ul);

    function runSearch() {
        const query = input.value;
        const items = query ? fuse.search(query).map(o => o.item) : fuse.getIndex().docs;
        for (const {li} of fuse.getIndex().docs) {
            li.style.display = 'none';
        }
        for (const {li} of items) {
            li.style.display = 'inherit';
        }

        span.innerText = `${items.length} results`;

        if (items.length) {
            const sorted = [...items]
                .filter(item => item.stats)
                .sort((a, b) => {
                    return parseFloat(a.stats.ratio) - parseFloat(b.stats.ratio);
                })
                .map(o => {
                    return parseFloat(o.stats.ratio);
                });

            p0 = Math.round(sorted[0] * 100) + '%';
            p25 = Math.round(sorted[Math.floor((sorted.length - 1) * 0.25)] * 100) + '%';
            p50 = Math.round(sorted[Math.floor((sorted.length - 1) * 0.5)] * 100) + '%';
            p75 = Math.round(sorted[Math.floor((sorted.length - 1) * 0.75)] * 100) + '%';
            p100 = Math.round(sorted[sorted.length - 1] * 100) + '%';

            span.innerText += `, ${p0}--[${p25} |${p50}| ${p75}]--${p100}`;
        }
    }

    function createItem(ul, o) {
        const li = ul.appendChild(document.createElement('li'));
        o.li = li;
        const details = li.appendChild(document.createElement('details'));
        details.addEventListener('defaultCrosshairsSet', event => {
            url.fnameTemplate = o.fnameTemplate;
        })
        const summary = details.appendChild(document.createElement('summary'));
        const a = summary.appendChild(document.createElement('a'));
        a.innerText = o.path;
        a.href = `#analyze#${encodeURIComponent(o.fnameTemplate)}`;
        a.addEventListener('click', event => {
            event.preventDefault();
            url.page = 'analyze';
            url.fnameTemplate = o.fnameTemplate;
            location.reload();
        })
        if (o.stats) {
            const progress = summary.appendChild(document.createElement('progress'));
            progress.value = o.stats.ratio;
            progress.style.marginLeft = '1em';
            const span = summary.appendChild(document.createElement('span'));
            span.innerText = `${Math.round(parseFloat(o.stats.ratio) * 100)}% (${o.stats['hit count']} + ${o.stats['miss count']} = ${o.stats['count']})`;
            span.style.marginLeft = '1em';
        }
        details.dataset['type'] = 'target';
        createImg(details, `${o.path}/composite.jpg`);
        return li;
    }

    ws.addEventListener('message', ({data: msg}) => {
        const o = JSON.parse(msg)
        console.log(o);
        fuse.add(o);
        createItem(ul, o);
    });
}

function createImg(details, src) {
    if (details.dataset['type'] !== 'IMAGE') {
        console.warn('Tried to create an image on a non-image details:', details, src);
    }

    const img = document.createElement('img');
    let dragStarted;
    let dragHandled;
    img.src = src;
    let match;
    // noinspection JSAssignmentUsedAsCondition
    if (match = src.match(/#(\d+(?:\.\d+)?)..(\d+(?:\.\d+)?)$/)) {
        const [, min, max] = match;
        img.dataset.minValue = min;
        img.dataset.maxValue = max;
    }
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
    img.addEventListener('load', () => {
        const canvas = document.createElement('canvas');
        canvas.width = realImageW / defaultZoom;
        canvas.height = realImageH / defaultZoom;
        const context = canvas.getContext('2d');
        context.drawImage(img, 0, 0);
        const div = img.parentElement.insertBefore(document.createElement('div'), img.nextSibling);
        img.addEventListener('mousemove', event => {
            if (!dragStarted) {
                const x = Math.round(event.offsetX / imageZoom - imageX);
                const y = Math.round(event.offsetY / imageZoom - imageY);
                if (x < 0 || x >= canvas.width || y < 0 || y >= canvas.height) {
                    div.innerText = 'Out of range';
                } else {
                    const {data: [r, g, b, a]} = context.getImageData(x, y, 1, 1, {colorSpace: 'srgb'});
                    if (img.dataset.hasOwnProperty('minValue') && img.dataset.hasOwnProperty('maxValue') &&
                        (r === g) && (g === b) && (a === 255)) {
                        const min = parseFloat(img.dataset.minValue);
                        const max = parseFloat(img.dataset.maxValue);
                        const base = (r + g + b) / 3 / 255;
                        div.innerText = `(${ps(x, 4)}, ${ps(y, 4)}) = ${ps(base * (max - min) + min, 3)}`;
                    } else {
                        div.innerText = `(${ps(x, 4)}, ${ps(y, 4)}) = srgb(${ps(r, 3)}, ${ps(g, 3)}, ${ps(b, 3)}, ${ps(a, 3)})`;
                    }

                    function ps(i, n) {
                        return i.toString().padStart(n, ' ');
                    }
                }
            }
        });
        img.addEventListener('mouseleave', event => {
            div.innerText = '';
        });

        let lastMouseEvent;
        function keypressListener(event) {
            switch (event.key) {
                case 'r':
                    document.querySelector('#compositePreview [data-channel="red"] img').src = src;
                    document.getElementById('compositePreview').open = true;
                    event.preventDefault();
                    break;

                case 'g':
                    document.querySelector('#compositePreview [data-channel="green"] img').src = src;
                    document.getElementById('compositePreview').open = true;
                    event.preventDefault();
                    break;

                case 'b':
                    document.querySelector('#compositePreview [data-channel="blue"] img').src = src;
                    document.getElementById('compositePreview').open = true;
                    event.preventDefault();
                    break;

                case ' ':
                    setDefaultCrosshairs(lastMouseEvent);
                    event.preventDefault();
                    break;
            }
        }
        img.addEventListener('mouseenter', event => {
            window.addEventListener('keypress', keypressListener);
            lastMouseEvent = event;
        });
        img.addEventListener('mouseleave', event => {
            window.removeEventListener('keypress', keypressListener);
            lastMouseEvent = event;
        });
        img.addEventListener('mousemove', event => {
            lastMouseEvent = event;
        })
    })
    img.loading='lazy';

    details.appendChild(img);

    return img;
}

document.addEventListener('keypress', event => {
    function toggleVisible(element) {
        element.style.display = element.style.display ? '' : 'none';
    }
    
    switch (event.key) {
        case 'R':
            toggleVisible(document.querySelector('#compositePreview [data-channel="red"] img'));
            event.preventDefault();
            break;

        case 'G':
            toggleVisible(document.querySelector('#compositePreview [data-channel="green"] img'));
            event.preventDefault();
            break;

        case 'B':
            toggleVisible(document.querySelector('#compositePreview [data-channel="blue"] img'));
            event.preventDefault();
            break;
    }
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
}

function setDefaultCrosshairs(event, permitReset = true) {
    const x = Math.round(event.offsetX / imageZoom - imageX);
    const y = Math.round(event.offsetY / imageZoom - imageY);
    let wasHandled = false;

    if (url.x != x || url.y != y) {
        const crosshairsChangedEvent = new Event('defaultCrosshairsSet', {
            bubbles: true,
            cancelable: true,
            composed: false,
        });
        event.target.dispatchEvent(crosshairsChangedEvent);
        if (!crosshairsChangedEvent.defaultPrevented) {
            url.x = x;
            url.y = y;
        }
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

    const urlZoom = imageZoom.toPrecision(2);
    if (url.zoom !== urlZoom) {
        clearTimeout(zoomImages.urlSetTimeoutHandle);
        zoomImages.urlSetTimeoutHandle = setTimeout(() => url.zoom = urlZoom, 100);
    }
}

function moveImages(from, to) {
    imageX += (to.offsetX - from.offsetX) / imageZoom;
    imageY += (to.offsetY - from.offsetY) / imageZoom;
    zoomRule.style.objectPosition = `${imageX}px ${imageY}px`;
}
