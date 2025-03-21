import streamlit as st
import base64
import pymysql
import bcrypt
import google.generativeai as genai
import pandas as pd
import speech_recognition as sr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_community.utilities.sql_database import SQLDatabase

# 🔹 MySQL Database Credentials
db_user = "root"
db_password = "root"
db_host = "localhost"
db_name = "hitesh"

# 🔹 Connect to MySQL using LangChain SQLDatabase
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

# 🔹 Initialize Gemini Model
GOOGLE_API_KEY = "AIzaSyBwMo91yPTenaS3o99FN6kjeLeVvEBfZ_4"
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001", google_api_key=GOOGLE_API_KEY)


# 🎤 Function to Capture Voice Input
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Speak now...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand. Try again."
        except sr.RequestError:
            return "API unavailable. Check your connection."


# Function to Verify User Login
def verify_user(username, password):
    try:
        connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()
        if user_data:
            return bcrypt.checkpw(password.encode('utf-8'), user_data[0].encode('utf-8'))
        return False
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False


# Function to Add Background Image
def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)


# Add Background Image
add_bg_from_local("xyz.jpg")

# Streamlit Login UI
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login to Access AI-Powered SQL Generator")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.authenticated = True
            st.success("Login Successful!")
            st.rerun()
        else:
            st.error("Invalid Credentials. Try again.")
else:
    # Main App UI
    st.title("AI-Powered SQL Query Generator & Executor")
    st.subheader("Convert Natural Language to SQL and Execute It on MySQL Database")

    query_type = st.radio("Select Query Type:", ("Retrieve Data", "Insert Data"))

    # 🎤 Voice Input Section
    st.write("🎤 Speak your query or type below:")
    voice_query = ""
    if st.button("🎤 Use Voice Input"):
        voice_query = voice_input()

    # Display the recognized query in text area
    question = st.text_area("Enter your natural language query:", value=voice_query if voice_query else "")

    if st.button("Generate & Execute Query"):
        with st.spinner("Generating SQL Query..."):
            prompt = """You are an expert in converting English questions to SQL queries!

                        The SQL database has the name 'hitesh' and has the following table: emp with columns - NAME, SALARY, DEPARTMENT, etc.

                        For example:
                        - input :- How many employees are in the database?
                          output:-  SELECT COUNT(*) FROM emp;

                        - input:- List all employees in the IT department.
                          output:- SELECT * FROM emp WHERE DEPARTMENT = 'IT';

                        Your tasks:
                        1. Ensure the SQL queries do NOT include backticks (` `) around table or column names.
                        2. Do NOT include formatting like code block markers (```).
                        3. Avoid using unnecessary single quotes (' ') around table or column names, unless required for strings.
                        4. Ensure the SQL query adheres to MySQL syntax.
                        5. Only return executable queries without additional text.
                        
                        When a user provides an insertion request, generate a valid **INSERT INTO** SQL query.  
- If `empid` is not mentioned, assume it is **auto-generated** by the database.  
- If `deptid` is missing, assume **NULL** (not required).  
- Ensure that all required fields (`ename`, `salary`) are included.  
- Do **NOT** use backticks (`).  

Example Inputs & Expected Outputs:  

1️⃣ **Input:** "Add a new employee John Doe with a salary of 50,000."  
   **Expected SQL Output:**  
   ```sql
   INSERT INTO emp (ename, salary) VALUES ('John Doe', 50000);
                        """
            full_input = f"{prompt}\n\nQuestion: {question}"
            generate_query = create_sql_query_chain(llm, db)
            sql_query = generate_query.invoke({"question": full_input}).replace("SQLQuery:", "").strip()
            st.code(sql_query, language="sql")

        # Function to Execute Query
        def execute_query(query):
            try:
                connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
                cursor = connection.cursor()
                cursor.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    json_result = [dict(zip(columns, row)) for row in result] if result else []
                else:
                    connection.commit()
                    json_result = "Query executed successfully!"
                cursor.close()
                connection.close()
                return json_result
            except Exception as e:
                return {"error": str(e)}

        # Execute and Display Results
        query_results = execute_query(sql_query)
        if isinstance(query_results, str):
            st.success(query_results)
        elif "error" in query_results:
            st.error(f"Error executing query: {query_results['error']}")
        else:
            df = pd.DataFrame(query_results)
            st.write("### 📊 Query Results")
            st.dataframe(df)

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()
