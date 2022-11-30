import os
import pickle
import re
import sys

import toml

from list_targets import walk


def generate_figure(df, x='total', y='positive ratio', c='RPF',
                    group: str | None = None,
                    type='scatter',
                    try_showing_stage=True):
    import pandas as pd
    import plotly.express as px

    time_availability = ['time not available' if pd.isna(h) else 'time available' for h in df['h']]

    marker_symbols = None
    symbol_sequence = None

    if group is None and not h_columns.isdisjoint([x]):
        group = time_availability
    elif try_showing_stage:
        marker_symbols = time_availability
        symbol_sequence = []
        if len(df) > 0 and df['h'].isna().sum() > 0:
            symbol_sequence = ['x', 'circle']
            if df['h'].isna().sum() > len(df) / 2:
                symbol_sequence = symbol_sequence.reverse()

    marker_sizes = None
    if try_showing_stage and h_columns.isdisjoint([x, y, c, group]):
        marker_sizes = [(0 if pd.isna(h) else h) - (min(0, df['h'].min())) + 1 for h in df['h']]

    title = f"Comparison of <i>{x}</i> and <i>{y}</i> for different <i>stage</i>s among " + (
        "datasets" if group == 'dataset name' else ", ".join(
            [f"<b>{n}</b>" for n in df['dataset name'].unique()]) + " images")
    custom_data = ['dump', 'fname_template', 'string representation', 'csv path', 'stats path']
    hover_name = 'name'
    hover_data = {'stage': True,
                  'count': True, 'positive': True, 'negative': True,
                  'invalid': True,
                  'positive ratio': ':.1%',
                  # 'size': False, 'symbol': False,
                  }

    match type:
        case 'scatter':
            fig = px.scatter(df, x, y, c, marker_symbols, marker_sizes,
                             symbol_sequence=symbol_sequence,
                             custom_data=custom_data, hover_name=hover_name, hover_data=hover_data,
                             marginal_y='box',
                             marginal_x=None if group else 'histogram',
                             facet_row=group, title=title)
            fig.update_traces(notched=False, selector=dict(type='box'))
            fig.layout.yaxis.tickformat = ',.0%'

        case 'strip':
            fig = px.strip(df, x, y, c,
                           custom_data=custom_data, hover_name=hover_name, hover_data=hover_data,
                           facet_row=group, title=title)
            fig.update_traces(notched=False, selector=dict(type='box'))
            fig.layout.yaxis.tickformat = ',.0%'

        case 'box':
            fig = px.box(df, x, y, c,
                         custom_data=custom_data, hover_name=hover_name, hover_data=hover_data,
                         facet_col=group, title=title)
            fig.update_layout(legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ))
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
            fig.layout.yaxis.tickformat = ',.0%'

        case 'scatter_3d':
            fig = px.scatter_3d(df, x, y, 'RPF', c,
                                custom_data=custom_data, hover_name=hover_name, hover_data=hover_data,
                                title=title)

        case _:
            raise Exception(f"Unexpected plot type {type}")

    return fig


_df = None

h_columns = {'h', 'stage', 'RPF'}

_config = None


def get_config():
    global _config

    if _config is not None:
        return _config

    print("Loading configuration", file=sys.stderr)

    from list_targets import default_dataset

    _config = toml.load('config.toml')

    if _config['datasets'] is None:
        _config['datasets'] = default_dataset

    if isinstance(_config['datasets'], str):
        if 'output' not in _config:
            _config['output'] = _config['datasets']
        _config['datasets'] = [entry.path for entry in os.scandir(_config['datasets'])]
    else:
        if 'output' not in _config:
            _config['output'] = default_dataset

    return _config


def get_df():
    global _df
    if _df is None:
        print("Loading statistical data", file=sys.stderr)
        import pandas as pd
        import pickle
        import codecs

        _df = pd.DataFrame(
            columns=['dataset', 'dataset name', 'fname_template', 'dump', 'name', 'h', 'string representation',
                     'csv path', 'stats path',
                     'count', 'positive', 'negative', 'invalid',
                     ])

        h_re = re.compile(r'.*_(-?\d+)h[-_]\d{4}$')

        for target in walk(get_config()['datasets']):
            # print(target)
            from base64 import urlsafe_b64encode

            row = {
                'dump': urlsafe_b64encode(pickle.dumps(target)).decode(),
                'fname_template': target.fname_template,
                'csv path': target.csv_path,
                'stats path': target.stats_path,
                'name': target.name,
                'dataset': target.dataset,
                'dataset name': os.path.basename(target.dataset),
                'string representation': str(target),
            }
            h_re_match = h_re.match(target.name)
            if h_re_match:
                row['h'] = h_re_match.group(1)
            if target.stats:
                for k in target.stats:
                    # print(k, repr(target.stats[k]))
                    row[k] = target.stats[k]
            else:
                continue
            _df.loc[target.path] = row
        _df = _df.astype({
            'h': 'Int64',
            'count': 'Int64',
            'positive': 'Int64',
            'negative': 'Int64',
            'invalid': 'Int64',
        })
        _df['total'] = _df['positive'] + _df['negative']
        _df['positive ratio'] = 1 - _df['negative'] / _df['count']
        _df['stage'] = [pd.NA for _ in range(len(_df))]
        _df.loc[_df['h'] != 0, 'stage'] = _df.loc[_df['h'] != 0, 'h'].astype(str) + 'h RPF'
        _df.loc[_df['h'] == 0, 'stage'] = '0h (PF)'
        _df.loc[_df['h'].isna(), 'stage'] = 'N/A'
        _df['RPF'] = _df['h'].fillna(0)

    return _df


_app = None


def get_app():
    global _app

    if _app is None:
        print("Loading dash app", file=sys.stderr)

        import dash
        from dash import Dash, dcc, html, Input, Output
        import diskcache
        from dash.long_callback import DiskcacheLongCallbackManager
        import dash_bootstrap_components as dbc
        from dash_bootstrap_templates import load_figure_template

        load_figure_template('DARKLY')
        dbc_css = ("https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css")
        _app = Dash(url_base_pathname='/dash/',
                    background_callback_manager=DiskcacheLongCallbackManager(diskcache.Cache()),
                    external_stylesheets=[dbc.themes.DARKLY, dbc_css])

        _app.layout = dbc.Container(style={'marginTop': '12px'}, children=[
            dbc.Row([
                dbc.Col(dcc.Dropdown(id='dropdown',
                                     options=get_df()['dataset name'].unique(),
                                     multi=True)),
                dbc.Col(dbc.Button("🔃 Reload data", 'reload', color='primary'),
                        style={'flexGrow': '0', 'flexBasis': 'content'}),
            ]),
            dbc.Row([
                dbc.Label("Pupae stage visualization:"),
                dbc.RadioItems(id='radio', inline=True, value="size"),
            ], id='radioContainer'),
            dcc.Graph(id='graph', clear_on_unhover=True),
            html.Pre(id='debug'),
            html.Div(id='preview'),
        ], fluid=True, className="dbc")

        @_app.callback(Output('dropdown', 'options'),
                       Input('reload', 'n_clicks'),
                       background=True,
                       running=[
                           (Output('reload', 'disabled'), True, False),
                       ])
        def update(n_clicks):
            global _df

            if n_clicks is not None:
                _df = None

            return get_df()['dataset name'].unique()

        @_app.callback(Output('graph', 'figure'),
                       [Input('dropdown', 'value'), Input('radio', 'value'), Input('dropdown', 'options')])
        def update(dataset_names, rendering_style, dropdown_options):
            df = get_df()
            if dataset_names:
                df = df[df['dataset name'].isin(dataset_names)]

            if rendering_style == 'none':
                fig = generate_figure(df, x='dataset name', c=None, group=None, type='box', try_showing_stage=False)
            elif not dataset_names or rendering_style == 'boxplot':
                df = df[~df['h'].isna()]
                fig = generate_figure(df, x='RPF', c=None, group='dataset name', type='box')
            else:
                match rendering_style:
                    case 'size':
                        fig = generate_figure(df, c='dataset name')
                    case 'color':
                        fig = generate_figure(df, c='RPF')
                    case 'scatter':
                        fig = generate_figure(df, x='RPF', c='dataset name',
                                              type='strip')
            return fig

        @_app.callback(Output('graph', 'style'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if not dataset_names:
                # return {'height': f"calc({len(df['dataset name'].unique())} * 450px / 2)"}
                return {'height': "450px"}
            else:
                return {'height': "600px"}

        @_app.callback(Output('radio', 'options'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if not dataset_names:
                return [
                    {'value': "boxplot", 'label': "yes"},
                    {'value': "none", 'label': "no"},
                ]
            else:
                return [
                    {'value': "none", 'label': "no differentation"},
                    {'value': "boxplot", 'label': "boxplot X axis"},
                    {'value': "scatter", 'label': "scatter X axis"},
                    {'value': "color", 'label': "color"},
                    {'value': "size", 'label': "size (later is bigger)"},
                ]

        @_app.callback(Output('debug', 'children'),
                       [Input('graph', 'selectedData')])
        def update(selected_data):
            if selected_data is None:
                raise dash.exceptions.PreventUpdate()

            return [
                "\n".join([data['hovertext'] for data in selected_data['points']]),
                html.Br(), dcc.ConfirmDialogProvider(
                    dbc.Button("Remove statistics of selected images", color='danger'),
                    id='excludeSelectionDangerProvider',
                    message=f"Danger! Removing statistics is destructive, "
                            f"selected data points will be lost after reloading the data.\n"
                            f"If you ever want to see the selected {len(selected_data['points'])} images again, "
                            f"you have to re-run analysis.\n"
                            f"Did you take note of the images to be removed?"
                ), html.Span(id='excludeSelectionDebug')
            ]

        @_app.callback(Output('preview', 'children'),
                       Input('graph', 'clickData'),
                       background=True, interval=500,
                       progress=[Output('preview', 'children')],
                       progress_default=[html.Div([html.H3(), "Loading just started, or some error happened"])])
        def update(set_progress, click_data):
            result = []

            if click_data is None:
                result.append(html.Span())
                return result

            try:
                from skimage.util import img_as_ubyte
                from skimage.io import imread
                from io import BytesIO
                import imageio
                import base64
                import numpy as np
                import plotly.express as px
                import dash_bootstrap_components as dbc

                def to_data_url(image, fmt='png'):
                    image = img_as_ubyte(image)
                    buf = BytesIO()
                    imageio.imwrite(buf, image, format=fmt)
                    buf.seek(0)
                    buf.getvalue()
                    return f"data:image/{fmt};base64,{base64.b64encode(buf.getvalue()).decode()}"

                if click_data is None:
                    pass
                if len(click_data['points']) == 1:
                    hover_text: str = click_data['points'][0]['hovertext']
                    dump: str = click_data['points'][0]['customdata'][0]
                    fname_template: str = click_data['points'][0]['customdata'][1]
                    csv_path: str = click_data['points'][0]['customdata'][3]
                    stats_path: str = click_data['points'][0]['customdata'][4]

                    set_progress([
                        html.Div([
                            html.H3([hover_text]),
                            dbc.Col(dbc.Progress(value=0, label="Loading image..."), width=3),
                        ])
                    ])
                    r = imread(fname_template.format(0), as_gray=True)

                    set_progress([
                        html.Div([
                            html.H3([hover_text]),
                            dbc.Col(dbc.Progress(value=100 / 3, label="Loading image..."), width=3),
                        ])
                    ])
                    g = imread(fname_template.format(1), as_gray=True)

                    set_progress([
                        html.Div([
                            html.H3([hover_text]),
                            dbc.Col(dbc.Progress(value=200 / 3, label="Loading image..."), width=3),
                        ])
                    ])
                    b = imread(fname_template.format(2), as_gray=True)

                    img = np.dstack([r, g, b])
                    result.append(html.Div([
                        html.Div(dcc.ConfirmDialogProvider(
                            dbc.Button("Remove statistics of this image", color='danger', outline=True),
                            id='excludeImageDangerProvider',
                            message=f"Danger! Removing statistics is destructive.\n"
                                    f"If you ever want to see this image on the charts again after reloading the data, "
                                    f"you have to re-run analysis.\n"
                                    f"Did you take note of the image name ({hover_text})?"
                        ), style={'float': 'right'}),
                        html.H3(hover_text),
                        dcc.Input(type='hidden', id='excludeImagePath', value=stats_path),
                        html.Span(id="excludeImageDebug")
                    ]))

                    fig = px.imshow(img, template='plotly_dark')
                    if os.path.exists(csv_path):
                        set_progress([
                            html.Div([
                                html.H3([hover_text]),
                                dbc.Col(dbc.Progress(value=100, striped=True, label="Loading points...", animated=True),
                                        width=3),
                            ])
                        ])

                        import pandas as pd
                        df = pd.read_csv(csv_path)
                        scatter = px.scatter(df,
                                             'x', 'y', 'class',
                                             hover_data={'value': ':.3f'})
                        for trace in scatter.data:
                            fig.add_trace(trace)
                    result.append(dcc.Graph(id='image', figure=fig, style={'height': 'calc(100vw / 1388 * 1040)'}))
                    result.append(html.Pre(id='imageDebug'))
                    result.append(html.Div(dcc.ConfirmDialogProvider(
                        dbc.Button("Save these statistics", color='warning', outline=True),
                        'saveStatsDangerProvider',
                        "Warning! This will overwrite the statistics of this image.\n"
                        "After reloading the data, you will need to open this image again to reset.\n"
                        "Are you sure?"
                    ), style={'float': 'left', 'position': 'relative', 'zIndex': '1', 'top': '1em', 'left': '1em'}))
                    result.append(dcc.Graph(id='imageSelectionGraph'))
                    result.append(html.Pre(id='imageSelectionDebug'))
                    result.append(dcc.Input(id='saveStatsDumpInput', type='hidden', value=dump))
                    result.append(html.Br())
            except ImportError as e:
                result.append(html.P([
                    "Error: Failed to load preview image",
                    html.Pre([str(e)]),
                ]))

            for point in click_data['points']:
                dump, fname_template, string_repr = point['customdata'][:3]
                result.append(html.Div([
                    "Analyze: ",
                    html.A([string_repr],
                           href="/analyze/" + dump,
                           target='_blank')
                ]))

            return result

        @_app.callback(Output('excludeImageDebug', 'children'),
                       Input('excludeImageDangerProvider', 'submit_n_clicks'), Input('excludeImagePath', 'value'))
        def exclude_image(n_clicks, path):
            if n_clicks == 1:
                os.remove(path)
                return [" ", "Ok 🙂"]

        @_app.callback(Output('excludeSelectionDebug', 'children'),
                       Input('excludeSelectionDangerProvider', 'submit_n_clicks'), Input('graph', 'selectedData'))
        def exclude_selection(n_clicks, selected_data):
            if n_clicks == 1:
                for point in selected_data['points']:
                    os.remove(point['customdata'][4])
                return [" ", "Ok 🙂"]

        _app.clientside_callback(
            """
            function handleClick(graphClickData, imageFigure, imageClickData) {
                if (dash_clientside.callback_context.triggered.length === 1) {
                    switch (dash_clientside.callback_context.triggered[0].prop_id) {
                        case 'image.clickData': {
                            const {customdata: [encodedTarget]} = graphClickData.points[0];
                            if (imageClickData.points.length === 1) {
                                const {x, y} = imageClickData.points[0];
                                window.open(`/analyze/${encodedTarget}?x=${x}&y=${y}`);
                            }
                            return [];
                        }
                    }
                }
            }        
            """,
            Output('imageDebug', 'children'),
            Input('graph', 'clickData'), Input('image', 'figure'), Input('image', 'clickData'))

        def get_df_for_image_selection_data(image, selected_data):
            if not len(image['data']):
                raise dash.exceptions.PreventUpdate()

            import pandas as pd

            if selected_data is None:
                df = pd.DataFrame([
                    {'class': trace['name'], 'count': len(trace['x'])}
                    for trace in image['data']
                    if trace['type'] != 'image'
                ])
            else:
                df = pd.DataFrame(selected_data['points'])
                df['class'] = [image['data'][curveNumber]['name'] for curveNumber in df['curveNumber']]
                df = df[['class', 'pointNumber']].groupby('class').aggregate('count')
                df.reset_index(inplace=True)
                df = df.rename(columns={'index': 'class', 'pointNumber': 'count'})

            return df

        @_app.callback(Output('imageSelectionGraph', 'figure'),
                       Input('image', 'figure'), Input('image', 'selectedData'))
        def update(image, selected_data):
            import plotly.express as px

            df = get_df_for_image_selection_data(image, selected_data)
            fig = px.pie(df, names='class', values='count')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            return fig

        @_app.callback(Output('imageSelectionDebug', 'children'),
                       Input('image', 'figure'), Input('image', 'selectedData'),
                       Input('saveStatsDangerProvider', 'submit_n_clicks'), Input('saveStatsDumpInput', 'value'))
        def update(image, selected_data, n_clicks, dump):
            if n_clicks is None:
                raise dash.exceptions.PreventUpdate()

            import base64

            df = get_df_for_image_selection_data(image, selected_data)
            df.index = df['class']
            df.drop('class', axis='columns')

            if n_clicks:
                target = pickle.loads(base64.urlsafe_b64decode(dump))
                target.stats = {
                    'Count': get_df_for_image_selection_data(image, None)['count'].sum(),
                    'Positive': df.loc['positive', 'count'],
                    'Negative': df.loc['negative', 'count'],
                    'Invalid': get_df_for_image_selection_data(image, None)['count'].sum() - df['count'].sum(),
                    'Dropped': f"{1 - (df.loc['positive', 'count'] + df.loc['negative', 'count']) / df['count'].sum():.2%}",
                    'Negative ratio': f"{df.loc['negative', 'count'] / df.loc[['positive', 'negative'], 'count'].sum():.2%}",
                }
                target.save_stats()

                return " Ok " + ["😅", "🙂"][n_clicks % 2]

    return _app


if __name__ == '__main__':
    df = get_df()
    print(df)
    print()
    print(df.describe())

    output_folder = get_config()['output']

    df.to_csv(os.path.join(output_folder, 'stats.csv'),
              index_label="path")

    generate_figure(df).write_html(os.path.join(output_folder, 'stats.html'))

    app = get_app()
    app.run_server(debug=True)
