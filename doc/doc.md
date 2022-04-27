<head>
   <meta charset="UTF-8">
   <title>IntelliJ Markdown Preview</title>               
   <style>/* Reworked by IntelliJ Team The MIT License (MIT) Copyright (c) JetBrains Adapted from https://github.com/sindresorhus/github-markdown-css The MIT License (MIT) Copyright (c) Sindre Sorhus &lt;sindresorhus@gmail.com&gt; (sindresorhus.com) Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. */ @font-face { font-family: octicons-anchor; src: url(data:font/woff;charset=utf-8;base64,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) format('woff'); } body { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, freesans, sans-serif; font-size: 14px; line-height: 1.6; word-wrap: break-word; margin: 0 2em; } strong { font-weight: bold; } img { border: 0; } input { color: inherit; font: inherit; margin: 0; line-height: normal; } html input[disabled] { cursor: default; } input[type="checkbox"] { box-sizing: border-box; padding: 0; } body * { box-sizing: border-box; } input { font: 13px/1.4 Helvetica, arial, nimbussansl, liberationsans, freesans, clean, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol"; } a { text-decoration: none; } a:hover, a:active { text-decoration: underline; } hr { height: 1px; padding: 0; margin: 20px 0; border: 0 none; } hr:before { display: table; content: ""; } hr:after { display: table; clear: both; content: ""; } blockquote { margin: 0; } ul, ol { padding: 0; margin-top: 0; margin-bottom: 0; } ol ol, ul ol { list-style-type: lower-roman; } ul ul ol, ul ol ol, ol ul ol, ol ol ol { list-style-type: lower-alpha; } dd { margin-left: 0; } .octicon { font: normal normal normal 16px/1 octicons-anchor; display: inline-block; text-decoration: none; text-rendering: auto; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; } .octicon-link:before { content: '\f05c'; } .markdown-body &gt; *:first-child { margin-top: 0 !important; } .markdown-body &gt; *:last-child { margin-bottom: 0 !important; } .anchor { position: absolute; top: 0; left: 0; display: block; padding-right: 6px; padding-left: 30px; margin-left: -30px; } .anchor:focus { outline: none; } h1, h2, h3, h4, h5, h6 { position: relative; margin-top: 1em; margin-bottom: 16px; font-weight: bold; line-height: 1.4; } h1 .octicon-link, h2 .octicon-link, h3 .octicon-link, h4 .octicon-link, h5 .octicon-link, h6 .octicon-link { display: none; color: #000; vertical-align: middle; } h1:hover .anchor, h2:hover .anchor, h3:hover .anchor, h4:hover .anchor, h5:hover .anchor, h6:hover .anchor { padding-left: 8px; margin-left: -30px; text-decoration: none; } h1:hover .anchor .octicon-link, h2:hover .anchor .octicon-link, h3:hover .anchor .octicon-link, h4:hover .anchor .octicon-link, h5:hover .anchor .octicon-link, h6:hover .anchor .octicon-link { display: inline-block; } h1 { font-size: 2.2em; padding-top: 0.6em; } h1 .anchor { line-height: 1; } h2 { font-size: 1.8em; line-height: 1.2; padding-top: 0.6em; } h2 .anchor { line-height: 1.2; } h3 { font-size: 1.3em; line-height: 1; padding-top: 0.6em; } h3 .anchor { line-height: 1.2; } h4 { font-size: 1em; } h4 .anchor { line-height: 1.2; } h5 { font-size: 1em; } h5 .anchor { line-height: 1.1; } h6 { font-size: 1em; } h6 .anchor { line-height: 1.1; } p, blockquote, ul, ol, dl, table, pre { margin-top: 16px; margin-bottom: 16px; } ul, ol { padding-left: 2em; } ul ul, ul ol, ol ol, ol ul { margin-top: 0; margin-bottom: 0; } li &gt; p { margin-top: 0; margin-bottom: 0; } dl { padding: 0; } dl dt { padding: 0; margin-top: 16px; font-size: 1em; font-style: italic; font-weight: bold; } dl dd { padding: 0 16px; margin-bottom: 16px; } blockquote { padding: 10px 10px 10px 16px; border-left: 2px solid; border-radius: 0 3px 3px 0; } blockquote &gt; :first-child { margin-top: 0; } blockquote &gt; :last-child { margin-bottom: 0; } table { display: block; width: 100%; overflow: auto; word-break: normal; border-collapse: collapse; border-spacing: 0; font-size: 1em; } table th { font-weight: bold; } table th, table td { padding: 6px 13px; background: transparent; } table tr { border-top: 1px solid; } img { max-width: 100%; box-sizing: border-box; } code { font: 0.9em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 0.2em 0.4em; margin: 2px; border-radius: 3px; } pre &gt; code { padding: 0; margin: 0; font-size: 100%; word-break: normal; white-space: pre; background: transparent; border: 0; } .highlight { margin-bottom: 16px; } .highlight pre, pre { font: 0.85em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 16px; overflow: auto; line-height: 1.45; border-radius: 3px; } pre code { display: inline; max-width: initial; padding: 0; margin: 0; overflow: initial; line-height: inherit; word-wrap: normal; background-color: transparent; border: 0; } pre code:before, pre code:after { content: normal; } kbd { font: 0.9em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 0.2em 0.4em; margin: 2px; border-radius: 3px; } .task-list-item { list-style-type: none; } .task-list-item + .task-list-item { margin-top: 3px; } .task-list-item input { margin: 0 0.35em 0.25em -0.6em; vertical-align: middle; } :checked + .radio-label { z-index: 1; position: relative; } span.user-del { text-decoration: line-through; } ::-webkit-scrollbar { width: 6px; height: 6px; } ::-webkit-scrollbar-thumb { -webkit-border-radius: 10px; } ::-webkit-scrollbar-track:vertical { -webkit-box-shadow: -1px 0 0 #ededed; } ::-webkit-scrollbar-track { background-color: transparent; } ::-webkit-scrollbar { width: 6px; } </style>
   <style>body { background-color: rgba(43, 43, 43, 255.0); font-size: 14px !important; } body, p, blockquote, ul, ol, dl, table, pre, code, tr { color: rgba(169, 183, 198, 255.0); } a { color: rgba(88, 157, 246, 255.0); } table td, table th { border: 1px solid rgba(81, 81, 81, 255.0); } hr { background-color: rgba(81, 81, 81, 255.0); } kbd, tr { border: 1px solid rgba(81, 81, 81, 255.0); } h6 { color: rgba(120, 120, 120, 255.0); } blockquote { border-left: 2px solid rgba(88, 157, 246, 0.4); } ::-webkit-scrollbar-thumb { background-color: rgba(166, 166, 166, 0.2784313725490196); } blockquote, code, pre { background-color: rgba(212, 222, 231, 0.09803921568627451); }</style>
   <style>/* Copyright 2000-2021 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license that can be found in the LICENSE file. */ .code-fence-highlighter-copy-button { float: right; display: flex; } .code-fence-highlighter-copy-button-icon { max-width: 1em; } .code-fence:hover .code-fence-highlighter-copy-button-icon { /*noinspection CssUnknownTarget*/ content: url("copy-button-copy-icon.png"); } .code-fence:hover .code-fence-highlighter-copy-button:hover .code-fence-highlighter-copy-button-icon { /*noinspection CssUnknownTarget*/ content: url("copy-button-copy-icon-hovered.png"); cursor: pointer; } </style>
   <style>/* Copyright 2000-2021 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license that can be found in the LICENSE file. */ .run-icon &gt; img { max-width: 1em; vertical-align: text-top; margin-right: 0.3em; } .code-block { position: absolute; left: 1em; } .hidden { display: none; }</style>
</head>

# gfp-ring-detector

## Szoftverkövetelmények, letöltés

### Futtatás Windowson
A program Windowson futtatható változata
egy egyszerűen használható önkicsomgoló program
formájában kerül terjesztésre.

Az alább dokumentált változat letölthető itt:
[gfp-ring-detector.exe](dist-windows/gfp-ring-detector.exe)
(Forráskód: [{{ GITHUB_REF_NAME }}, {{ "now" | date: "%F %R" }}](https://github.com/{{ GITHUB_REPOSITORY }}/tree/{{ GITHUB_SHA }}))

A legutóbbi automatikus build letölthető a következő linkkel,
amennyiben az elmúlt 90 napban volt frissítés:
<https://bit.ly/gfp-ring-detector-downloader>

### Futtatás Linuxon (fejlesztőknek)
A forráskódból való futtatáshoz szükség van
az [Anaconda](https://www.anaconda.com/products/distribution) telepítésére illetve egy
[új környezet létrehozására](https://docs.anaconda.com/anaconda/navigator/tutorials/manage-environments/#importing-an-environment)
a `conda-env.yml` alapján.

Ezután az adott környezet aktiválását követően indítsuk el
ízlés szerint a `server.py` vagy `interactive-server.py` programot.

## Dokumentáció

### Felhasználói dokumentáció

#### Áttekintés

A program webes felületről használható.

Indításkor pár felugró dialógus ablakban ki kell választanunk,
hogy melyik mappában találhatóak az elemezni kívánt fájlok ("dataset"),
továbbá a a program megkérdez néhány, az adathalmazra vonatkozó információt,
majd megnyílik egy böngészőablak, amelyben betöltődik a program webes felülete.

Ez alatt megnyílik egy konzolos ablak, amelyben
a program az esetleges hibaüzeneteket elénk tárja. A program leállításához
ezt az ablakot kell bezárni, mindaddig, amíg a konzolablak nyitva van,
akár több fájlt is megnyithatunk különböző lapokon.

[//]: # (![A program működésének áttekintése]&#40;interactive-server-overview.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

start

repeat
    :Mappaválasztás;
    if (Van már dataset.toml fájl?) then (létezik)
        break
    else (még nincs)
    endif
    :Új fájl létrehozása felugró-ablakkal;
repeat while (dataset.toml elmentve?) is ("Mégsem") not ("Ok")

:Böngésző megnyitása;
:Szerver elindítása;

fork
    #darkGreen:Szerver fut és elérhető böngészőből
    (Lásd ""server.puml"")|
fork again
    while (fekete ablak nyitva van?)
    endwhile (bezártuk az ablakot)
    #black:Szerver bezárása;
end merge

stop

@enduml
```

Mivel a program egy webszervert indít el,
a Windows tűzfal indításkor megkérdezheti, hogy szeretnénk-e
engedélyezni a más gépekkel való kommunikálást.
Ha azt szeretnénk, hogy a hálózatunkra kapcsolt más
számítógépekről is vezérelni lehessen a programunkat, akkor
engedjük át a programot a tűzfalon, ellenkező esetben ne.
Sajnos a beállítás módosítása némileg körülményes, és
legközelebbi indításkor nem fogja a Windows megkérdezni.

#### A webes felület használata

A program webes felületén lehetőség van az analizálandó
felvételek listázására, egyedi képek analizálására.

Ha kiválasztunk egy képet elemzésre, akkor egyrészt
a webes felület megkéri a konzolos alkalmazást, hogy
végezzen el analízist az adott képen, továbbá
valós időben jeleníti meg számunkra a részeredményeket.
_Mind az egyes lépések kimenetei és a bemenetei is láthatóak._ 

Ha rávisszük az egeret egy-egy képre, akkor van lehetőség
nagyításra/kicsinyítésre (görgő), a kép arrébbhúzására,
vagy akár színes kompozit létrehozására az `r`/`g`/`b` gombokkal,
vagy a kompozit képen az egyes csatornák ki-/bekapcsolására
ha ugyanezen gombok mellett nyomva tartjuk a `shit` gombot.

Az alábbi diagramon kékkel jelöltem azokat az állapotokat,
amelyek megmaradnak, ha újratöltjük az oldalt, vagy
ha a címsort átadjuk valakinek, esetleg elmentjük az
oldalt könyvjelzőbe.

[//]: # (![A webes felhasználói felület]&#40;website-pages.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

[*] -[dotted]-> list: Alapértelmezetten\nmegnyílik a böngészőben
list --> analyze: Fájlra kattintunk

state "Fájlok listázása" as list #blue {
    [*] -[dotted]-> noFilter
    noFilter --> filtered
    filtered --> filtered
    state "Keresőmező üres" as noFilter: Nincs boxplot
    state "Szűrőfeltétel megadva" as filtered: Van boxplot
}
list: Van lehetőség keresővel szűrni

state "Analizálás" as analyze #blue {
    state "Fájl ismeretlen" as fileUnknown #blue
    state "Fájl kiválasztva" as fileKnownAndAnalyzing #blue {
        state connected {
            state analyzing1 {
                state got1inputs
                state got1outputs
                state got1error #darkRed
            
                [*] -[dotted]> got1inputs: 🖧
                got1inputs -[dotted]> got1outputs: 🖧
                got1outputs -[dotted]> [*]: 🖧
                got1inputs -[dotted]-> got1error: 🖧
            }
                    
            state analyzing2 {
                state got2inputs
                state got2outputs
                state got2error #darkRed
            
                [*] -[dotted]> got2inputs: 🖧
                got2inputs -[dotted]> got2outputs: 🖧
                got2outputs -[dotted]> [*]: 🖧
                got2inputs -[dotted]-> got2error: 🖧
            }
        
            state analyzing3 {
                state got3inputs
                state got3outputs
                state got3error #darkRed
            
                [*] -[dotted]> got3inputs: 🖧
                got3inputs -[dotted]> got3outputs: 🖧
                got3outputs -[dotted]> [*]: 🖧
                got3inputs -[dotted]-> got3error: 🖧
            }
                
            [*] -[dotted]-> analyzing1: 🖧
            analyzing1 -[dotted]-> analyzing2: 🖧
            analyzing2 -[dotted]-> analyzing3: 🖧
            analyzing3 -[dotted]-> [*]: 🖧
        }
        
        state wsError #darkRed
        
        [*] -[dotted]-> connected
        'connected -[dotted]-> [*]: 🖧
        connected -[dotted]-> wsError: 🖧
    }

    fileUnknown -[dotted]-> fileKnownAndAnalyzing: Fájlnév bekérése\nfelugró ablakban
    [*] -[dotted]-> fileKnownAndAnalyzing

    ||

    state "Fázis ismeretlen" as phaseUnknown #blue
    state "Fázis kiválasztva" as phaseSelected #blue: ""load"" / ""clean"" / stb...
    state "Fázis és szekció kiválasztva" as sectionSelected #blue: bemenet / kimenet (alsó vagy felső)

    [*] -[dotted]> phaseUnknown
    phaseUnknown -[hidden]-> phaseSelected
    phaseSelected --> sectionSelected: Fül lenyitása
    
    phaseUnknown ---> sectionSelected: Fül lenyitása

    phaseUnknown -[dashed]--> sectionSelected: Koordináták kiválasztása

    ||
    
    state "Képkimenet ismeretlen" as outputUnknown #blue
    state "Képkimenet kiválasztva" as outputSelected #blue: DsRed / GFP / DAPI / ...
    
    [*] -[dotted]> outputUnknown
    outputUnknown --> outputSelected: Fül lenyitása

    outputUnknown -[dashed]--> outputSelected: Koordináták kiválasztása
    outputSelected -[dashed]--> outputUnknown: Koordináták törlése

    --

    state "Célkereszt az egérnél" as hover {
        state "Kép teljes méretben" as zoomUnknown #blue
        state "Kép nagyítva" as zoomSelected #blue

        [*] -[dotted]> zoomUnknown
        zoomUnknown -> zoomSelected: Görgetés
        zoomSelected -> zoomSelected: Görgetés

        --

        state "Kép a keretben" as movedUnknown
        state "Kép elmozgatva" as movedSelected

        [*] -[dotted]> movedUnknown
        movedUnknown -> movedSelected: Arrébbhúzás
        movedSelected -> movedSelected: Arrébbhúzás

        --

        state "Koordináták törölve" as coordinatesUnknown #blue
        state spacePressed <<choice>>
        state "Koordináták kiválasztva" as coordinatesSelected #blue

        [*] -r-> coordinatesUnknown
        coordinatesUnknown --> coordinatesSelected: "space"
        coordinatesSelected -r-> spacePressed: "space"
        spacePressed -l-> coordinatesSelected: random helyen
        spacePressed -l-> coordinatesUnknown: ugyanott mint\naz előbb

        --

        state "Vörös csatorna beállítva" as redSelected
        [*] -> redSelected: "r"
        redSelected -> redSelected: "r"

        --

        state "Zöld csatorna beállítva" as greenSelected
        [*] -> greenSelected: "g"
        greenSelected -> greenSelected: "g"

        --

        state "Kék csatorna beállítva" as blueSelected
        [*] -> blueSelected: "b"
        blueSelected -> blueSelected: "b"

        --

        state "RGB előnézet becsukva" as compositePreviewCollapsed
        state "RGB előnézet kinyitva" as compositePreviewOpen
        
        [*] -[dotted]> compositePreviewCollapsed
        compositePreviewCollapsed -> compositePreviewOpen: Fül lenyitása
        compositePreviewOpen -> compositePreviewCollapsed: Fül becsukása
        compositePreviewCollapsed -[dashed]> compositePreviewOpen: "r" | "g" | "b"
        
        --
        
        state "Vörös csatorna látható" as redVisible
        state "Vörös csatorna nem látható" as redInvisible
        
        [*] -[dotted]> redVisible
        redVisible -> redInvisible: "shift" + "R"
        redInvisible -> redVisible: "shift" + "R"
    
        --
        
        state "Zöld csatorna látható" as greenVisible
        state "Zöld csatorna nem látható" as greenInvisible
        
        [*] -[dotted]> greenVisible
        greenVisible -> greenInvisible: "shift" + "G"
        greenInvisible -> greenVisible: "shift" + "G"
    
        --
        
        state "Kék csatorna látható" as blueVisible
        state "Kék csatorna nem látható" as blueInvisible
        
        [*] -[dotted]> blueVisible
        blueVisible -> blueInvisible: "shift" + "B"
        blueInvisible -> blueVisible: "shift" + "B"
    }

    state "Célkereszt a kiválasztott helyen" as noHover

    noHover --> hover: Rávisszük az\negeret egy képre
    hover --> noHover: Levisszük az egeret a képről
}

@enduml
```

#### Algoritmus

A program korábbi verzióiról készült egy színes-szagos leírás,
ez elérhető a következő linken:  
<https://bit.ly/gfp-ring-detector-v2-demo>

A program által végrehajtott algoritmust az alábbi diagramon szemléltetem:

[//]: # (![A pipeline felépítése]&#40;pipeline.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

start

card #2e2e2e """load""" {
    :""dataset.toml"" beolvasása\\
    :DsRed beolvasása\\
    :GFP beolvasása\\
    :DAPI beolvasása\\
    :DsRed, GFP, DAPI>
}

card #2e2e2e """clean""" {
    :""DsRed"", ""GFP""<
    :DsRed gauss elmosás (σ=1);
    :GFP gauss elmosás (σ=1);
    :DsRed kiégett részeinek törlése (r=30, i>80);
    :""DsRed"", ""GFP"">
}

card #2e2e2e """edge_detect""" {
    :""DsRed""<
    :Sobel-féle deriválás (vízszintesen);
    note right: ""edges_h""
    :Sobel-féle deriválás (függőlegesen);
    note right: ""edges_v""
    :Sobel-féle deriválás (abszolútértékben);
    note right: ""edges""
    partition "Színes kép előállítása"
        :Szög számítása vízszintes/függőleges között;
        note: hue
        :Teljesen fehér kép generálása;
        note: saturation
        :Abszolút derivált maximalizálásra 1-re;
        note: value
        :""hsv2rgb(hue, saturation, value)""]
        note right: ""edges""
    end group
    :""edges_h"", ""edges_v"", ""edges"", ""edges_colorful"">
}

card #2e2e2e """edge_abs""" {
    :""edges_h"", ""edges_v""<
    :Abszolútérték (vízszintes deriválton);
    :Abszolútérték (függőleges deriválton);
    :Szög számítása vízszintes/függőleges között;
    :""edges_h_abs"", ""edges_v_abs"", ""edges_angle"">
}

card #2e2e2e """find_granule_centers""" {
    :""DsRed""<
    :Lokális maximumok megkeresése\n(Legalább 15 px távolságra, 0.6-os érték fölött);
    :""coordinates"">
}

card #2e2e2e """threshold""" {
    :""GFP""<
    :Gauss simítás;
    :Eredmény kivonása az eredetiből\n(különbség vizsgálata);
    :Kivonunk 0.01-et;
    :""GFP"">
}

card #2e2e2e """analyze_coordinates""" {
    :""all_coordinates"", ""edges"", ""edges_angle"", ""GFP""<
    :GFP binárissá alakítása\n//( > 0 ? )//;
    while (Összes granulumra) is (van granulum középpont a listában)
        :Középpont felrajzolása a lumenek közé;
        note right: ""all_granules""
        partition "Granulum feldolgozása" {
            :Derivált abszolútértékek leméretezése\n(30x30px a középpont körül);
            note left: ""edges""
            :Deriváltak irányának leméretezése\n(30x30px a középpont körül);
            note left: ""edges_angle""
            partition "Projekció feldolgozása" {
                :Várt irányok felrajzolása 30x30px területen
                (Egy körlap, amin minden sugár olyan színes, amekkora a sugár szöge);
                note right: minta szögek
                :Abszolút különbség számítása a minta szögek és a derivált iránya között;
                note right: szögkülönbség
                :Szögkülönbség inverzének összeszorzása a magnitudóval;
                note right: szorzat (valószínűség)
                :Szorzat binárissá alakítása ISODATA küszöböléssel;
                note right: maszk
            }
            :Elkülönülő maszk-részek felszámozása
            (vizsgálás teljes kapcsolódásban);
            :Leginkább a középpont felé eső rész kiválasztása;
            :Konvex burok kiszámítása;
            note right: lumen
            :Lumen külső peremének elkülönítése;
            :Külső peremből csak annak a területnek a figyelembe vétele,\nahol eredetileg is átfedésben volt a résszel;
            :Külső perem megnövelése 3 pixellel;
            note right: membrán
            :Membrán és a GFP között átfedés keresése;
            :Guo & Hall féle morfológiai elvékonyítás végrehajtása 1px vastagságig;
            note right: gyűrű
            :Membránon Guo & Hall féle elvékonyítás alkalmazása 1px vastagságig;
            note right: hamis gyűrű
        }
        if (Van eredmény?) then (van)
            if (Ismert a lumen?) then (lumen meghatározva)
                :Lumen felrajzolása;
                note right: ""all_granules""
            endif
            if (Ismert a membrán?) then (membrán meghatározva)
                :Membrán felrajzolása a membrán területek közé;
                note right: ""rings_searched""
            endif
            if (Ismert a hamis gyűrű?) then (hamis gyűrű meghatározva)
                :Hamis gyűrű felrajzolása a membránok közé;
                note right: ""rings_expected""
            endif
            if (Ismert a döntés?\n("jó" vagy "rossz")) then (döntés meghatározva)
                switch (Mi a döntés?)
                case (Jó granulum)
                    :Koordináta felvétele a jó koordináták közé;
                    note right: ""good_coordinates""
                    :Lumen felrajzolása a jó lumenek közé;
                    note right: ""good_granules""
                    :Gyűrű felrajzolása a jó membránok közé;
                    note right: ""rings_found""
                case (Rossz granulum)
                    :Koordináta felvétele a rossz koordináták közé;
                    note right: ""bad_coordinates""
                    :Lumen felrajzolása a rossz lumenek közé;
                    note right: ""bad_granules""
                    :Gyűrű felrajzolása a rossz membránok közé;
                    note right: ""rings_too_small""
                endswitch
            endif
        endif
    endwhile (elfogytak)
    :""rings_searched"", ""all_granules"", ""rings_expected"", ""rings_found"", ""rings_too_small"", ""good_coordinates"", ""good_granules"", ""bad_coordinates"", ""bad_granules"">
}

card #2e2e2e """count""" {
    :""all_coordinates"", ""good_coordinates"", ""bad_coordinates""<
    :Üres szöveg létrehozása;
    note right: ""stat_text""
    :Összes granulum megszámolása;
    note left: ""all_coordinates""
    note right: ""Count"" mező a ""stat_text"" végére fűzve
    :Jó granulumok megszámolása;
    note left: ""good_coordinates""
    note right: ""Hit count"" mező a ""stat_text"" végére fűzve
    :Rossz granulum megszámolása;
    note left: ""bad_coordinates""
    note right: ""Miss count"" mező a ""stat_text"" végére fűzve
    :Jó és rössz granulumok arányának kiszámítása;
    note left: ""good_coordinates"", ""bad_coordinates""
    note right: ""Ratio"" mező a ""stat_text"" végére fűzve
    :""stat_text"">
}

stop

@enduml
```

#### A kiszolgáló-folyamat

A konzolos alkalmazás belső működése az alábbi diagramon látható:

[//]: # (![A program reakciója webes lekérdezésekre]&#40;server.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

'split
'    -[hidden]->
    start
    :Böngészőből megnyitunk egy lapot<
    :Webes felület elküldése a böngészőnek>
    note: Lásd ""website-pages.puml""
    stop


'-[hidden]->

'split again
'    -[hidden]->
    start
    :A webes felület felcsatlakozik a szerverre<
    switch (Mi a feladat?)
    case (Fájlok listázása)
        repeat
            :Következő //*.tif_Files// mappa megkeresése;
            :Mappa nevének elküldése>
            if (Van benne ""composite.jpg""?) then (van)
                :""composite.jpg"" elküldése>
                note: Színes, RGB kép\n(előnézet)
            endif
            if (Van benne ""stats.txt""?) then (van)
                :""stats.txt"" elküldése>
                note: Előre elkészített analízis
            endif
        repeat while (Van még feldolgozandó mappa?) is (van)
        stop
    case (Analizálás)
        :Felvétel mappájának bekérése<
        fork
            :Pipeline végrehajtása|

        fork again
            while (Nyitva van a weboldal?) is (nyitva)
                :Parancsra várakozás<
                :Parancs feldolgozása
                Lásd ""analyze-commands.puml""|
            endwhile (bezártuk az oldalt)
        endfork
        stop
    endswitch
'end split

@enduml
```

A speciális gombok működésébe betekintést nyújthat az alábbi diagram:

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

!pragma useVerticalIf on

start

'switch (Mi a kapott parancs?)
'case (Open in editor)
if (Melyik gomb?) then (Open in editor)
    if (Forráskódból futtatjuk a programot?) then (Igen, letöltöttük\na forráskódot)
        :Programkód megnyitása PyCharm-ban;
    else (Windows,\n.exe fájlból)
        #darkRed:hiba a konzolon;
    endif
'case (Open in viewer)
elseif (Melyik gomb?) then (Open in viewer)
    :Fázis beolvasása<
    :Fázis kikeresése;
    if (Fázis lefutott?) then (nem)
        label view5D_error_sp1
        label view5D_error_sp2
        label view5D_error
        #darkRed:hiba a konzolon;
    else
        if (NanoImagingPack bele van fordítve a programba?) then (nem)
            label view5D_error_sp3
            goto view5D_error
        else
            label view5D_error_sp4
            :ImageJ 5D Viewer megnyitása;
        endif
    endif
'case (Open in 5D viewer)
elseif (Melyik gomb?) then (Open in 5D viewer)
    if (Interaktívan indítottuk?) then
        if (""extract_coordinates"" fázis lefutott?) then (nem)
            label view5D_error_sp1
            label view5D_error_sp2
            label view5D_error
            #darkRed:hiba a konzolon;
        else
            if (NanoImagingPack bele van fordítve a programba?) then (nem)
                label view5D_error_sp3
                goto view5D_error
            else
                label view5D_error_sp4
                :ImageJ 5D Viewer megnyitása;
            endif
        endif
    else (nem)
        #darkRed:hiba a konzolon;
    endif
'endswitch
else
    #darkRed:hiba a konzolon;
endif

stop

@enduml
```
