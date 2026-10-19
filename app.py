import json
import random
import re
import uuid

import streamlit as st

st.set_page_config(page_title="Study Buddy", page_icon="📚", layout="wide")

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
NOTE_FIELDS = ("title", "content")
CARD_FIELDS = ("question", "answer")


def clean_items(raw, fields):
    """Make any loaded data safe: every item gets text fields and a unique id.

    This is the real fix for the missing "id" error. Old items without an id
    (or with duplicate ids) are repaired once, here, when the data is loaded.
    Returns (items, changed) where changed means something was repaired.
    """
    if not isinstance(raw, list):
        return [], True
    items, seen, changed = [], set(), False
    for entry in raw:
        if not isinstance(entry, dict):
            changed = True
            continue
        item = {f: str(entry.get(f, "")).strip() for f in fields}
        if not all(item.values()):
            changed = True  # skip incomplete entries
            continue
        item_id = str(entry.get("id", "")).strip()
        if not item_id or item_id in seen:
            item_id = uuid.uuid4().hex
            changed = True
        seen.add(item_id)
        item["id"] = item_id
        items.append(item)
    return items, changed


def find_by_id(items, item_id):
    return next((i for i in items if i["id"] == item_id), None)


# ---------------------------------------------------------------------------
# Session state (loaded once per browser session)
# ---------------------------------------------------------------------------
DEMO_NOTES = [
    {
        "title": "Ohm's Law",
        "content": "Voltage equals current multiplied by resistance. Resistance is measured in ohms. Current is the flow of electric charge through a conductor. Power equals voltage multiplied by current.",
    },
    {
        "title": "Kirchhoff's Laws",
        "content": "Kirchhoff's current law says the total current entering a junction equals the total current leaving it. Kirchhoff's voltage law says the sum of voltages around a closed loop is zero. These laws are used for analysing complex circuits.",
    },
]
DEMO_CARDS = [
    {"question": "What is the unit of resistance?", "answer": "Ohm"},
    {"question": "What is the unit of current?", "answer": "Ampere"},
    {"question": "What does KVL stand for?", "answer": "Kirchhoff's Voltage Law"},
    {"question": "What is the formula for power?", "answer": "P = VI"},
]

# st.session_state is private to each visitor's browser session, so every
# visitor starts with their own copy of the demo data and cannot see or
# change anyone else's notes.
if "notes" not in st.session_state:
    st.session_state.notes = [dict(n, id=uuid.uuid4().hex) for n in DEMO_NOTES]
    st.session_state.cards = [dict(c, id=uuid.uuid4().hex) for c in DEMO_CARDS]

defaults = {
    "edit_note_id": None,
    "card_pos": 0,
    "card_revealed": False,
    "quiz": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

notes = st.session_state.notes
cards = st.session_state.cards

# ---------------------------------------------------------------------------
# Layout: title + sidebar
# ---------------------------------------------------------------------------
st.title("📚 Study Buddy")
st.caption("Your personal workspace for smarter studying.")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard", "📝 My Notes", "📚 Flashcards", "🧠 Quiz"],
)
st.sidebar.divider()
st.sidebar.metric("Total notes", len(notes))
st.sidebar.metric("Total flashcards", len(cards))
st.sidebar.caption("Built with Python + Streamlit")
st.sidebar.caption("🔒 Your data is private to this session")


# ---------------------------------------------------------------------------
# Quiz generators (plain Python, no AI model)
# ---------------------------------------------------------------------------
def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]


def build_note_quiz(note, how_many=5):
    """Fill-in-the-blank questions made from the sentences of one note."""
    sentences = split_sentences(note["content"])
    words = sorted({w.lower() for w in re.findall(r"[A-Za-z]{5,}", note["content"])})
    if not sentences or len(words) < 4:
        return []
    random.shuffle(sentences)
    questions = []
    for sentence in sentences:
        candidates = re.findall(r"[A-Za-z]{5,}", sentence)
        if not candidates:
            continue
        answer = random.choice(candidates)
        blanked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1)
        correct = answer.lower()
        options = [correct] + random.sample([w for w in words if w != correct], 3)
        random.shuffle(options)
        questions.append({"question": blanked, "options": options, "answer": correct})
        if len(questions) == how_many:
            break
    return questions


def build_card_quiz(card_list, how_many=5):
    """Multiple-choice questions: pick the right answer for each flashcard."""
    questions = []
    for card in random.sample(card_list, min(how_many, len(card_list))):
        others = list({c["answer"] for c in card_list if c["answer"] != card["answer"]})
        if not others:
            continue
        options = [card["answer"]] + random.sample(others, min(3, len(others)))
        random.shuffle(options)
        questions.append(
            {"question": card["question"], "options": options, "answer": card["answer"]}
        )
    return questions


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    st.subheader("Welcome back, learner! 👋")
    st.caption("🔒 Your notes and flashcards are private to you in this session.")

    a, b, c = st.columns(3)
    a.metric("Total notes", len(notes))
    b.metric("Total flashcards", len(cards))
    c.metric("Words saved", sum(len(n["content"].split()) for n in notes))

    st.divider()
    st.subheader("What you can do")
    st.write("📝 **My Notes:** Create, search, edit and delete notes.")
    st.write("📚 **Flashcards:** Make question/answer cards and reveal answers.")
    st.write("🧠 **Quiz:** Test yourself with quizzes built from your notes or cards.")

    if notes:
        st.subheader("Recently added notes")
        for note in notes[-3:][::-1]:
            with st.container(border=True):
                st.markdown(f"**{note['title']}**")
                st.write(note["content"][:250])

    st.divider()
    with st.expander("💾 Save & restore your data"):
        st.caption(
            "Your notes and flashcards are private and only live in this browser "
            "session. Refreshing or closing the tab clears them, so download a "
            "backup to keep them and restore it next time."
        )
        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇️ Download notes.json",
            json.dumps(notes, indent=2, ensure_ascii=False),
            file_name="notes.json",
            mime="application/json",
        )
        d2.download_button(
            "⬇️ Download flashcards.json",
            json.dumps(cards, indent=2, ensure_ascii=False),
            file_name="flashcards.json",
            mime="application/json",
        )

        st.markdown("**Restore from a backup** (this replaces your current data)")
        kind = st.radio("The file contains", ["Notes", "Flashcards"], horizontal=True)
        upload = st.file_uploader("Choose a .json backup", type="json")
        if upload is not None and st.button("Restore now"):
            try:
                raw = json.load(upload)
            except (json.JSONDecodeError, UnicodeDecodeError):
                st.error("That file is not valid JSON.")
            else:
                fields = NOTE_FIELDS if kind == "Notes" else CARD_FIELDS
                items, _ = clean_items(raw, fields)
                if kind == "Notes":
                    st.session_state.notes = items
                else:
                    st.session_state.cards = items
                st.session_state.quiz = None
                st.success(f"Restored {len(items)} item(s).")
                st.rerun()


# ---------------------------------------------------------------------------
# My Notes
# ---------------------------------------------------------------------------
elif page == "📝 My Notes":
    st.subheader("📝 Your study notes")

    query = st.text_input("🔍 Search notes by title or content").strip().lower()

    edit_note = find_by_id(notes, st.session_state.edit_note_id)
    if edit_note is None:
        st.session_state.edit_note_id = None
    form_key = edit_note["id"] if edit_note else "new"

    with st.form("note_form", clear_on_submit=True):
        title = st.text_input(
            "Note title",
            value=edit_note["title"] if edit_note else "",
            key=f"note_title_{form_key}",
        )
        content = st.text_area(
            "Your notes",
            value=edit_note["content"] if edit_note else "",
            height=180,
            key=f"note_content_{form_key}",
        )
        submitted = st.form_submit_button(
            "💾 Update note" if edit_note else "💾 Save note"
        )

    if submitted:
        if not title.strip() or not content.strip():
            st.warning("Enter both a title and some notes.")
        elif edit_note:
            edit_note["title"] = title.strip()
            edit_note["content"] = content.strip()
            st.session_state.edit_note_id = None
            st.rerun()
        else:
            notes.append(
                {
                    "id": uuid.uuid4().hex,
                    "title": title.strip(),
                    "content": content.strip(),
                }
            )
            st.rerun()

    if edit_note:
        st.info(f"Editing: {edit_note['title']}")
        if st.button("Cancel editing"):
            st.session_state.edit_note_id = None
            st.rerun()

    st.divider()

    filtered = [
        n for n in notes if query in (n["title"] + " " + n["content"]).lower()
    ]

    if not filtered:
        st.info("No matching notes yet. Create one above!")
    else:
        for note in filtered:
            with st.container(border=True):
                st.markdown(f"### {note['title']}")
                st.write(note["content"])

                col_edit, col_delete = st.columns(2)
                if col_edit.button("✏️ Edit", key=f"edit_{note['id']}"):
                    st.session_state.edit_note_id = note["id"]
                    st.rerun()
                if col_delete.button("🗑️ Delete", key=f"del_{note['id']}"):
                    st.session_state.notes = [
                        n for n in notes if n["id"] != note["id"]
                    ]
                    if st.session_state.edit_note_id == note["id"]:
                        st.session_state.edit_note_id = None
                    st.rerun()


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------
elif page == "📚 Flashcards":
    st.subheader("📚 Flashcards")
    study_tab, manage_tab = st.tabs(["Study", "Add / manage cards"])

    with manage_tab:
        with st.form("card_form", clear_on_submit=True):
            question = st.text_input("Question")
            answer = st.text_area("Answer", height=100)
            add_card = st.form_submit_button("➕ Add flashcard")

        if add_card:
            if not question.strip() or not answer.strip():
                st.warning("Enter both a question and an answer.")
            else:
                cards.append(
                    {
                        "id": uuid.uuid4().hex,
                        "question": question.strip(),
                        "answer": answer.strip(),
                    }
                )
                st.rerun()

        st.divider()
        if not cards:
            st.info("No flashcards yet. Add your first one above!")
        for card in cards:
            with st.container(border=True):
                st.markdown(f"**Q:** {card['question']}")
                st.write(f"**A:** {card['answer']}")
                if st.button("🗑️ Delete", key=f"delcard_{card['id']}"):
                    st.session_state.cards = [
                        c for c in cards if c["id"] != card["id"]
                    ]
                    st.session_state.card_revealed = False
                    st.rerun()

    with study_tab:
        if not cards:
            st.info("Add some flashcards in the 'Add / manage cards' tab first.")
        else:
            pos = st.session_state.card_pos % len(cards)
            card = cards[pos]
            st.caption(f"Card {pos + 1} of {len(cards)}")

            with st.container(border=True):
                st.markdown("### ❓ Question")
                st.write(card["question"])
                if st.session_state.card_revealed:
                    st.markdown("### ✅ Answer")
                    st.write(card["answer"])

            c1, c2, c3, c4 = st.columns(4)
            if c1.button("⬅️ Previous"):
                st.session_state.card_pos = (pos - 1) % len(cards)
                st.session_state.card_revealed = False
                st.rerun()
            if c2.button(
                "🙈 Hide answer" if st.session_state.card_revealed else "👀 Show answer"
            ):
                st.session_state.card_revealed = not st.session_state.card_revealed
                st.rerun()
            if c3.button("🔀 Random"):
                st.session_state.card_pos = random.randrange(len(cards))
                st.session_state.card_revealed = False
                st.rerun()
            if c4.button("Next ➡️"):
                st.session_state.card_pos = (pos + 1) % len(cards)
                st.session_state.card_revealed = False
                st.rerun()


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
elif page == "🧠 Quiz":
    st.subheader("🧠 Test your knowledge")

    source = st.radio(
        "Make a quiz from",
        ["📝 A note (fill in the blank)", "📚 My flashcards (pick the answer)"],
        horizontal=True,
    )

    selected_note = None
    if source.startswith("📝"):
        if not notes:
            st.info("Create a note first, then come back for a quiz.")
            st.stop()
        selected_note = st.selectbox(
            "Choose a note", notes, format_func=lambda n: n["title"]
        )
        source_key = "note:" + selected_note["id"]
    else:
        if len(cards) < 2:
            st.info("Add at least two flashcards to make a quiz.")
            st.stop()
        source_key = "cards"

    if st.button("🔄 Generate new quiz"):
        if selected_note:
            questions = build_note_quiz(selected_note)
        else:
            questions = build_card_quiz(cards)
        if not questions:
            st.warning(
                "Not enough material. Notes need a few full sentences "
                "(5+ words each) with some longer words."
            )
            st.session_state.quiz = None
        else:
            st.session_state.quiz = {
                "id": uuid.uuid4().hex,
                "source": source_key,
                "questions": questions,
                "choices": None,
            }

    quiz = st.session_state.quiz
    if quiz and quiz["source"] != source_key:
        quiz = None  # the chosen source changed; ask for a fresh quiz

    if not quiz:
        st.info("Press **Generate new quiz** to begin.")
    else:
        with st.form(f"quiz_form_{quiz['id']}"):
            picks = []
            for i, q in enumerate(quiz["questions"]):
                st.markdown(f"**Question {i + 1}:** {q['question']}")
                picks.append(
                    st.radio(
                        f"Answer for question {i + 1}",
                        q["options"],
                        index=None,
                        key=f"quiz_{quiz['id']}_{i}",
                        label_visibility="collapsed",
                    )
                )
                st.write("")
            finished = st.form_submit_button("✅ Submit answers")

        if finished:
            quiz["choices"] = picks

        if quiz["choices"] is not None:
            score = 0
            for q, pick in zip(quiz["questions"], quiz["choices"]):
                if pick == q["answer"]:
                    score += 1
            total = len(quiz["questions"])
            st.success(f"Your score: {score} / {total}")
            for i, (q, pick) in enumerate(zip(quiz["questions"], quiz["choices"])):
                if pick == q["answer"]:
                    st.write(f"✅ Question {i + 1}: correct")
                else:
                    st.write(f"❌ Question {i + 1}: the answer was **{q['answer']}**")

        st.caption(
            "This quiz is generated with simple Python rules from your own "
            "material. It does not use an AI model."
        )

st.sidebar.divider()
st.sidebar.caption("Keep learning. Keep building. 🚀")
