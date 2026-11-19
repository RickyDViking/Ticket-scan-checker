import datetime

import pandas as pd
import streamlit as st

st.title("Tickets per dag")

# Export uploaden
file = st.file_uploader("Upload de export (AttendanceReportFilter_….xlsx)", type="xlsx")

if file is None:
    st.stop()

df = pd.read_excel(file)
df["Ticket"] = df["Ticket"].astype(str).str.strip()

# Only scanned
df = df[df["Scanned"] == "Gescand"].copy()

# Date column
df["Date"] = pd.to_datetime(df["Scan Date"]).dt.date

# Dag kiezen (standaard vandaag)
dag = st.date_input("Dag", value=datetime.date.today(), format="DD-MM-YYYY")

df = df[df["Date"] == dag]

if df.empty:
    st.warning(f"Geen gescande tickets op {dag:%d-%m-%Y}.")
    st.stop()

# Discounted tickets
df["Discounted"] = (
    (df["Final Price"] > 0) &
    (df["Final Price"] < df["Original Price"])
)

# Indeling in categorieën
gewoon = df["Ticket"].isin(["Volwassenen", "Kinderen vanaf 3 jaar"])
tripper = df["Ticket"] == "Tripper ticket"

# Vaste kolommen, altijd in deze volgorde
aantallen = {
    "Tripper tickets": int(tripper.sum()),
    "Gewone tickets": int((gewoon & ~df["Discounted"]).sum()),
    "Gewone tickets korting": int((gewoon & df["Discounted"]).sum()),
}

# Daarna: elke andere ticketsoort die die dag gescand is
overig = df[~gewoon & ~tripper]["Ticket"].value_counts()
for ticket, aantal in overig.items():
    aantallen[ticket] = int(aantal)

report = pd.DataFrame([aantallen], index=[dag.strftime("%d-%m-%Y")])
report.index.name = "Datum"

st.dataframe(report)
