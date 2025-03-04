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
original_groups = groups.copy()

def apply_correction_to_groups(original_groups, correction_factor):
    """Apply correction factor to all relevant isotope ratio columns."""
    modified_groups = {}
    
    for key, df in original_groups.items():
        # Create a deep copy to avoid modifying the original
        modified_df = df.copy()
        
        # Apply correction factor to 13/12 corr
        if '13/12 corr' in modified_df.columns:
            # Correction can be additive or multiplicative depending on your needs
            # Additive:
            modified_df['13/12 corr'] = modified_df['13/12 corr'] + (correction_factor * 0.001)  # Adjust scale factor as needed
            
            # If 14/12corr depends on 13/12 corr, recalculate it
            if '14/12corr' in modified_df.columns:
                # Example recalculation (adjust formula as per your specific calculation)
                modified_df['14/12corr'] = recalculate_14_12(modified_df['14/12corr'], 
                                                            df['13/12 corr'], 
                                                            modified_df['13/12 corr'])
            
            # If 14/13corr depends on 13/12 corr and 14/12corr, recalculate it
            if '14/13corr' in modified_df.columns and '14/12corr' in modified_df.columns:
                modified_df['14/13corr'] = modified_df['14/12corr'] / modified_df['13/12 corr']
        
        modified_groups[key] = modified_df
    
    return modified_groups


def generate_figure(groups, correction_factor):
    """Generate the figure with corrected data."""
    fig = go.Figure()
    
    # Process and plot OXII data
    oxii_13_12_corr_columns = {}
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
        title=f"13/12 Analysis with Correction Factor: {correction_factor}",
        xaxis_title="Measurement",
        yaxis_title="13/12 corr",
        legend_title="Samples"
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
    hidden_columns = ["13/12new", "E", "Run Completion Time", "Grp", "Sample Name 2", 'bias', 'stripPR', 'FacTR']

    tables = [
        html.Div(
            [
                html.P(f"{df['Sample Name'].iloc[0]}"),
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
        for df in groups.values()
    ]
    return tables

tables = generate_tables(groups)
fig = generate_figure(groups, 0)

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
                                    min=-10,
                                    max=10,
                                    step=0.5,
                                    value=0,
                                    marks={i: f"{i}" for i in range(-10, 11, 2)},
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

if __name__ == "__main__":
    app.run(debug=True, port=8001)
    print(groups)
