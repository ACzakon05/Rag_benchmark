"""RAG Benchmark & Playground — aplikacja Streamlit (strona startowa).

Streamlit automatycznie wykrywa podstrony z katalogu `pages/`:
  1_Konfigurator.py  — wgrywanie danych + wybor konfiguracji (US-1, US-2)  [Osoba 2]
  2_Dashboard.py     — tabela porownawcza + inspekcja pytania (US-3, US-4) [Osoba 2 / 6]
  3_Playground.py    — interaktywny czat wybranej konfiguracji (US-5)       [Osoba 6]

Szkielet — bez logiki UI. Frontend moze byc budowany rownolegle na
zamockowanych danych (patrz docs/api.md).
"""

import streamlit as st

st.set_page_config(page_title="RAG Benchmark & Playground", layout="wide")

st.title("RAG Benchmark & Playground")
st.info("Szkielet projektu. Wybierz zakladke z menu bocznego. TODO: tresc stron.")
