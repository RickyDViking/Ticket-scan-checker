import pandas as pd
import streamlit as st

st.title("Tickets per dag")

# Export uploaden (in plaats van een vast pad op je eigen pc)
file = st.file_uploader("Upload de export (AttendanceReportFilter_….xlsx)", type="xlsx")

if file is None:
    st.stop()

df = pd.read_excel(file)

# Only scanned
df = df[df["Scanned"] == "Gescand"].copy()

# Date column
df["Date"] = pd.to_datetime(df["Scan Date"]).dt.date

# Discounted tickets
df["Discounted"] = (
    (df["Final Price"] > 0) &
    (df["Final Price"] < df["Original Price"])
)

# Combine Adults + Children
df["Category"] = df["Ticket"]

df.loc[
    df["Ticket"].isin(
        ["Volwassenen", "Kinderen vanaf 3 jaar"]
    ),
    "Category"
] = "Gewone tickets"

# User filter
user_input = st.text_input(
    "Voer maand of datum in (YYYY-MM of YYYY-MM-DD): "
).strip()

date_str = pd.to_datetime(df["Date"]).astype(str)

if len(user_input) == 7:
    df = df[date_str.str.startswith(user_input)]

elif len(user_input) == 10:
    df = df[date_str == user_input]

# Regular tickets FULL PRICE
gewone_full = (
    df[
        (df["Category"] == "Gewone tickets") &
        (~df["Discounted"])
    ]
    .groupby("Date")
    .size()
)

# Regular tickets DISCOUNTED
gewone_discount = (
    df[
        (df["Category"] == "Gewone tickets") &
        (df["Discounted"])
    ]
    .groupby("Date")
    .size()
)

# Other tickets
other = (
    df[
        df["Category"] != "Gewone tickets"
    ]
    .groupby(["Date", "Category"])
    .size()
    .unstack(fill_value=0)
)

report = pd.concat(
    [
        gewone_full.rename("Gewone tickets"),
        gewone_discount.rename("Gewone tickets korting"),
        other
    ],
    axis=1
).fillna(0).astype(int)

st.dataframe(report)
