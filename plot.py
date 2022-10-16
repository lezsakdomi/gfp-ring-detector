import json
import os
import re
import urllib.parse

from list_targets import walk


def generate_figure(df, x='total', y='positive ratio', c='stage',
                    facet_row: str | None = 'dataset name',
                    type='scatter'):
    import plotly.express as px

    marker_symbols = None
    marker_sizes = None
    symbol_sequence = []
    if c != 'h':
        marker_symbols = ['time not available' if pd.isna(h) else 'time available' for h in df['h']]
        marker_sizes = [(0 if pd.isna(h) else h) - (min(0, df['h'].min())) + 1 for h in df['h']]
    if len(df) > 0:
        symbol_sequence = ['x', 'circle']
        if df['h'].isna().sum() > len(df) / 2:
            symbol_sequence = symbol_sequence.reverse()
    title = f"Comparison of <i>{x}</i> and <i>{y}</i> for different <i>stage</i>s among " + (
        "datasets" if facet_row == 'dataset name' else ", ".join(
            [f"<b>{n}</b>" for n in df['dataset name'].unique()]) + " images")
    custom_data = ['dump', 'fname_template', 'string representation']
    hover_name = 'name'
    hover_data = {'stage': True, 'h': False,
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
                             facet_row=facet_row, title=title)
            fig.update_traces(notched=False, selector=dict(type='box'))
            fig.layout.yaxis.tickformat = ',.0%'

        case 'scatter_3d':
            fig = px.scatter_3d(df, x, y, 'h', c,
                                custom_data=custom_data, hover_name=hover_name, hover_data=hover_data,
                                title=title)

        case _:
            raise Exception(f"Unexpected plot type {type}")

    return fig


_df = None


def get_df():
    global _df
    if _df is None:
        _df = pd.DataFrame(
            columns=['dataset', 'dataset name', 'fname_template', 'dump', 'name', 'h', 'string representation',
                     'count', 'positive', 'negative', 'invalid',
                     ])

        h_re = re.compile(r'.*_(-?\d+)h-\d{4}$')

        for target in walk([entry.path for entry in os.scandir(folder_of_datasets)]):
            # print(target)
            row = {
                'dump': codecs.encode(pickle.dumps(target), 'base64').decode(),
                'fname_template': target.fname_template,
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
        _df['positive ratio'] = _df['positive'] / _df['total']
        _df['stage'] = [pd.NA for _ in range(len(_df))]
        _df.loc[_df['h'] != 0, 'stage'] = _df.loc[_df['h'] != 0, 'h'].astype(str) + 'h RPF'
        _df.loc[_df['h'] == 0, 'stage'] = '0h (PF)'
        _df.loc[_df['h'].isna(), 'stage'] = 'N/A'

    return _df


_app = None


def get_app():
    global _app

    import dash
    from dash import Dash, dcc, html, Input, Output

    if _app is None:
        df = get_df()

        _app = Dash()
        _app.layout = html.Div([
            dcc.Dropdown(id='dropdown',
                         options=df['dataset name'].unique(),
                         multi=True),
            dcc.Graph(id='graph', clear_on_unhover=True),
            html.Pre(id='debug'),
            html.Div(id='preview'),
            dcc.Graph(id='graph2', style={'height': '100vh'}),
            html.Pre(id='debug2'),
            html.Div(id='preview2'),
        ])

        @_app.callback(Output('graph', 'figure'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if not dataset_names:
                fig = generate_figure(df[~df['h'].isna()], c='h')
            else:
                fig = generate_figure(df[df['dataset name'].isin(dataset_names)], facet_row=None, c='dataset name')
            return fig

        @_app.callback(Output('graph2', 'figure'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if not dataset_names:
                fig = generate_figure(df[~df['h'].isna()], c='dataset name', type='scatter_3d')
            else:
                fig = None
            return fig

        @_app.callback(Output('graph', 'style'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if not dataset_names:
                return {'height': f"calc({len(df['dataset name'].unique())} * 450px / 2)"}
            else:
                return {'height': "450px"}

        @_app.callback(Output('debug', 'children'),
                       [Input('graph', 'selectedData')])
        def update(selected_data):
            if selected_data is None:
                raise dash.exceptions.PreventUpdate()

            print(selected_data)
            return ["\n".join([data['hovertext'] for data in selected_data['points']])]

        def click_handler(click_data):
            if click_data is None:
                raise dash.exceptions.PreventUpdate()

            result = []
            try:
                from skimage.util import img_as_ubyte
                from skimage.io import imread
                from io import BytesIO
                import imageio
                import base64
                import numpy as np

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
                    fname_template: str = click_data['points'][0]['customdata'][1]
                    img = np.dstack([
                        imread(fname_template.format(0)),
                        imread(fname_template.format(1)),
                        imread(fname_template.format(2)),
                    ])
                    result.append(html.H3([hover_text]))
                    result.append(html.Img(src=to_data_url(img)))
            except ImportError as e:
                result.append(html.P([
                    "Error: Failed to load preview image",
                    html.Pre([str(e)]),
                ]))

            for point in click_data['points']:
                dump, fname_template, string_repr = point['customdata'][:3]
                result.append(html.Div([
                    html.A([string_repr],
                           href="http://localhost:8080/analyze/" + urllib.parse.quote(dump),
                           target='_blank')
                ]))

            return result

        @_app.callback(Output('preview', 'children'),
                       Input('graph', 'clickData'))
        def update(click_data):
            return click_handler(click_data)

        @_app.callback(Output('preview2', 'children'),
                       Input('graph2', 'clickData'))
        def update(click_data):
            return click_handler(click_data)

        # _app.clientside_callback("""
        #     function update(clickData) {
        #         console.log(clickData);
        #         if (clickData && clickData['points'].length == 1) {
        #             targetDump = clickData.points[0].customdata[0];
        #             window.open("http://localhost:8080/analyze/"
        #                     + encodeURIComponent(targetDump),
        #                     "_blank")
        #         }
        #         return [];
        #     }
        # """,
        #                          Output('debug2', 'children'),
        #                          Input('graph', 'clickData'))

    return _app


folder_of_datasets = "C:\\Users\\led\\OneDrive - elte.hu\\képek\\BEN-Jra-TNF pathway"

if __name__ == '__main__':
    import pandas as pd
    import pickle
    import codecs

    df = get_df()
    print(df)
    print()
    print(df.describe())

    df.to_csv(os.path.join(folder_of_datasets, 'stats.csv'),
              index_label="path")

    generate_figure(df).write_html(os.path.join(folder_of_datasets, 'stats.html'))

    app = get_app()
    app.run_server(debug=True)
