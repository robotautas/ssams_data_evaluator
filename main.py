import time
from data import Data
from dash import Dash, dash_table, html, dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import plotly.express as px
from dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output


data = Data()
app = Dash(__name__)

data.fetch()
groups = data.get_groups()
original_groups = groups.copy()

def apply_correction_to_groups(original_groups, correction_factor):
    """Apply correction factor to all relevant isotope ratio columns."""
    modified_groups = {}

    
    for key, df in original_groups.items():
        if not isinstance(df, pd.DataFrame):
            continue
        # Create a deep copy to avoid modifying the original
        modified_df = df.copy()
        
        # Apply correction factor to 13/12 corr
        if '13/12 corr' in modified_df.columns:
            # Correction can be additive or multiplicative depending on your needs

            # Additive:
            modified_df['13/12 corr'] = modified_df['13/12he'] * ((modified_df['13/12he'].mean() / modified_df['13/12new'])**correction_factor)
            modified_df['14/12corr'] = modified_df['14/12he'] * ((modified_df['13/12he'].mean() / modified_df['13/12new'])**(correction_factor*2))
            modified_df['14/13corr'] = modified_df['14/13he'] * ((modified_df['13/12new']/modified_df['13/12he'].mean())**correction_factor)

        
        modified_groups[key] = modified_df

    # RECAKLCULATE MEAN OXII 13/12!!!!
    
    return modified_groups


def generate_figure(groups, correction_factor):
    """Generate the figure with corrected data."""
    fig = go.Figure()
    
    # Process and plot OXII data
    oxii_13_12_corr_columns = {}
    for item, df in groups.items():

        if not isinstance(df, pd.DataFrame):
            continue

        if df["Sample Name"].iloc[0].lower().startswith("oxii"):
            fig.add_trace(
                go.Scatter(
                    x=df["Meas"],
                    y=df["13/12 corr"],
                    mode="lines+markers",
                    name=f"{df['Item'].iloc[0]}.{df['Sample Name'].iloc[0]}",
                )
            )
            new_column_name = df["Sample Name"].iloc[0]
            reindexed_series = df['13/12 corr'].reset_index(drop=True)
            reindexed_series.index = reindexed_series.index + 1
            oxii_13_12_corr_columns[new_column_name] = reindexed_series
    
    # Create DataFrame and calculate trend
    oxii_df = pd.concat(oxii_13_12_corr_columns, axis=1)
    oxii_df.columns = oxii_13_12_corr_columns.keys()
    df_for_trend = oxii_df.T
    df_for_trend.columns = range(1, len(df_for_trend.columns) + 1)
    
    # Calculate means and trend line
    meas_means = [df_for_trend[column].mean() for column in df_for_trend.columns]
    trendline_x = list(range(1, len(meas_means) + 1))
    trendline_slope, trendline_intercept = np.polyfit(trendline_x, meas_means, 1)
    trendline_y = [trendline_slope * x + trendline_intercept for x in trendline_x]
    
    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=trendline_x,
            y=trendline_y,
            mode="markers+lines",
            name=f"Mean Trend (corr: {correction_factor})",
            marker=dict(color="black", size=5),
        )
    )
    
    # Add title showing the correction factor
    fig.update_layout(
        # title=f"13/12 Analysis with Correction Factor: {correction_factor}",
        xaxis_title="Measurement",
        yaxis_title="13/12 corr",
        # legend_title="Samples",
        legend=dict(
            orientation="h",            # horizontal orientation
            yanchor="bottom",           # anchor point
            y=1.02,                     # position above the chart (1.0 is top of chart)
            xanchor="center",           # anchor point 
            x=0.5,                      # centered horizontally
            bgcolor="rgba(255,255,255,0.8)",  
            bordercolor="Black",        
            borderwidth=1               
        )
    )
    
    return fig






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


def generate_tables(groups):
    """Generate tables with corrected data."""
    hidden_columns = ["13/12new", "E", "Run Completion Time", "Grp", "Sample Name 2", 'bias', 'stripPR', 'FacTR', 'Item', 'Sample Name']
    tables = [
        html.Div(
            [
                html.H5(f"{df['Item'].iloc[0]}.{df['Sample Name'].iloc[0]}:"),
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
                        )
                        for col in df.columns
                    ],
                    column_selectable=None,
                    editable=False,
                    hidden_columns=hidden_columns,
                    style_table={"overflowX": "auto"},
                ),
            ],
            style={"margin-bottom": "20px"},
        )
        for key, df in groups.items() if key != 'mean_oxii_13_12' and isinstance(df, pd.DataFrame)
    ]
    return tables

tables = generate_tables(groups)
fig = generate_figure(groups, 1)

# Updated app layout
app.layout = html.Div(
    [
        html.H1("Better Lithuanian Evaluation Tool, For RC Data", className="app-header"),
        
        # Main content container: tables and graph side by side
        html.Div(
            children=[
                # Left side: Tables
                html.Div(
                    id='tables-container',
                    children=[html.Div([table], className="data-table") for table in tables],
                    className="tables-section"
                ),
                
                # Right side: Graph and controls
                html.Div(
                    children=[
                        # Graph
                        html.Div(
                            id='graph-container',
                            children=[dcc.Graph(
                                id='main-graph', 
                                figure=fig,
                                style={"height": "100%"}
                            )],
                            className="graph-container"
                        ),
                        
                        # Slider controls under the graph
                        html.Div(
                            children=[
                                html.Label("13/12 Correction Factor (‰):"),
                                dcc.Slider(
                                    id='correction-slider',
                                    min=0,
                                    max=2,
                                    step=0.01,
                                    value=1,
                                    marks={i: f"{i}" for i in range(0, 2, 1)},
                                    tooltip={
                                        "always_visible": True,
                                        "style": {"color": "LightSteelBlue", "fontSize": "20px"},
                                        },
                                ),
                            ],
                            className="slider-container"
                        ),
                    ],
                    className="graph-section"
                ),
            ],
            className="content-container"
        ),
        
        # Add statistical summary section at the bottom
        html.Div(
            id="stats-container",
            className="stats-container"
        )
    ],
    className="app-container"
)

@app.callback(
    [Output('main-graph', 'figure'),
     Output('tables-container', 'children')],
    Input('correction-slider', 'value')
)
def update_data_with_correction(correction_factor):
    start_time = time.time()

    # Apply correction factor (slider value) to data
    modified_groups = apply_correction_to_groups(original_groups, correction_factor)
    
    # Regenerate plot and tables with modified data
    new_fig = generate_figure(modified_groups, correction_factor)
    new_tables = generate_tables(modified_groups)
    
    # Wrap each table in a div with className="data-table"
    table_components = [html.Div([table], className="data-table") for table in new_tables]
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time: {total_time}")

    return new_fig, table_components


if __name__ == "__main__":
    app.run(debug=True, port=8001)
