
from nicegui import ui
import pandas as pd
from data import Data

# Sample DataFrame
data = Data()
data.fetch()
df = data.get_dataframe()

# Add a checkbox column (default False)
df["Checked"] = False

# Convert DataFrame to a dictionary
table_data = df.to_dict('records')

# Define AG Grid column structure
columns = [
    {"field": col, "headerName": col} for col in df.columns[:-1]  # Normal columns
] + [
    {"field": "Checked", "headerName": "Select", "checkboxSelection": True}  # Checkbox column
]

# Create the AG Grid table
grid = ui.aggrid({
    "columnDefs": columns,
    "rowData": table_data,
    "rowSelection": "multiple",  # Enables multiple row selection with checkboxes
    "domLayout": "autoHeight"
})

# Function to get selected rows
def get_selected():
    df = data.get_dataframe()
    print('blablabla')


# Add a button to print selected rows

ui.run(port=8080)






ui.run(port=8001)  # Runs a local web server