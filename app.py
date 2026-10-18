import streamlit as st

st.title("📚 AI Study Buddy")

st.write("Welcome! Your personal study assistant.")

st.subheader("📝 Write Your Notes")

notes = st.text_area("Enter your study notes here:")

if st.button("Save Notes"):
    if notes:
        st.success("Notes saved successfully!")
    else:
        st.warning("Please enter some notes first.")
