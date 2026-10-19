
import json
from pathlib import Path
import random
import streamlit as st

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

FILE = Path("notes.json")


def load_notes():
    try:
        if FILE.exists():
            data = json.loads(FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_notes(notes):
    FILE.write_text(
        json.dumps(notes, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


if "notes" not in st.session_state:
    st.session_state.notes = load_notes()

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

notes = st.session_state.notes

st.title("📚 AI Study Buddy")
st.caption("Your personal workspace for smarter studying.")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard", "📝 My Notes", "🃏 Flashcards", "🧠 Quiz"]
)

st.sidebar.divider()
st.sidebar.metric("Total notes", len(notes))
st.sidebar.caption("Built with Python + Streamlit")


def persist():
    save_notes(st.session_state.notes)


if page == "🏠 Dashboard":
    st.subheader("Welcome back, learner! 👋")

    a, b, c = st.columns(3)
    a.metric("Total notes", len(notes))
    b.metric("Words saved", sum(
        len(n.get("content", "").split()) for n in notes
    ))
    c.metric("Study tools", 3)

    st.divider()
    st.subheader("Quick start")

    st.write("📝 **My Notes:** Create, search, edit and delete notes.")
    st.write("🃏 **Flashcards:** Revise your saved material.")
    st.write("🧠 **Quiz:** Test yourself using your notes.")

    if notes:
        st.subheader("Recently added")
        for note in notes[-3:][::-1]:
            with st.container(border=True):
                st.markdown(f"**{note['title']}**")
                st.write(note["content"][:250])


elif page == "📝 My Notes":
    st.subheader("📝 Your study notes")

    query = st.text_input("🔍 Search notes by title or content")

    edit_note = next(
        (n for n in notes if n.get("id") == st.session_state.edit_id),
        None
    )

    with st.form("note_form", clear_on_submit=True):
        title = st.text_input(
            "Note title",
            value=edit_note["title"] if edit_note else ""
        )
        content = st.text_area(
            "Your notes",
            value=edit_note["content"] if edit_note else "",
            height=180
        )
        save = st.form_submit_button(
            "💾 Update note" if edit_note else "💾 Save note",
            use_container_width=True
        )

    if save:
        if not title.strip() or not content.strip():
            st.warning("Enter both a title and some notes.")
        elif edit_note:
            edit_note["title"] = title.strip()
            edit_note["content"] = content.strip()
            st.session_state.edit_id = None
            persist()
            st.success("Note updated!")
            st.rerun()
        else:
            notes.append({
                "id": str(random.getrandbits(64)),
                "title": title.strip(),
                "content": content.strip()
            })
            persist()
            st.success("Note saved!")
            st.rerun()

    if edit_note and st.button("Cancel editing"):
        st.session_state.edit_id = None
        st.rerun()

    st.divider()

    filtered = [
        n for n in notes
        if query.lower() in (
            n.get("title", "") + " " + n.get("content", "")
        ).lower()
    ]

    if not filtered:
        st.info("No matching notes yet. Create one above!")
    else:
        for note in filtered:
            with st.container(border=True):
                st.markdown(f"### {note['title']}")
                st.write(note["content"])

                x, y = st.columns(2)

                if x.button("✏️ Edit", key="edit_" + note["id"]):
                    st.session_state.edit_id = note["id"]
                    st.rerun()

                if y.button("🗑️ Delete", key="del_" + note["id"]):
                    st.session_state.notes = [
                        n for n in notes if n["id"] != note["id"]
                    ]
                    if st.session_state.edit_id == note["id"]:
                        st.session_state.edit_id = None
                    persist()
                    st.rerun()


elif page == "🃏 Flashcards":
    st.subheader("🃏 Flashcard revision")

    if not notes:
        st.info("Create some notes first!")
    else:
        selected = st.selectbox(
            "Choose study material",
            notes,
            format_func=lambda n: n["title"]
        )

        sentences = [
            s.strip()
            for s in selected["content"].replace("\n", ".").split(".")
            if s.strip()
        ]

        if sentences:
            if "card_index" not in st.session_state:
                st.session_state.card_index = 0

            idx = st.session_state.card_index % len(sentences)

            st.caption(
                f"Card {idx + 1} of {len(sentences)}"
            )

            with st.container(border=True):
                st.markdown("### 📖 Study point")
                st.write(sentences[idx])

            left, right = st.columns(2)

            if left.button("⬅️ Previous", use_container_width=True):
                st.session_state.card_index = (
                    idx - 1
                ) % len(sentences)
                st.rerun()

            if right.button("Next ➡️", use_container_width=True):
                st.session_state.card_index = (
                    idx + 1
                ) % len(sentences)
                st.rerun()

            st.caption(
                "These cards use sentences from your notes."
            )
        else:
            st.info("Add more text to your selected note.")


elif page == "🧠 Quiz":
    st.subheader("🧠 Test your knowledge")

    if not notes:
        st.info("Create study notes before starting a quiz.")
    else:
        selected = st.selectbox(
            "Choose a topic",
            notes,
            format_func=lambda n: n["title"],
            key="quiz_topic"
        )

        sentences = [
            s.strip()
            for s in selected["content"].replace("\n", ".").split(".")
            if len(s.strip().split()) >= 3
        ]

        if len(sentences) < 2:
            st.info(
                "Add at least two sentences of study material "
                "to create a quiz."
            )
        else:
            if st.button("🔄 Generate new quiz"):
                st.session_state.quiz_questions = random.sample(
                    sentences, min(5, len(sentences))
                )
                st.session_state.quiz_answers = {}

            if (
                "quiz_questions" not in st.session_state
                or st.session_state.get("quiz_topic_id")
                != selected["id"]
            ):
                st.session_state.quiz_questions = random.sample(
                    sentences, min(5, len(sentences))
                )
                st.session_state.quiz_answers = {}
                st.session_state.quiz_topic_id = selected["id"]

            questions = st.session_state.quiz_questions
            score = 0

            for i, answer in enumerate(questions):
                options = list(dict.fromkeys(
                    [answer] + random.sample(
                        [s for s in sentences if s != answer],
                        min(3, len(sentences) - 1)
                    )
                ))
                random.shuffle(options)

                st.markdown(f"**Question {i + 1}: Which statement appeared in your notes?**")

                choice = st.radio(
                    f"Select an answer for question {i + 1}",
                    options,
                    key=f"q_{selected['id']}_{i}",
                    label_visibility="collapsed"
                )

                if st.button(
                    "Check answer",
                    key=f"check_{selected['id']}_{i}"
                ):
                    st.session_state.quiz_answers[str(i)] = (
                        choice == answer
                    )

                if str(i) in st.session_state.quiz_answers:
                    correct = st.session_state.quiz_answers[str(i)]
                    if correct:
                        st.success("Correct! 🎉")
                    else:
                        st.info(f"Review this statement: {answer}")

                    if correct:
                        score += 1

                st.divider()

            st.caption(
                "This quiz tests recognition of your notes. "
                "It does not yet use an AI model."
            )

st.sidebar.divider()
st.sidebar.caption("Keep learning. Keep building. 🚀")
