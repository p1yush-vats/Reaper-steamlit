import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from transformers import TapasTokenizer, TapasForQuestionAnswering, pipeline
from streamlit_chat import message
import tempfile

# Streamlit Page Configuration
st.set_page_config(
    page_title="Client Data Survey System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Styling for a clean UI
st.markdown("""
    <style>
    body {
        background-color: #f5f7fa;
    }
    .css-1d391kg {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #007acc;
        color: white;
        border: None;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #005f99;
    }
    .css-1v3fvcr {
        font-size: 18px;
        font-weight: bold;
        color: #444;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Function to load the TAPAS model
@st.cache_resource
def load_tapas_model():
    model_path = "./models"  # Location of saved model
    tokenizer = TapasTokenizer.from_pretrained(model_path)
    model = TapasForQuestionAnswering.from_pretrained(model_path)
    pipe = pipeline("table-question-answering", model=model, tokenizer=tokenizer)
    return pipe

# Initialize model pipeline
pipe = load_tapas_model()

# Extract the answer from the model pipeline
def get_answer(table, query):
    return pipe(table=table, query=query)

# Convert answer based on its type
def convert_answer(answer):
    if answer['aggregator'] == 'SUM':
        return sum(float(v.replace(',', '')) for v in answer['cells'])
    if answer['aggregator'] == 'AVERAGE':
        values = [float(v.replace(',', '')) for v in answer['cells']]
        return sum(values) / len(values)
    if answer['aggregator'] == 'COUNT':
        return len(answer['cells'])
    return answer['answer']

# Get converted answer for a query and table
def get_converted_answer(table, query):
    return convert_answer(get_answer(table, query))

# Initialize session state variables
if 'uploaded' not in st.session_state:
    st.session_state.uploaded = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'dataframe' not in st.session_state:
    st.session_state.dataframe = None

# Main Title of the App
st.title("📊 Reaper AI Chatbot")

# Sidebar for navigation
with st.sidebar:
    st.header("📍 Navigation")
    menu = st.radio("Choose Option", ["Upload Data", "Chat with Data", "Analyze Data"])
    st.markdown("---")
    st.write("👨‍💻 Built with love using Streamlit + Transformers.")

# Upload Data Tab
if menu == "Upload Data":
    st.subheader("📤 Upload your CSV File")
    uploaded_file = st.file_uploader("Choose your CSV file", type="csv")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            dataframe = pd.read_csv(temp_file_path)
            st.session_state.dataframe = dataframe
            st.session_state.uploaded = True
            st.session_state.chat_history = []
            st.success("✅ Data uploaded successfully!")
            st.dataframe(dataframe.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")
            st.session_state.uploaded = False

# Chat with Data Tab
elif menu == "Chat with Data":
    if st.session_state.uploaded and st.session_state.dataframe is not None:
        dataframe = st.session_state.dataframe.astype(str)

        st.subheader("🤖 Ask a question about your data")

        # Structural preview of the data
        with st.expander("📌 Preview Your Data (First 5 Rows)"):
            st.dataframe(dataframe.head(), use_container_width=True)

        # Displaying previous chat history
        for idx, entry in enumerate(st.session_state.chat_history):
            if entry['role'] == 'user':
                message(entry['content'], is_user=True, key=f'{idx}_user', avatar_style="personas")
            else:
                message(entry['content'], key=f'{idx}_bot', avatar_style="bottts")

        # Form for asking questions
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your question...", key="input")
            submit_button = st.form_submit_button(label="Ask")

        if submit_button and user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})

            try:
                answer = get_converted_answer(dataframe, user_input)
                response = f"Answer: **{answer}**"
            except Exception as e:
                response = f"❌ An error occurred: {e}"

            st.session_state.chat_history.append({'role': 'bot', 'content': response})
            st.rerun()
    else:
        st.warning("⚠️ Please upload a CSV file first from the Upload tab.")

# Analyze Data Tab
elif menu == "Analyze Data":
    if st.session_state.uploaded and st.session_state.dataframe is not None:
        dataframe = st.session_state.dataframe

        st.subheader("📊 Visualize Your Data")

        with st.form("plot_form"):
            cols = dataframe.columns.tolist()
            x_col = st.selectbox("X-axis", cols)
            y_col = st.selectbox("Y-axis", cols)
            chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Pie Chart"])
            submit_btn = st.form_submit_button("Generate Chart")

        if submit_btn:
            try:
                fig, ax = plt.subplots()

                # Preparing data for the chart
                if pd.api.types.is_numeric_dtype(dataframe[y_col]):
                    grouped = dataframe.groupby(x_col)[y_col].sum()
                else:
                    grouped = dataframe[x_col].value_counts()

                # Plotting chart based on selection
                if chart_type == "Bar Chart":
                    grouped.plot(kind="bar", ax=ax)
                elif chart_type == "Line Chart":
                    grouped.plot(kind="line", ax=ax)
                elif chart_type == "Pie Chart":
                    grouped.plot(kind="pie", ax=ax, autopct="%1.1f%%")

                st.pyplot(fig)
            except Exception as e:
                st.error(f"Error creating chart: {e}")
    else:
        st.warning("⚠️ Please upload a CSV file first.")
