import io

import pandas as pd
import streamlit as st

st.set_page_config(page_title="KidZcity tickets per dag", layout="wide")
st.title("Tickets per dag")

GEWONE = ["Volwassenen", "Kinderen vanaf 3 jaar"]


@st.cache_data
def laad_export(data: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(data))
    df["Ticket"] = df["Ticket"].astype(str).str.strip()
    df["Scanned"] = df["Scanned"].astype(str).str.strip()
    return df


def maak_rapport(df: pd.DataFrame) -> pd.DataFrame:
    gewone_full = (
        df[(df["Category"] == "Gewone tickets") & (~df["Discounted"])]
        .groupby("Date").size()
    )
    gewone_discount = (
        df[(df["Category"] == "Gewone tickets") & (df["Discounted"])]
        .groupby("Date").size()
    )
    other = (
        df[df["Category"] != "Gewone tickets"]
        .groupby(["Date", "Category"]).size()
        .unstack(fill_value=0)
    )
    report = pd.concat(
        [
            gewone_full.rename("Gewone tickets"),
            gewone_discount.rename("Gewone tickets korting"),
            other,
        ],
        axis=1,
    ).fillna(0).astype(int).sort_index()
    report.index.name = "Datum"
    return report


bestand = st.file_uploader(
    "Upload de export (AttendanceReportFilter_….xlsx)", type="xlsx"
)

if bestand is None:
    st.info("Upload een export om te beginnen.")
    st.stop()

alles = laad_export(bestand.getvalue())

# Controle: scanstatus per Tripper-ticket
tripper = alles[alles["Ticket"].str.contains("tripper", case=False, na=False)]
with st.expander("Controle Tripper-tickets (gescand / niet gescand)"):
    if len(tripper):
        st.dataframe(
            tripper.groupby(["Ticket", "Scanned"]).size().unstack(fill_value=0)
        )
    else:
        st.write("Geen Tripper-tickets in dit bestand.")

# Alleen gescande tickets
df = alles[alles["Scanned"] == "Gescand"].copy()
df["Date"] = pd.to_datetime(df["Scan Date"]).dt.date

df["Discounted"] = (df["Final Price"] > 0) & (df["Final Price"] < df["Original Price"])

df["Category"] = df["Ticket"]
df.loc[df["Ticket"].isin(GEWONE), "Category"] = "Gewone tickets"

if df.empty:
    st.warning("Geen gescande tickets in dit bestand.")
    st.stop()

# Periode kiezen
keuze = st.radio("Periode", ["Hele bestand", "Maand", "Dag"], horizontal=True)

datums = pd.to_datetime(df["Date"])

if keuze == "Maand":
    maanden = sorted(datums.dt.strftime("%Y-%m").unique(), reverse=True)
    maand = st.selectbox("Maand", maanden)
    df = df[datums.dt.strftime("%Y-%m") == maand]
    label = maand
elif keuze == "Dag":
    dag = st.date_input(
        "Dag",
        value=df["Date"].max(),
        min_value=df["Date"].min(),
        max_value=df["Date"].max(),
        format="DD-MM-YYYY",
    )
    df = df[df["Date"] == dag]
    label = str(dag)
else:
    label = "alles"

if df.empty:
    st.warning("Geen gescande tickets in deze periode.")
    st.stop()

report = maak_rapport(df)

st.dataframe(report, width="stretch")

st.subheader("Totaal")
st.dataframe(report.sum().rename("Aantal").to_frame(), width="content")

# Download als Excel
buffer = io.BytesIO()
report.to_excel(buffer)
st.download_button(
    "Download als Excel",
    data=buffer.getvalue(),
    file_name=f"Rapport_{label}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
