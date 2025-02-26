from data import Data
from dash import Dash, dash_table, html, dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import plotly.express as px
from dash_table.Format import Format, Scheme


data = Data()
app = Dash(__name__)

data.fetch()
groups = data.get_groups()


fig = go.Figure()

oxii_13_12_corr_columns = []
for item, df in groups.items():
    if df["Sample Name"].iloc[0].lower().startswith("oxii"):
        fig.add_trace(
            go.Scatter(
                x=df["Meas"],
                y=df["13/12 corr"],
                mode="lines+markers",
                name=f"sample {item}",
            )
        )
        oxii_13_12_corr_columns.append(df["13/12 corr"])

y_mean = np.mean(oxii_13_12_corr_columns, axis=0)
print(f'YYYYYYYYYYYYYYYYYYYYYYYYY: {y_mean}')



def get_column_precision(col: str) -> int:
    match col:
        case "FacTR":
            return 1
        case "bias":
            return 2
        case (
            "12Cle"
            | "13Cle"
            | "12Che"
            | "13Che"
            | "13/12le"
            | "13/12he"
            | "14/12he"
            | "14/13he"
            | "13/12new"
            | "13/12 corr"
            | "14/12corr"
            | "14/13corr"
        ):
            return 4
        case _:
            return 0


float_columns = [
    "12Cle",
    "13Cle",
    "12Che",
    "13Che",
    "13/12le",
    "13/12he",
    "14/12he",
    "14/13he",
    "13/12new",
    "13/12 corr",
    "14/12corr",
    "14/13corr",
    "bias",
    "FacTR",
]


tables = [
    html.Div(
        [
            dash_table.DataTable(
                df.to_dict("records"),
                [
                    (
                        {
                            "name": col,
                            "id": col,
                            "type": "numeric",
                            "format": Format(precision=4, scheme=Scheme.exponent),
                        }
                        if col in float_columns
                        else {"name": col, "id": col}
                    )  # Apply formatting only to float columns
                    for col in df.columns
                ],
                column_selectable=None,
                editable=False,
                hidden_columns=[
                    "13/12new",
                    "E",
                    "Run Completion Time",
                    "Grp",
                    "Sample Name 2",
                ],
                style_table={"overflowX": "auto"},
            ),
            html.P("Sample"),
        ],
        style={"margin-bottom": "20px"},
    )
    for df in groups.values()
]


# App layout
app.layout = html.Div(
    [
        # Left side: Tables
        html.Div(
            [html.Div([table]) for table in tables],
            style={"flex": "1", "padding": "10px"},
        ),
        # Right side: Graph + Slider
        html.Div(
            [
                dcc.Graph(figure=fig),
                dcc.Slider(
                    min=-10,
                    max=10,
                    step=1,
                    value=0,
                    marks={i: str(i) for i in range(-10, 11)},
                ),
            ],
            style={"flex": "1", "padding": "10px"},
        ),
    ],
    style={"display": "flex"},
)

if __name__ == "__main__":
    app.run(debug=True, port=8001)
    print(groups)
