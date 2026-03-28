import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# --- Load API key from .env ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- System & API settings ---
st.set_page_config(page_title="Leia's Diary", page_icon="🐱", layout='wide')

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

# --- Initialize Gemini ---
if api_key:
  client = genai.Client(api_key=api_key)
else:
  st.error("Gemini API key not found. Please check you .env file.")
  st.stop()

# --- Database (CSV) Initialization ---
FILE_NAME = "weight_data.csv"

# Create a new CSV file with headers if it doesn't exist
if not os.path.exists(FILE_NAME):
  df = pd.DataFrame(columns=["Date", "Weight (kg)"])
  df.to_csv(FILE_NAME, index=False)

def calculate_age(birthday) -> str:
  today = datetime.now().date()
  years = today.year - birthday.year
  months = today.month - birthday.month
  if months < 0:
    years = years - 1
    months = months + 12
  if years < 0: # check wrong birthday input
    return "unknown"
  return f"{years} years and {months} months"

# --- Sidebar for Cat Profile ---
st.sidebar.title("🐾 Cat Profile")
cat_name = st.sidebar.text_input("Name", value="Leia")
breed = st.sidebar.selectbox("Breed", ["Domestic Short Hair", "Persian", "Maine Coon", "Siamese", "Ragdoll", "Bengal", "Sphynx"], 4)
gender = st.sidebar.radio("Gender", ["Male", "Female"], 1)
birthday = st.sidebar.date_input("Birthday", datetime(2022, 6, 19))
age_str = calculate_age(birthday)
st.sidebar.info(f"Age: {age_str}")

# get detailed AI diagnosis using Gemini
@st.cache_data(show_spinner="Consulting Gemini AI ...")
def get_ai_diagnosis(name, breed, gender, age_str, current_weight, history_df):
  history_summary = history_df.tail(5).to_csv(index=False)

  # Prompt Engineering for Gemini
  prompt = f"""
    You are a professional feline health consultant.
    Analyze the following cat's data:
    - Name: {name}, Breed: {breed}, Gender: {gender}, Age: {age_str}
    - Current Weight: {current_weight}kg
    - Recent Weight History: {history_summary}
    Provide a detailed health analysis and advice in a warm tone.
    """

  try:
    response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt
    )
    return response.text
  except Exception as e:
    return f"Error connecting to Gemini: {str(e)}"

# --- App Main Title ---
st.title(f"{cat_name}'s Diary")

# --- AI Consultant Section ---
st.subheader("🤖 AI Health Specialist (Gemini)")

df = pd.read_csv(FILE_NAME) # Load the lastest data from csv

if not df.empty:
  latest_data = df.sort_values(by="Date").iloc[-1]
  latest_date = latest_data["Date"]
  latest_weight = latest_data["Weight (kg)"]

  if st.button("Get AI Analysis"):
    diagnosis = get_ai_diagnosis(cat_name, breed, gender, age_str, latest_weight, df)
    st.session_state['ai_diagnosis'] = diagnosis

  if 'ai_diagnosis' in st.session_state:
    with st.chat_message("assistant", avatar="🐱"):
      st.markdown(f"***Analysis based on {cat_name}'s latest record:***")
      st.markdown(st.session_state['ai_diagnosis'])
else:
  with st.chat_message("assistant", avatar="🐱"):
    st.write("Add a weight record to get a health analysis from Gemini.")

st.divider() # Horizontal line separator

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
    if 'ai_diagnosis' in st.session_state:
      del st.session_state['ai_diagnosis']
    st.rerun()

st.divider() # Horizontal line separator

# --- Visualization & Data Management Section ---
st.subheader("Weight Graph")

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
            if 'ai_diagnosis' in st.session_state:
              del st.session_state['ai_diagnosis']
            st.rerun() # Refresh the app to update the graph and table immediately

else:
    # Message shown when the CSV is empty
    st.info("No data recorded yet. Please add your first entry above.")