import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import json
import os

DATA_PATH = "save_data.json"

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

# Lade bestehende Daten
loaded_data = load_data()

st.set_page_config(page_title="Kletter-Wettkampf", layout="wide")
st.title("🧗 Kletter-Wettkampf Auswertungstool")

wk_classes = ["WK 1", "WK 2", "WK 3", "WK 4", "WK-Inklusion"]

if 'wettkampf_data' not in st.session_state:
    st.session_state.wettkampf_data = loaded_data or {wk: {'teams': {}, 'toprope_routes': {'Route 1': 40, 'Route 2': 40, 'Route 3': 40}} for wk in wk_classes}

def download_teams_csv():
    all_teams = []
    for wk_key, wk_data in st.session_state.wettkampf_data.items():
        for team_name, members in wk_data['teams'].items():
            for member in members:
                all_teams.append({'Wettkampfklasse': wk_key, 'Team': team_name, 'Mitglied': member})
    df_teams = pd.DataFrame(all_teams)
    return df_teams.to_csv(index=False).encode('utf-8')

def upload_teams_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    # Reset the teams
    for wk in wk_classes:
        st.session_state.wettkampf_data[wk]['teams'] = {}
    # Populate the teams
    for _, row in df.iterrows():
        wk_key = row['Wettkampfklasse']
        team_name = row['Team']
        member = row['Mitglied']
        if team_name not in st.session_state.wettkampf_data[wk_key]['teams']:
            st.session_state.wettkampf_data[wk_key]['teams'][team_name] = []
        st.session_state.wettkampf_data[wk_key]['teams'][team_name].append(member)
    save_data(st.session_state.wettkampf_data)

st.download_button(
    label="📥 Teams als CSV herunterladen",
    data=download_teams_csv(),
    file_name='teams.csv',
    mime='text/csv'
)

uploaded_file = st.file_uploader("CSV-Datei hochladen", type="csv")
if uploaded_file is not None:
    upload_teams_csv(uploaded_file)
    st.success("Teams erfolgreich geladen!")

def generate_results_pdf(wk_key, result_df, speed_df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>Ergebnisse – {wk_key}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Teamwertung
    elements.append(Paragraph("Team-Rangliste", styles["Heading2"]))
    data = [result_df.columns.tolist()] + result_df.values.tolist()
    table = Table(data, hAlign='LEFT')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    if len(data) > 1:
        table_style.add('BACKGROUND', (0, 1), (-1, 1), colors.gold)
    if len(data) > 2:
        table_style.add('BACKGROUND', (0, 2), (-1, 2), colors.silver)
    if len(data) > 3:
        table_style.add('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#cd7f32"))
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Einzel-Speedwertung
    elements.append(Paragraph("Speed Einzelwertung", styles["Heading2"]))
    data = [speed_df.columns.tolist()] + speed_df.values.tolist()
    table = Table(data, hAlign='LEFT')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    if len(data) > 1:
        table_style.add('BACKGROUND', (0, 1), (-1, 1), colors.gold)
    if len(data) > 2:
        table_style.add('BACKGROUND', (0, 2), (-1, 2), colors.silver)
    if len(data) > 3:
        table_style.add('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#cd7f32"))
    table.setStyle(table_style)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

def generate_laufzettel_pdfs(wk_key, teams):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    # Griffanzahlen aus dem gespeicherten Wettkampf laden
    route_grips = st.session_state.wettkampf_data[wk_key]['toprope_routes']
    max_r1 = route_grips.get("Route 1", "")
    max_r2 = route_grips.get("Route 2", "")
    max_r3 = route_grips.get("Route 3", "")

    for team, members in teams.items():
        elements.append(Paragraph(f"<b>Laufzettel – {wk_key}</b>", styles["Title"]))
        elements.append(Paragraph(f"<b>Team:</b> {team}", styles["Heading2"]))

        # Tabellenköpfe
        header_main = ["TN", "Bouldern", "", "", "Schwierigkeitsklettern", "", "", "Speed", ""]
        header_sub = ["", "Boulder 1", "Boulder 2", "Boulder 3", "Route 1", "Route 2", "Route 3", "Zeit 1", "Zeit 2"]
        griffanzahl = [
            "",
            "", "", "",
            f"max. {max_r1}" if max_r1 else "",
            f"max. {max_r2}" if max_r2 else "",
            f"max. {max_r3}" if max_r3 else "",
            "", ""
        ]

        # Teilnehmerzeilen
        data = [header_main, header_sub, griffanzahl]
        for m in members:
            data.append([m] + ["" for _ in range(8)])

        col_widths = [100] + [60]*8
        row_heights = [20, 20, 20] + [40]*len(members)

        table = Table(data, hAlign='LEFT', colWidths=col_widths, rowHeights=row_heights)

        # Tabellenstil
        style = TableStyle([
            ('SPAN', (1,0), (3,0)),  # Bouldern
            ('SPAN', (4,0), (6,0)),  # Schwierigkeitsklettern
            ('SPAN', (7,0), (8,0)),  # Speed

            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
            ('BACKGROUND', (0, 2), (-1, 2), colors.whitesmoke),

            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,2), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)

        elements.append(table)
        elements.append(Spacer(1, 12))

        # Erklärung
        erklaerung = (
            "📌 <b>Hinweise zur Punktevergabe:</b><br/>"
            "• Beim <b>Bouldern</b> können pro Problem 0, 25 oder 50 Punkte erreicht werden.<br/>"
            "• Beim <b>Schwierigkeitsklettern</b> bitte die Nummer des erreichten Griffs eintragen.<br/>"
            "• Beim <b>Speed</b> hat jede(r) TN zwei Versuche – bitte beide Zeiten (in Sekunden) bei <i>Zeit 1</i> und <i>Zeit 2</i> eintragen."
        )
        elements.append(Paragraph(erklaerung, styles["Normal"]))
        elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()

tabs = st.tabs(wk_classes)
for wk_key, tab in zip(wk_classes, tabs):
    with tab:
        st.header(f"Wettkampfklasse: {wk_key}")
        wk_state = st.session_state.wettkampf_data[wk_key]

        st.subheader("👥 Teams verwalten")
        with st.form(f"team_form_{wk_key}"):
            team_name = st.text_input("Teamname", key=f"teamname_{wk_key}")
            members = st.text_area("Teammitglieder (ein Name pro Zeile)", key=f"members_{wk_key}").splitlines()
            submitted = st.form_submit_button("Team hinzufügen")
            if submitted and team_name and 4 <= len(members) <= 6:
                wk_state['teams'][team_name] = members
                st.success(f"Team '{team_name}' hinzugefügt.")
                save_data(st.session_state.wettkampf_data)

        if wk_state['teams']:
            with st.expander("✏️ Team bearbeiten"):
                team_to_edit = st.selectbox("Team auswählen", list(wk_state['teams'].keys()), key=f"edit_team_{wk_key}")
                edited_members = st.text_area("Mitglieder bearbeiten (ein Name pro Zeile)",
                                              value="\n".join(wk_state['teams'][team_to_edit]),
                                              key=f"edit_members_{wk_key}").splitlines()
                if st.button("Team aktualisieren", key=f"update_team_{wk_key}"):
                    if 4 <= len(edited_members) <= 6:
                        wk_state['teams'][team_to_edit] = edited_members
                        st.success(f"Team '{team_to_edit}' wurde aktualisiert.")
                        save_data(st.session_state.wettkampf_data)
                    else:
                        st.error("Ein Team muss zwischen 4 und 6 Mitglieder haben.")

            laufzettel_pdf = generate_laufzettel_pdfs(wk_key, wk_state['teams'])
            st.download_button(
                label="📄 Laufzettel für alle Teams herunterladen",
                data=laufzettel_pdf,
                file_name=f"{wk_key}_laufzettel.pdf",
                mime="application/pdf"
            )

            st.subheader("💪 Boulderwertung")
            if wk_state['teams']:
                boulder_tabs = st.tabs(list(wk_state['teams'].keys()))
                for team, btab in zip(wk_state['teams'].keys(), boulder_tabs):
                    with btab:
                        st.markdown(f"**Team: {team}**")
                        for i in range(1, 4):
                            st.markdown(f"Boulder {i}")
                            for member in wk_state['teams'][team]:
                                z_key = f"{wk_key}_b{i}_{team}_{member}_zone"
                                t_key = f"{wk_key}_b{i}_{team}_{member}_top"
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.checkbox(f"Zone erreicht: {member}", key=z_key)
                                with col2:
                                    st.checkbox(f"Top erreicht: {member}", key=t_key)

            st.subheader("🧗‍♂️ Schwierigkeitsklettern")
            if wk_state['teams']:
                toprope_tabs = st.tabs(list(wk_state['teams'].keys()))
                for team, ttab in zip(wk_state['teams'].keys(), toprope_tabs):
                    with ttab:
                        st.markdown(f"**Team: {team}**")
                        for i in range(1, 4):
                            route_name = f"Route {i}"
                            max_grips = st.number_input(
                                f"Anzahl Griffe für {route_name}",
                                min_value=1, max_value=100,
                                value=wk_state['toprope_routes'].get(route_name, 40),
                                key=f"{wk_key}_{team}_grips_{route_name}"  # Eindeutiger Schlüssel
                            )
                            wk_state['toprope_routes'][route_name] = max_grips

                            for member in wk_state['teams'][team]:
                                key = f"{wk_key}_t{i}_{team}_{member}_griff"
                                st.number_input(f"{member} erreichte Griffnummer", min_value=0, max_value=max_grips, key=key)

            st.subheader("⏱️ Speedwertung")
            all_speeds = []  # Initialize the list here
            if wk_state['teams']:
                speed_tabs = st.tabs(list(wk_state['teams'].keys()))
                for team, stab in zip(wk_state['teams'].keys(), speed_tabs):
                    with stab:
                        st.markdown(f"**Team: {team}**")
                        for member in wk_state['teams'][team]:
                            key = f"{wk_key}_speed_{team}_{member}"
                            time = st.number_input(f"Zeit für {member} (Sekunden)", min_value=0.0, max_value=300.0, step=0.01, key=key)
                            all_speeds.append((member, team, time))  # Collect speed data

        st.subheader("🏆 Gesamtwertung")

        def get_boulder_score(team):
            total = 0
            for i in range(1, 4):
                scores = []
                for member in wk_state['teams'][team]:
                    z = st.session_state.get(f"{wk_key}_b{i}_{team}_{member}_zone", False)
                    t = st.session_state.get(f"{wk_key}_b{i}_{team}_{member}_top", False)
                    score = 50 if t else 25 if z else 0
                    scores.append(score)
                top_scores = sorted(scores, reverse=True)[:4]
                total += sum(top_scores)
            return total

        def get_toprope_score(team):
            total = 0
            for i in range(1, 4):
                route = f"Route {i}"
                max_grips = wk_state['toprope_routes'][route]
                scores = []
                for member in wk_state['teams'][team]:
                    reached = st.session_state.get(f"{wk_key}_t{i}_{team}_{member}_griff", 0)
                    score = (reached / max_grips) * 100
                    scores.append(score)
                top_scores = sorted(scores, reverse=True)[:4]
                total += sum(top_scores)
            return total

        def get_speed_scores():
            valid = [(m, t, time) for m, t, time in all_speeds if time > 0]
            sorted_by_time = sorted(valid, key=lambda x: x[2])
            scores = []
            for rank, (member, team, time) in enumerate(sorted_by_time):
                score = max(0, 100 - rank * 2)
                scores.append((member, team, time, score))
            return scores

        speed_scores = get_speed_scores()

        team_results = []
        for team in wk_state['teams']:
            b = get_boulder_score(team)
            t = get_toprope_score(team)
            team_speed_scores = sorted([score for m, tname, _, score in speed_scores if tname == team], reverse=True)[:4]
            s = sum(team_speed_scores)
            team_score = (1/5)*s + (2/5)*t + (2/5)*b
            team_results.append((team, round(team_score, 2)))

        st.subheader("🔹 Team-Rangliste")
        result_df = pd.DataFrame(sorted(team_results, key=lambda x: x[1], reverse=True), columns=["Team", "Punkte"])
        result_df.index += 1
        st.dataframe(result_df, use_container_width=True)

        st.subheader("⏱️ Einzel-Speedwertung")
        speed_df = pd.DataFrame(speed_scores, columns=["Teilnehmer", "Team", "Zeit (s)", "Punkte"])
        speed_df = speed_df.sort_values(by="Zeit (s)")
        speed_df.index += 1
        st.dataframe(speed_df, use_container_width=True)

        pdf_data = generate_results_pdf(wk_key, result_df, speed_df)
        st.download_button(
            label="📄 Ergebnisse als PDF exportieren",
            data=pdf_data,
            file_name=f"{wk_key}_ergebnisse.pdf",
            mime="application/pdf"
        )
