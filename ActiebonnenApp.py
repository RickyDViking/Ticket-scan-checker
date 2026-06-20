import pandas as pd
import streamlit as st
import openpyxl

st.set_page_config(page_title='ActiebonnenApp',layout='wide')
st.header('Blue Excel Uploader')
#Input van datum met kalender
input_dag = st.date_input('Selecteer een dag',format="DD/MM/YYYY")


#Input van file via drag and drop
upload_file = st.file_uploader('Sleep hier het bestand')
if upload_file is not None:
    df = pd.read_excel(upload_file)

#Alleen wat er gescand is
    df = df[df["Scanned"] == "Gescand"].copy()

#Verzamel datums
    df["Date"] = pd.to_datetime(df["Scan Date"]).dt.date

#Verzamel kortingen
    df["Discounted"] = (
        (df["Final Price"] > 0) &
        (df["Final Price"] < df["Original Price"]))

#Volwassenen en 3+ samenvoegen
    df["Category"] = df["Ticket"]

    df.loc[
        df["Ticket"].isin(
            ["Volwassenen", "Kinderen vanaf 3 jaar"]
        ),
        "Category"
    ] = "Gewone tickets"

#Check welke dag
    date_str = input_dag

#Gewone tickets volle prijs
    gewone_full = (
        df[
            (df["Category"] == "Gewone tickets") &
            (~df["Discounted"])
        ]
        .groupby("Date")
        .size()
    )

#Gewone tickets met korting
    gewone_discount = (
        df[
            (df["Category"] == "Gewone tickets") &
            (df["Discounted"])
        ]
        .groupby("Date")
        .size()
    )
#Tripper tickets
    Tripper = (
        df[
            (df["Category"] == "Tripper ticket")
            ]
        .groupby("Date")
        .size()
    )
#Alle andere tickets

    other = (
        df[
            ~df["Category"].isin(["Gewone tickets", "Tripper ticket"])
        ]
        .groupby(["Date", "Category"])
        .size()
        .unstack(fill_value=0)
    )

    report = pd.concat(
        [
            Tripper_ticket.rename("Tripper ticket"),
            gewone_full.rename("Gewone tickets"),
            gewone_discount.rename("Gewone tickets korting"),
            other
        ],
        axis=1
    ).fillna(0)

# Laat alleen de resultaten zien van de berekeningen, en verwijder als er nul gescand zijn
    if upload_file is not None:
        if input_dag in report.index:
            selected_result = report.loc[[input_dag]]
            selected_result = selected_result.loc[:, (selected_result != 0).any(axis=0)]
            st.dataframe(selected_result)
        else:
            st.warning(f"Deze dag is er geen ticket gescand!")
