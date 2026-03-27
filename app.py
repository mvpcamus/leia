import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- UI Style Settings ---
# Center-align text inside tables using CSS
st.markdown(
  """
  <style>
  div[data-testid="stTable"] {text-align: center;}
  div[data-testid="stTable"] th {text-align: center !important;}
  div[data-testid="stTable"] td {text-align: center !important;}
  </style>
  """,
  unsafe_allow_html=True
)

# --- Database (CSV) Initialization ---
FILE_NAME = "weight_data.csv"

# Create a new CSV file with headers if it doesn't exist
if not os.path.exists(FILE_NAME):
  df = pd.DataFrame(columns=["Date", "Weight(kg)"])
  df.to_csv(FILE_NAME, index=False)

# --- App Main Title ---
st.title("Leia's Diary")

# --- Data Input Section ---
st.subheader("Add New Records")
col1, col2 = st.columns(2) # Split layout into 2 columns

with col1:
  # Date input (Defaults to current date)
  date = st.date_input("Date", datetime.now())
with col2:
  # Weight input (Range: 0-20kg, Step: 0.1kg)
  weight = st.number_input("Weight", min_value=0.0, max_value=20.0, step=0.1, format="%.1f")

# Logic for 'Save Data' button
if st.button("Save Data"):
    # Convert input into a DataFrame row
    new_data = pd.DataFrame({"Date": [str(date)], "Weight (kg)": [weight]})
    # Append data to CSV (mode='a') without overwriting existing rows
    new_data.to_csv(FILE_NAME, mode='a', header=False, index=False)
    st.success(f"{date} data saved.")
    st.balloons() # Visual celebration effect

st.divider() # Horizontal line separator

# --- Visualization & Data Management Section ---
st.subheader("Weight Graph")

# Load the latest data from CSV
df = pd.read_csv(FILE_NAME)

if not df.empty:
    # Pre-processing: Convert strings to date objects and sort
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values(by="Date")

    # Create an interactive line chart using Plotly
    # line_shape='spline' creates smooth curves between data points
    fig = px.line(df, x="Date", y="Weight (kg)",
                title="Weight Change History",
                markers=True,
                render_mode='svg',
                line_shape='spline')

    # Force X-axis to display dates in YYYY-MM-DD format
    fig.update_xaxes(tickformat="%Y-%m-%d")

    # Render the chart in the web app
    st.plotly_chart(fig, width='stretch')

    # Data Editor Section (Inside an expandable container)
    with st.expander("See and Edit Records"):
        st.write("Tip: Select a row and press [Delete] to remove, or click a cell to edit.")

        # st.data_editor allows real-time editing and row deletion (num_rows='dynamic')
        edited_df = st.data_editor(
            df,
            width='stretch',
            num_rows='dynamic',
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Weight (kg)": st.column_config.NumberColumn("Weight (kg)", format="%.1f"),
            },
            hide_index=True # Hide the default numeric index column
        )

        # Button to commit changes back to the CSV file
        if st.button("Save Changes"):
            # Overwrite the CSV with the modified DataFrame
            edited_df.to_csv(FILE_NAME, index=False)
            st.success("Successfully Updated")
            st.rerun() # Refresh the app to update the graph and table immediately

else:
    # Message shown when the CSV is empty
    st.info("No data recorded yet. Please add your first entry above.")