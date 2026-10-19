import streamlit as st
import json
from pathlib import Path

st.title("📚 AI Study Buddy")
st.write("Your personal study assistant!")

FILE = Path("notes.json")

def load_notes():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return []

notes = load_notes()

st.subheader("📝 Write Your Notes")
title = st.text_input("Note title")
content = st.text_area("Enter your study notes")

if st.button("Save Notes"):
    if title.strip() and content.strip():
        notes.append({"title": title, "content": content})
        FILE.write_text(json.dumps(notes, indent=2))
        st.success("Note saved!")
    else:
        st.warning("Enter both a title and notes.")

st.subheader("📖 Your Notes")
for note in load_notes():
    st.markdown(f"### {note['title']}")
    st.write(note["content"])
