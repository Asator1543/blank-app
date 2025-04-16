import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

st.set_page_config(page_title="Kletter-Wettkampf", layout="wide")
st.title("🧗 Kletter-Wettkampf Auswertungstool")

wk_classes = ["WK 1", "WK 2", "WK 3", "WK 4", "WK-Inklusion"]

if 'wettkampf_data' not in st.session_state:
    st.session_state.wettkampf_data = {}
for wk in wk_classes:
    if wk not in st.session_state.wettkampf_data:
        st.session_state.wettkampf_data[wk] = {
            'teams': {},
            'toprope_routes': {'Route 1': 40, 'Route 2': 40, 'Route 3': 40},
        }

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
                    else:
                        st.error("Ein Team muss zwischen 4 und 6 Mitglieder haben.")

        if wk_state['teams']:
            laufzettel_pdf = generate_laufzettel_pdfs(wk_key, wk_state['teams'])
            st.download_button(
                label="📄 Laufzettel für alle Teams herunterladen",
                data=laufzettel_pdf,
                file_name=f"{wk_key}_laufzettel.pdf",
                mime="application/pdf"
            )

        st.subheader("💪 Boulderwertung")
        boulder_tabs = st.tabs([f"Boulder {i}" for i in range(1, 4)])
        for i, btab in enumerate(boulder_tabs, start=1):
            with btab:
                for team, members in wk_state['teams'].items():
                    st.markdown(f"**{team}**")
                    for member in members:
                        z_key = f"{wk_key}_b{i}_{team}_{member}_zone"
                        t_key = f"{wk_key}_b{i}_{team}_{member}_top"
                        col1, col2 = st.columns(2)
                        with col1:
                            st.checkbox(f"Zone erreicht: {member}", key=z_key)
                        with col2:
                            st.checkbox(f"Top erreicht: {member}", key=t_key)

        st.subheader("🧗‍♂️ Schwierigkeitsklettern")
        toprope_tabs = st.tabs([f"Route {i}" for i in range(1, 4)])
        for i, ttab in enumerate(toprope_tabs, start=1):
            route_name = f"Route {i}"
            with ttab:
                max_grips = st.number_input(
                    f"Anzahl Griffe für {route_name}",
                    min_value=1, max_value=100,
                    value=wk_state['toprope_routes'].get(route_name, 40),
                    key=f"{wk_key}_grips_{route_name}"
                )
                wk_state['toprope_routes'][route_name] = max_grips

                for team, members in wk_state['teams'].items():
                    st.markdown(f"**{team}**")
                    for member in members:
                        key = f"{wk_key}_t{i}_{team}_{member}_griff"
                        st.number_input(f"{member} erreichte Griffnummer", min_value=0, max_value=max_grips, key=key)

        st.subheader("⏱️ Speedwertung")
        all_speeds = []
        for team, members in wk_state['teams'].items():
            st.subheader(f"{team}")
            for member in members:
                key = f"{wk_key}_speed_{team}_{member}"
                time = st.number_input(f"Zeit für {member} (Sekunden)", min_value=0.0, max_value=300.0, step=0.01, key=key)
                all_speeds.append((member, team, time))

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
            s = sum([score for m, tname, _, score in speed_scores if tname == team])
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
