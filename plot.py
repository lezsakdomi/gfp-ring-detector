import json
import os
import re

from list_targets import walk


def generate_figure(df, facet_row='dataset name'):
    import plotly.express as px

    x = 'total'
    y = 'positive ratio'
    c = 'stage'
    fig = px.scatter(df, x, y, c,
                     custom_data=['dump'],
                     hover_name='name', hover_data={'stage': False, 'h': True,
                                                    'count': True, 'positive': True, 'negative': True, 'invalid': True,
                                                    'positive ratio': ':.1%'},
                     marginal_y='box',
                     facet_row=facet_row,
                     title=f"Comparison of <i>{x}</i> and <i>{y}</i> for different <i>{c}</i> among " + (
                         "datasets" if facet_row == 'dataset name' else
                         ", ".join([f"<b>{n}</b>" for n in df['dataset name'].unique()]) + " images"))
    fig.update_traces(notched=False, selector=dict(type='box'))
    fig.layout.yaxis.tickformat = ',.0%'

    return fig


_df = None


def get_df():
    global _df
    if _df is None:
        _df = pd.DataFrame(columns=['dataset', 'dataset name', 'fname_template', 'dump', 'name', 'h',
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
                'dataset name': os.path.basename(target.dataset)
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
            dcc.Graph(id='graph'),
            html.Pre(id='debug'),
            html.Pre(id='debug2'),
        ])

        @_app.callback(Output('graph', 'figure'),
                       [Input('dropdown', 'value')])
        def update(dataset_names):
            if dataset_names is not None:
                fig = generate_figure(df[df['dataset name'].isin(dataset_names)], facet_row=None)
            else:
                fig = generate_figure(df)
            return fig

        @_app.callback(Output('debug', 'children'),
                       [Input('graph', 'clickData')])
        def update(click_data):
            if click_data is None:
                print("Received None click")
                raise dash.exceptions.PreventUpdate()

            print(click_data)
            if len(click_data['points']) == 1:
                target_dump = click_data['points'][0]['customdata'][0]
                return [
                    "Opening new window with " + target_dump,
                    html.Script([f"""
                        window.open("http://localhost:8080/analyze/"
                            + encodeURIComponent({json.dumps(target_dump)}),
                            "_blank")
                    """])
                ]
            return [repr(click_data)]

        _app.clientside_callback("""
            function update(clickData) {
                console.log(clickData);
                if (clickData && clickData['points'].length == 1) {
                    targetDump = clickData.points[0].customdata[0];
                    window.open("http://localhost:8080/analyze/"
                            + encodeURIComponent(targetDump),
                            "_blank")
                }
                return [];
            }
        """,
                                 Output('debug2', 'children'),
                                 Input('graph', 'clickData'))

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
