<head>
   <meta charset="UTF-8">
   <title>IntelliJ Markdown Preview</title>               
   <style>/* Reworked by IntelliJ Team The MIT License (MIT) Copyright (c) JetBrains Adapted from https://github.com/sindresorhus/github-markdown-css The MIT License (MIT) Copyright (c) Sindre Sorhus &lt;sindresorhus@gmail.com&gt; (sindresorhus.com) Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. */ @font-face { font-family: octicons-anchor; src: url(data:font/woff;charset=utf-8;base64,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) format('woff'); } body { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, freesans, sans-serif; font-size: 14px; line-height: 1.6; word-wrap: break-word; margin: 0 2em; } strong { font-weight: bold; } img { border: 0; } input { color: inherit; font: inherit; margin: 0; line-height: normal; } html input[disabled] { cursor: default; } input[type="checkbox"] { box-sizing: border-box; padding: 0; } body * { box-sizing: border-box; } input { font: 13px/1.4 Helvetica, arial, nimbussansl, liberationsans, freesans, clean, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol"; } a { text-decoration: none; } a:hover, a:active { text-decoration: underline; } hr { height: 1px; padding: 0; margin: 20px 0; border: 0 none; } hr:before { display: table; content: ""; } hr:after { display: table; clear: both; content: ""; } blockquote { margin: 0; } ul, ol { padding: 0; margin-top: 0; margin-bottom: 0; } ol ol, ul ol { list-style-type: lower-roman; } ul ul ol, ul ol ol, ol ul ol, ol ol ol { list-style-type: lower-alpha; } dd { margin-left: 0; } .octicon { font: normal normal normal 16px/1 octicons-anchor; display: inline-block; text-decoration: none; text-rendering: auto; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; } .octicon-link:before { content: '\f05c'; } .markdown-body &gt; *:first-child { margin-top: 0 !important; } .markdown-body &gt; *:last-child { margin-bottom: 0 !important; } .anchor { position: absolute; top: 0; left: 0; display: block; padding-right: 6px; padding-left: 30px; margin-left: -30px; } .anchor:focus { outline: none; } h1, h2, h3, h4, h5, h6 { position: relative; margin-top: 1em; margin-bottom: 16px; font-weight: bold; line-height: 1.4; } h1 .octicon-link, h2 .octicon-link, h3 .octicon-link, h4 .octicon-link, h5 .octicon-link, h6 .octicon-link { display: none; color: #000; vertical-align: middle; } h1:hover .anchor, h2:hover .anchor, h3:hover .anchor, h4:hover .anchor, h5:hover .anchor, h6:hover .anchor { padding-left: 8px; margin-left: -30px; text-decoration: none; } h1:hover .anchor .octicon-link, h2:hover .anchor .octicon-link, h3:hover .anchor .octicon-link, h4:hover .anchor .octicon-link, h5:hover .anchor .octicon-link, h6:hover .anchor .octicon-link { display: inline-block; } h1 { font-size: 2.2em; padding-top: 0.6em; } h1 .anchor { line-height: 1; } h2 { font-size: 1.8em; line-height: 1.2; padding-top: 0.6em; } h2 .anchor { line-height: 1.2; } h3 { font-size: 1.3em; line-height: 1; padding-top: 0.6em; } h3 .anchor { line-height: 1.2; } h4 { font-size: 1em; } h4 .anchor { line-height: 1.2; } h5 { font-size: 1em; } h5 .anchor { line-height: 1.1; } h6 { font-size: 1em; } h6 .anchor { line-height: 1.1; } p, blockquote, ul, ol, dl, table, pre { margin-top: 16px; margin-bottom: 16px; } ul, ol { padding-left: 2em; } ul ul, ul ol, ol ol, ol ul { margin-top: 0; margin-bottom: 0; } li &gt; p { margin-top: 0; margin-bottom: 0; } dl { padding: 0; } dl dt { padding: 0; margin-top: 16px; font-size: 1em; font-style: italic; font-weight: bold; } dl dd { padding: 0 16px; margin-bottom: 16px; } blockquote { padding: 10px 10px 10px 16px; border-left: 2px solid; border-radius: 0 3px 3px 0; } blockquote &gt; :first-child { margin-top: 0; } blockquote &gt; :last-child { margin-bottom: 0; } table { display: block; width: 100%; overflow: auto; word-break: normal; border-collapse: collapse; border-spacing: 0; font-size: 1em; } table th { font-weight: bold; } table th, table td { padding: 6px 13px; background: transparent; } table tr { border-top: 1px solid; } img { max-width: 100%; box-sizing: border-box; } code { font: 0.9em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 0.2em 0.4em; margin: 2px; border-radius: 3px; } pre &gt; code { padding: 0; margin: 0; font-size: 100%; word-break: normal; white-space: pre; background: transparent; border: 0; } .highlight { margin-bottom: 16px; } .highlight pre, pre { font: 0.85em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 16px; overflow: auto; line-height: 1.45; border-radius: 3px; } pre code { display: inline; max-width: initial; padding: 0; margin: 0; overflow: initial; line-height: inherit; word-wrap: normal; background-color: transparent; border: 0; } pre code:before, pre code:after { content: normal; } kbd { font: 0.9em "JetBrains Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace; padding: 0.2em 0.4em; margin: 2px; border-radius: 3px; } .task-list-item { list-style-type: none; } .task-list-item + .task-list-item { margin-top: 3px; } .task-list-item input { margin: 0 0.35em 0.25em -0.6em; vertical-align: middle; } :checked + .radio-label { z-index: 1; position: relative; } span.user-del { text-decoration: line-through; } ::-webkit-scrollbar { width: 6px; height: 6px; } ::-webkit-scrollbar-thumb { -webkit-border-radius: 10px; } ::-webkit-scrollbar-track:vertical { -webkit-box-shadow: -1px 0 0 #ededed; } ::-webkit-scrollbar-track { background-color: transparent; } ::-webkit-scrollbar { width: 6px; } </style>
   <style>body { background-color: rgba(43, 43, 43, 255.0); font-size: 14px !important; } body, p, blockquote, ul, ol, dl, table, pre, code, tr { color: rgba(169, 183, 198, 255.0); } a { color: rgba(88, 157, 246, 255.0); } table td, table th { border: 1px solid rgba(81, 81, 81, 255.0); } hr { background-color: rgba(81, 81, 81, 255.0); } kbd, tr { border: 1px solid rgba(81, 81, 81, 255.0); } h6 { color: rgba(120, 120, 120, 255.0); } blockquote { border-left: 2px solid rgba(88, 157, 246, 0.4); } ::-webkit-scrollbar-thumb { background-color: rgba(166, 166, 166, 0.2784313725490196); } blockquote, code, pre { background-color: rgba(212, 222, 231, 0.09803921568627451); }</style>
   <style>/* Copyright 2000-2021 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license that can be found in the LICENSE file. */ .code-fence-highlighter-copy-button { float: right; display: flex; } .code-fence-highlighter-copy-button-icon { max-width: 1em; } .code-fence:hover .code-fence-highlighter-copy-button-icon { /*noinspection CssUnknownTarget*/ content: url("copy-button-copy-icon.png"); } .code-fence:hover .code-fence-highlighter-copy-button:hover .code-fence-highlighter-copy-button-icon { /*noinspection CssUnknownTarget*/ content: url("copy-button-copy-icon-hovered.png"); cursor: pointer; } </style>
   <style>/* Copyright 2000-2021 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license that can be found in the LICENSE file. */ .run-icon &gt; img { max-width: 1em; vertical-align: text-top; margin-right: 0.3em; } .code-block { position: absolute; left: 1em; } .hidden { display: none; }</style>
</head>

# gfp-ring-detector

## Szoftverk??vetelm??nyek, let??lt??s

### Futtat??s Windowson
A program Windowson futtathat?? v??ltozata
egy egyszer??en haszn??lhat?? ??nkicsomgol?? program
form??j??ban ker??l terjeszt??sre.

Az al??bb dokument??lt v??ltozat let??lthet?? itt:
[gfp-ring-detector.exe](dist-windows/gfp-ring-detector.exe)
(Forr??sk??d: [{{ GITHUB_REF_NAME }}, {{ "now" | date: "%F %R" }}](https://github.com/{{ GITHUB_REPOSITORY }}/tree/{{ GITHUB_SHA }}))

A legut??bbi automatikus build let??lthet?? a k??vetkez?? linkkel,
amennyiben az elm??lt 90 napban volt friss??t??s:
<https://bit.ly/gfp-ring-detector-downloader>

### Futtat??s Linuxon (fejleszt??knek)
A forr??sk??db??l val?? futtat??shoz sz??ks??g van
az [Anaconda](https://www.anaconda.com/products/distribution) telep??t??s??re illetve egy
[??j k??rnyezet l??trehoz??s??ra](https://docs.anaconda.com/anaconda/navigator/tutorials/manage-environments/#importing-an-environment)
a `conda-env.yml` alapj??n.

Ezut??n az adott k??rnyezet aktiv??l??s??t k??vet??en ind??tsuk el
??zl??s szerint a `server.py` vagy `interactive-server.py` programot.

## Dokument??ci??

### Felhaszn??l??i dokument??ci??

#### ??ttekint??s

A program webes fel??letr??l haszn??lhat??.

Ind??t??skor p??r felugr?? dial??gus ablakban ki kell v??lasztanunk,
hogy melyik mapp??ban tal??lhat??ak az elemezni k??v??nt f??jlok ("dataset"),
tov??bb?? a a program megk??rdez n??h??ny, az adathalmazra vonatkoz?? inform??ci??t,
majd megny??lik egy b??ng??sz??ablak, amelyben bet??lt??dik a program webes fel??lete.

Ez alatt megny??lik egy konzolos ablak, amelyben
a program az esetleges hiba??zeneteket el??nk t??rja. A program le??ll??t??s??hoz
ezt az ablakot kell bez??rni, mindaddig, am??g a konzolablak nyitva van,
ak??r t??bb f??jlt is megnyithatunk k??l??nb??z?? lapokon.

[//]: # (![A program m??k??d??s??nek ??ttekint??se]&#40;interactive-server-overview.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

start

repeat
    :Mappav??laszt??s;
    if (Van m??r dataset.toml f??jl?) then (l??tezik)
        break
    else (m??g nincs)
    endif
    :??j f??jl l??trehoz??sa felugr??-ablakkal;
repeat while (dataset.toml elmentve?) is ("M??gsem") not ("Ok")

:B??ng??sz?? megnyit??sa;
:Szerver elind??t??sa;

fork
    #darkGreen:Szerver fut ??s el??rhet?? b??ng??sz??b??l
    (L??sd ""server.puml"")|
fork again
    while (fekete ablak nyitva van?)
    endwhile (bez??rtuk az ablakot)
    #black:Szerver bez??r??sa;
end merge

stop

@enduml
```

Mivel a program egy webszervert ind??t el,
a Windows t??zfal ind??t??skor megk??rdezheti, hogy szeretn??nk-e
enged??lyezni a m??s g??pekkel val?? kommunik??l??st.
Ha azt szeretn??nk, hogy a h??l??zatunkra kapcsolt m??s
sz??m??t??g??pekr??l is vez??relni lehessen a programunkat, akkor
engedj??k ??t a programot a t??zfalon, ellenkez?? esetben ne.
Sajnos a be??ll??t??s m??dos??t??sa n??mileg k??r??lm??nyes, ??s
legk??zelebbi ind??t??skor nem fogja a Windows megk??rdezni.

#### A webes fel??let haszn??lata

A program webes fel??let??n lehet??s??g van az analiz??land??
felv??telek list??z??s??ra, egyedi k??pek analiz??l??s??ra.

Ha kiv??lasztunk egy k??pet elemz??sre, akkor egyr??szt
a webes fel??let megk??ri a konzolos alkalmaz??st, hogy
v??gezzen el anal??zist az adott k??pen, tov??bb??
val??s id??ben jelen??ti meg sz??munkra a r??szeredm??nyeket.
_Mind az egyes l??p??sek kimenetei ??s a bemenetei is l??that??ak._ 

Ha r??vissz??k az egeret egy-egy k??pre, akkor van lehet??s??g
nagy??t??sra/kicsiny??t??sre (g??rg??), a k??p arr??bbh??z??s??ra,
vagy ak??r sz??nes kompozit l??trehoz??s??ra az `r`/`g`/`b` gombokkal,
vagy a kompozit k??pen az egyes csatorn??k ki-/bekapcsol??s??ra
ha ugyanezen gombok mellett nyomva tartjuk a `shit` gombot.

Az al??bbi diagramon k??kkel jel??ltem azokat az ??llapotokat,
amelyek megmaradnak, ha ??jrat??ltj??k az oldalt, vagy
ha a c??msort ??tadjuk valakinek, esetleg elmentj??k az
oldalt k??nyvjelz??be.

[//]: # (![A webes felhaszn??l??i fel??let]&#40;website-pages.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

[*] -[dotted]-> list: Alap??rtelmezetten\nmegny??lik a b??ng??sz??ben
list --> analyze: F??jlra kattintunk

state "F??jlok list??z??sa" as list #blue {
    [*] -[dotted]-> noFilter
    noFilter --> filtered
    filtered --> filtered
    state "Keres??mez?? ??res" as noFilter: Nincs boxplot
    state "Sz??r??felt??tel megadva" as filtered: Van boxplot
}
list: Van lehet??s??g keres??vel sz??rni

state "Analiz??l??s" as analyze #blue {
    state "F??jl ismeretlen" as fileUnknown #blue
    state "F??jl kiv??lasztva" as fileKnownAndAnalyzing #blue {
        state connected {
            state analyzing1 {
                state got1inputs
                state got1outputs
                state got1error #darkRed
            
                [*] -[dotted]> got1inputs: ????
                got1inputs -[dotted]> got1outputs: ????
                got1outputs -[dotted]> [*]: ????
                got1inputs -[dotted]-> got1error: ????
            }
                    
            state analyzing2 {
                state got2inputs
                state got2outputs
                state got2error #darkRed
            
                [*] -[dotted]> got2inputs: ????
                got2inputs -[dotted]> got2outputs: ????
                got2outputs -[dotted]> [*]: ????
                got2inputs -[dotted]-> got2error: ????
            }
        
            state analyzing3 {
                state got3inputs
                state got3outputs
                state got3error #darkRed
            
                [*] -[dotted]> got3inputs: ????
                got3inputs -[dotted]> got3outputs: ????
                got3outputs -[dotted]> [*]: ????
                got3inputs -[dotted]-> got3error: ????
            }
                
            [*] -[dotted]-> analyzing1: ????
            analyzing1 -[dotted]-> analyzing2: ????
            analyzing2 -[dotted]-> analyzing3: ????
            analyzing3 -[dotted]-> [*]: ????
        }
        
        state wsError #darkRed
        
        [*] -[dotted]-> connected
        'connected -[dotted]-> [*]: ????
        connected -[dotted]-> wsError: ????
    }

    fileUnknown -[dotted]-> fileKnownAndAnalyzing: F??jln??v bek??r??se\nfelugr?? ablakban
    [*] -[dotted]-> fileKnownAndAnalyzing

    ||

    state "F??zis ismeretlen" as phaseUnknown #blue
    state "F??zis kiv??lasztva" as phaseSelected #blue: ""load"" / ""clean"" / stb...
    state "F??zis ??s szekci?? kiv??lasztva" as sectionSelected #blue: bemenet / kimenet (als?? vagy fels??)

    [*] -[dotted]> phaseUnknown
    phaseUnknown -[hidden]-> phaseSelected
    phaseSelected --> sectionSelected: F??l lenyit??sa
    
    phaseUnknown ---> sectionSelected: F??l lenyit??sa

    phaseUnknown -[dashed]--> sectionSelected: Koordin??t??k kiv??laszt??sa

    ||
    
    state "K??pkimenet ismeretlen" as outputUnknown #blue
    state "K??pkimenet kiv??lasztva" as outputSelected #blue: DsRed / GFP / DAPI / ...
    
    [*] -[dotted]> outputUnknown
    outputUnknown --> outputSelected: F??l lenyit??sa

    outputUnknown -[dashed]--> outputSelected: Koordin??t??k kiv??laszt??sa
    outputSelected -[dashed]--> outputUnknown: Koordin??t??k t??rl??se

    --

    state "C??lkereszt az eg??rn??l" as hover {
        state "K??p teljes m??retben" as zoomUnknown #blue
        state "K??p nagy??tva" as zoomSelected #blue

        [*] -[dotted]> zoomUnknown
        zoomUnknown -> zoomSelected: G??rget??s
        zoomSelected -> zoomSelected: G??rget??s

        --

        state "K??p a keretben" as movedUnknown
        state "K??p elmozgatva" as movedSelected

        [*] -[dotted]> movedUnknown
        movedUnknown -> movedSelected: Arr??bbh??z??s
        movedSelected -> movedSelected: Arr??bbh??z??s

        --

        state "Koordin??t??k t??r??lve" as coordinatesUnknown #blue
        state spacePressed <<choice>>
        state "Koordin??t??k kiv??lasztva" as coordinatesSelected #blue

        [*] -r-> coordinatesUnknown
        coordinatesUnknown --> coordinatesSelected: "space"
        coordinatesSelected -r-> spacePressed: "space"
        spacePressed -l-> coordinatesSelected: random helyen
        spacePressed -l-> coordinatesUnknown: ugyanott mint\naz el??bb

        --

        state "V??r??s csatorna be??ll??tva" as redSelected
        [*] -> redSelected: "r"
        redSelected -> redSelected: "r"

        --

        state "Z??ld csatorna be??ll??tva" as greenSelected
        [*] -> greenSelected: "g"
        greenSelected -> greenSelected: "g"

        --

        state "K??k csatorna be??ll??tva" as blueSelected
        [*] -> blueSelected: "b"
        blueSelected -> blueSelected: "b"

        --

        state "RGB el??n??zet becsukva" as compositePreviewCollapsed
        state "RGB el??n??zet kinyitva" as compositePreviewOpen
        
        [*] -[dotted]> compositePreviewCollapsed
        compositePreviewCollapsed -> compositePreviewOpen: F??l lenyit??sa
        compositePreviewOpen -> compositePreviewCollapsed: F??l becsuk??sa
        compositePreviewCollapsed -[dashed]> compositePreviewOpen: "r" | "g" | "b"
        
        --
        
        state "V??r??s csatorna l??that??" as redVisible
        state "V??r??s csatorna nem l??that??" as redInvisible
        
        [*] -[dotted]> redVisible
        redVisible -> redInvisible: "shift" + "R"
        redInvisible -> redVisible: "shift" + "R"
    
        --
        
        state "Z??ld csatorna l??that??" as greenVisible
        state "Z??ld csatorna nem l??that??" as greenInvisible
        
        [*] -[dotted]> greenVisible
        greenVisible -> greenInvisible: "shift" + "G"
        greenInvisible -> greenVisible: "shift" + "G"
    
        --
        
        state "K??k csatorna l??that??" as blueVisible
        state "K??k csatorna nem l??that??" as blueInvisible
        
        [*] -[dotted]> blueVisible
        blueVisible -> blueInvisible: "shift" + "B"
        blueInvisible -> blueVisible: "shift" + "B"
    }

    state "C??lkereszt a kiv??lasztott helyen" as noHover

    noHover --> hover: R??vissz??k az\negeret egy k??pre
    hover --> noHover: Levissz??k az egeret a k??pr??l
}

@enduml
```

#### Algoritmus

A program kor??bbi verzi??ir??l k??sz??lt egy sz??nes-szagos le??r??s,
ez el??rhet?? a k??vetkez?? linken:  
<https://bit.ly/gfp-ring-detector-v2-demo>

A program ??ltal v??grehajtott algoritmust az al??bbi diagramon szeml??ltetem:

[//]: # (![A pipeline fel??p??t??se]&#40;pipeline.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

start

card #2e2e2e """load""" {
    :""dataset.toml"" beolvas??sa\\
    :DsRed beolvas??sa\\
    :GFP beolvas??sa\\
    :DAPI beolvas??sa\\
    :DsRed, GFP, DAPI>
}

card #2e2e2e """clean""" {
    :""DsRed"", ""GFP""<
    :DsRed gauss elmos??s (??=1);
    :GFP gauss elmos??s (??=1);
    :DsRed ki??gett r??szeinek t??rl??se (r=30, i>80);
    :""DsRed"", ""GFP"">
}

card #2e2e2e """edge_detect""" {
    :""DsRed""<
    :Sobel-f??le deriv??l??s (v??zszintesen);
    note right: ""edges_h""
    :Sobel-f??le deriv??l??s (f??gg??legesen);
    note right: ""edges_v""
    :Sobel-f??le deriv??l??s (abszol??t??rt??kben);
    note right: ""edges""
    partition "Sz??nes k??p el????ll??t??sa"
        :Sz??g sz??m??t??sa v??zszintes/f??gg??leges k??z??tt;
        note: hue
        :Teljesen feh??r k??p gener??l??sa;
        note: saturation
        :Abszol??t deriv??lt maximaliz??l??sra 1-re;
        note: value
        :""hsv2rgb(hue, saturation, value)""]
        note right: ""edges""
    end group
    :""edges_h"", ""edges_v"", ""edges"", ""edges_colorful"">
}

card #2e2e2e """edge_abs""" {
    :""edges_h"", ""edges_v""<
    :Abszol??t??rt??k (v??zszintes deriv??lton);
    :Abszol??t??rt??k (f??gg??leges deriv??lton);
    :Sz??g sz??m??t??sa v??zszintes/f??gg??leges k??z??tt;
    :""edges_h_abs"", ""edges_v_abs"", ""edges_angle"">
}

card #2e2e2e """find_granule_centers""" {
    :""DsRed""<
    :Lok??lis maximumok megkeres??se\n(Legal??bb 15 px t??vols??gra, 0.6-os ??rt??k f??l??tt);
    :""coordinates"">
}

card #2e2e2e """threshold""" {
    :""GFP""<
    :Gauss sim??t??s;
    :Eredm??ny kivon??sa az eredetib??l\n(k??l??nbs??g vizsg??lata);
    :Kivonunk 0.01-et;
    :""GFP"">
}

card #2e2e2e """analyze_coordinates""" {
    :""all_coordinates"", ""edges"", ""edges_angle"", ""GFP""<
    :GFP bin??riss?? alak??t??sa\n//( > 0 ? )//;
    while (??sszes granulumra) is (van granulum k??z??ppont a list??ban)
        :K??z??ppont felrajzol??sa a lumenek k??z??;
        note right: ""all_granules""
        partition "Granulum feldolgoz??sa" {
            :Deriv??lt abszol??t??rt??kek lem??retez??se\n(30x30px a k??z??ppont k??r??l);
            note left: ""edges""
            :Deriv??ltak ir??ny??nak lem??retez??se\n(30x30px a k??z??ppont k??r??l);
            note left: ""edges_angle""
            partition "Projekci?? feldolgoz??sa" {
                :V??rt ir??nyok felrajzol??sa 30x30px ter??leten
                (Egy k??rlap, amin minden sug??r olyan sz??nes, amekkora a sug??r sz??ge);
                note right: minta sz??gek
                :Abszol??t k??l??nbs??g sz??m??t??sa a minta sz??gek ??s a deriv??lt ir??nya k??z??tt;
                note right: sz??gk??l??nbs??g
                :Sz??gk??l??nbs??g inverz??nek ??sszeszorz??sa a magnitud??val;
                note right: szorzat (val??sz??n??s??g)
                :Szorzat bin??riss?? alak??t??sa ISODATA k??sz??b??l??ssel;
                note right: maszk
            }
            :Elk??l??n??l?? maszk-r??szek felsz??moz??sa
            (vizsg??l??s teljes kapcsol??d??sban);
            :Legink??bb a k??z??ppont fel?? es?? r??sz kiv??laszt??sa;
            :Konvex burok kisz??m??t??sa;
            note right: lumen
            :Lumen k??ls?? perem??nek elk??l??n??t??se;
            :K??ls?? peremb??l csak annak a ter??letnek a figyelembe v??tele,\nahol eredetileg is ??tfed??sben volt a r??sszel;
            :K??ls?? perem megn??vel??se 3 pixellel;
            note right: membr??n
            :Membr??n ??s a GFP k??z??tt ??tfed??s keres??se;
            :Guo & Hall f??le morfol??giai elv??kony??t??s v??grehajt??sa 1px vastags??gig;
            note right: gy??r??
            :Membr??non Guo & Hall f??le elv??kony??t??s alkalmaz??sa 1px vastags??gig;
            note right: hamis gy??r??
        }
        if (Van eredm??ny?) then (van)
            if (Ismert a lumen?) then (lumen meghat??rozva)
                :Lumen felrajzol??sa;
                note right: ""all_granules""
            endif
            if (Ismert a membr??n?) then (membr??n meghat??rozva)
                :Membr??n felrajzol??sa a membr??n ter??letek k??z??;
                note right: ""rings_searched""
            endif
            if (Ismert a hamis gy??r???) then (hamis gy??r?? meghat??rozva)
                :Hamis gy??r?? felrajzol??sa a membr??nok k??z??;
                note right: ""rings_expected""
            endif
            if (Ismert a d??nt??s?\n("j??" vagy "rossz")) then (d??nt??s meghat??rozva)
                switch (Mi a d??nt??s?)
                case (J?? granulum)
                    :Koordin??ta felv??tele a j?? koordin??t??k k??z??;
                    note right: ""good_coordinates""
                    :Lumen felrajzol??sa a j?? lumenek k??z??;
                    note right: ""good_granules""
                    :Gy??r?? felrajzol??sa a j?? membr??nok k??z??;
                    note right: ""rings_found""
                case (Rossz granulum)
                    :Koordin??ta felv??tele a rossz koordin??t??k k??z??;
                    note right: ""bad_coordinates""
                    :Lumen felrajzol??sa a rossz lumenek k??z??;
                    note right: ""bad_granules""
                    :Gy??r?? felrajzol??sa a rossz membr??nok k??z??;
                    note right: ""rings_too_small""
                endswitch
            endif
        endif
    endwhile (elfogytak)
    :""rings_searched"", ""all_granules"", ""rings_expected"", ""rings_found"", ""rings_too_small"", ""good_coordinates"", ""good_granules"", ""bad_coordinates"", ""bad_granules"">
}

card #2e2e2e """count""" {
    :""all_coordinates"", ""good_coordinates"", ""bad_coordinates""<
    :??res sz??veg l??trehoz??sa;
    note right: ""stat_text""
    :??sszes granulum megsz??mol??sa;
    note left: ""all_coordinates""
    note right: ""Count"" mez?? a ""stat_text"" v??g??re f??zve
    :J?? granulumok megsz??mol??sa;
    note left: ""good_coordinates""
    note right: ""Hit count"" mez?? a ""stat_text"" v??g??re f??zve
    :Rossz granulum megsz??mol??sa;
    note left: ""bad_coordinates""
    note right: ""Miss count"" mez?? a ""stat_text"" v??g??re f??zve
    :J?? ??s r??ssz granulumok ar??ny??nak kisz??m??t??sa;
    note left: ""good_coordinates"", ""bad_coordinates""
    note right: ""Ratio"" mez?? a ""stat_text"" v??g??re f??zve
    :""stat_text"">
}

stop

@enduml
```

#### A kiszolg??l??-folyamat

A konzolos alkalmaz??s bels?? m??k??d??se az al??bbi diagramon l??that??:

[//]: # (![A program reakci??ja webes lek??rdez??sekre]&#40;server.svg&#41;)

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

'split
'    -[hidden]->
    start
    :B??ng??sz??b??l megnyitunk egy lapot<
    :Webes fel??let elk??ld??se a b??ng??sz??nek>
    note: L??sd ""website-pages.puml""
    stop


'-[hidden]->

'split again
'    -[hidden]->
    start
    :A webes fel??let felcsatlakozik a szerverre<
    switch (Mi a feladat?)
    case (F??jlok list??z??sa)
        repeat
            :K??vetkez?? //*.tif_Files// mappa megkeres??se;
            :Mappa nev??nek elk??ld??se>
            if (Van benne ""composite.jpg""?) then (van)
                :""composite.jpg"" elk??ld??se>
                note: Sz??nes, RGB k??p\n(el??n??zet)
            endif
            if (Van benne ""stats.txt""?) then (van)
                :""stats.txt"" elk??ld??se>
                note: El??re elk??sz??tett anal??zis
            endif
        repeat while (Van m??g feldolgozand?? mappa?) is (van)
        stop
    case (Analiz??l??s)
        :Felv??tel mapp??j??nak bek??r??se<
        fork
            :Pipeline v??grehajt??sa|

        fork again
            while (Nyitva van a weboldal?) is (nyitva)
                :Parancsra v??rakoz??s<
                :Parancs feldolgoz??sa
                L??sd ""analyze-commands.puml""|
            endwhile (bez??rtuk az oldalt)
        endfork
        stop
    endswitch
'end split

@enduml
```

A speci??lis gombok m??k??d??s??be betekint??st ny??jthat az al??bbi diagram:

```plantuml
@startuml
!include https://raw.githubusercontent.com/ptrkcsk/one-dark-plantuml-theme/v1.0.0/theme.puml

!pragma useVerticalIf on

start

'switch (Mi a kapott parancs?)
'case (Open in editor)
if (Melyik gomb?) then (Open in editor)
    if (Forr??sk??db??l futtatjuk a programot?) then (Igen, let??lt??tt??k\na forr??sk??dot)
        :Programk??d megnyit??sa PyCharm-ban;
    else (Windows,\n.exe f??jlb??l)
        #darkRed:hiba a konzolon;
    endif
'case (Open in viewer)
elseif (Melyik gomb?) then (Open in viewer)
    :F??zis beolvas??sa<
    :F??zis kikeres??se;
    if (F??zis lefutott?) then (nem)
        label view5D_error_sp1
        label view5D_error_sp2
        label view5D_error
        #darkRed:hiba a konzolon;
    else
        if (NanoImagingPack bele van ford??tve a programba?) then (nem)
            label view5D_error_sp3
            goto view5D_error
        else
            label view5D_error_sp4
            :ImageJ 5D Viewer megnyit??sa;
        endif
    endif
'case (Open in 5D viewer)
elseif (Melyik gomb?) then (Open in 5D viewer)
    if (Interakt??van ind??tottuk?) then
        if (""extract_coordinates"" f??zis lefutott?) then (nem)
            label view5D_error_sp1
            label view5D_error_sp2
            label view5D_error
            #darkRed:hiba a konzolon;
        else
            if (NanoImagingPack bele van ford??tve a programba?) then (nem)
                label view5D_error_sp3
                goto view5D_error
            else
                label view5D_error_sp4
                :ImageJ 5D Viewer megnyit??sa;
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
