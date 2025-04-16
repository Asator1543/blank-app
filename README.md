mkdir kletter-auswertung
cd kletter-auswertung
pip install streamlit
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kletter-Wettkampf", layout="wide")

st.title("🏆 Kletter-Wettkampf Auswertungstool")

# SESSIONSTATE initialisieren
if 'teams' not in st.session_state:
    st.session_state.teams = {}

# TEAMS EINGEBEN
st.header("1️⃣ Teams & Mitglieder")

num_teams = st.number_input("Wie viele Teams nehmen teil?", min_value=1, max_value=20, step=1)

for i in range(1, num_teams + 1):
    team_name = st.text_input(f"Team {i} Name", key=f"team_{i}_name")
    num_members = st.slider(f"Anzahl Mitglieder für Team {team_name or i}", 4, 6, key=f"team_{i}_members")

    members = []
    for j in range(1, num_members + 1):
        member_name = st.text_input(f"Mitglied {j} Name für Team {team_name or i}", key=f"team_{i}_member_{j}")
        members.append(member_name)

    if team_name:
        st.session_state.teams[team_name] = members

st.success("Teams gespeichert!") if st.session_state.teams else None
st.header("2️⃣ Boulder-Erfassung")

# Punktevergabe definieren
BOULDER_ZONE_POINTS = 5
BOULDER_TOP_POINTS = 10
NUM_BOULDERS = 3

if st.session_state.teams:
    boulder_data = []

    for team, members in st.session_state.teams.items():
        st.subheader(f"Team: {team}")

        for member in members:
            st.markdown(f"**{member}**")

            member_points = 0
            for boulder_num in range(1, NUM_BOULDERS + 1):
                col1, col2 = st.columns(2)
                with col1:
                    zone = st.checkbox(f"Zone erreicht (Boulder {boulder_num})", key=f"{team}_{member}_b{boulder_num}_zone")
                with col2:
                    top = st.checkbox(f"Top erreicht (Boulder {boulder_num})", key=f"{team}_{member}_b{boulder_num}_top")

                points = 0
                if zone:
                    points += BOULDER_ZONE_POINTS
                if top:
                    points += BOULDER_TOP_POINTS

                member_points += points

            boulder_data.append({
                "Team": team,
                "Teilnehmer": member,
                "Punkte": member_points
            })

    # In DataFrame umwandeln
    df_boulder = pd.DataFrame(boulder_data)

    # Beste 4 Leistungen pro Team für die Teamwertung
    team_boulder_scores = {}
    for team in df_boulder["Team"].unique():
        team_df = df_boulder[df_boulder["Team"] == team]
        best_4 = team_df.nlargest(4, "Punkte")
        team_score = best_4["Punkte"].sum()
        team_boulder_scores[team] = team_score

    st.subheader("📋 Boulder-Teamwertung (Top 4 Leistungen pro Team)")
    boulder_results_df = pd.DataFrame([
        {"Team": team, "Team-Boulder-Punkte": points}
        for team, points in team_boulder_scores.items()
    ]).sort_values(by="Team-Boulder-Punkte", ascending=False)

    st.dataframe(boulder_results_df, use_container_width=True)

    # Speichern im Session State für spätere Gesamtauswertung
    st.session_state.boulder_scores = team_boulder_scores
else:
    st.warning("Bitte zuerst die Teams eintragen.")
st.header("3️⃣ Toprope-Erfassung")

NUM_TOPROPE_ROUTES = 3

if st.session_state.teams:
    st.subheader("🔧 Routen-Setup")

    # Eingabe der Griffanzahl pro Route
    toprope_grip_counts = []
    for route_num in range(1, NUM_TOPROPE_ROUTES + 1):
        grips = st.number_input(f"Anzahl Griffe für Route {route_num}", min_value=1, max_value=100, value=40, key=f"grips_route_{route_num}")
        toprope_grip_counts.append(grips)

    st.divider()
    st.subheader("🧗‍♀️ Ergebnisse eintragen")

    toprope_data = []

    for team, members in st.session_state.teams.items():
        st.markdown(f"### Team: {team}")
        for member in members:
            st.markdown(f"**{member}**")

            total_points = 0
            for route_num in range(1, NUM_TOPROPE_ROUTES + 1):
                max_grips = toprope_grip_counts[route_num - 1]
                reached = st.number_input(
                    f"Erreichte Griffe in Route {route_num} (von {max_grips})",
                    min_value=0,
                    max_value=max_grips,
                    key=f"{team}_{member}_route_{route_num}"
                )
                points = (reached / max_grips) * 100
                total_points += points

            toprope_data.append({
                "Team": team,
                "Teilnehmer": member,
                "Punkte": round(total_points, 2)
            })

    # DataFrame erstellen
    df_toprope = pd.DataFrame(toprope_data)

    # Beste 4 Leistungen pro Team
    team_toprope_scores = {}
    for team in df_toprope["Team"].unique():
        team_df = df_toprope[df_toprope["Team"] == team]
        best_4 = team_df.nlargest(4, "Punkte")
        team_score = best_4["Punkte"].sum()
        team_toprope_scores[team] = team_score

    st.subheader("📋 Toprope-Teamwertung (Top 4 Leistungen pro Team)")
    toprope_results_df = pd.DataFrame([
        {"Team": team, "Team-Toprope-Punkte": round(score, 2)}
        for team, score in team_toprope_scores.items()
    ]).sort_values(by="Team-Toprope-Punkte", ascending=False)

    st.dataframe(toprope_results_df, use_container_width=True)

    # Speichern für Gesamtauswertung
    st.session_state.toprope_scores = team_toprope_scores
else:
    st.warning("Bitte zuerst die Teams eintragen.")
st.header("4️⃣ Speed-Erfassung")

if st.session_state.teams:
    st.subheader("⏱ Zeiten eintragen (in Sekunden)")

    speed_data = []

    for team, members in st.session_state.teams.items():
        st.markdown(f"### Team: {team}")
        for member in members:
            time = st.number_input(
                f"Zeit für {member} (in Sekunden)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"{team}_{member}_speed"
            )
            speed_data.append({
                "Team": team,
                "Teilnehmer": member,
                "Zeit": time
            })

    # Ranking aller Teilnehmer:innen nach Zeit
    df_speed = pd.DataFrame(speed_data)
    df_speed_sorted = df_speed.sort_values(by="Zeit")
    df_speed_sorted.reset_index(drop=True, inplace=True)

    # Punktevergabe: 100 - 2 * Platz
    df_speed_sorted["Speed-Punkte"] = df_speed_sorted.index.map(lambda i: max(100 - 2 * i, 0))

    # Teamwertung: Top 4 Ergebnisse pro Team
    team_speed_scores = {}
    for team in df_speed["Team"].unique():
        team_df = df_speed_sorted[df_speed_sorted["Team"] == team]
        best_4 = team_df.nlargest(4, "Speed-Punkte")
        team_score = best_4["Speed-Punkte"].sum()
        team_speed_scores[team] = team_score

    st.subheader("📋 Speed-Teamwertung (Top 4 Leistungen pro Team)")
    speed_results_df = pd.DataFrame([
        {"Team": team, "Team-Speed-Punkte": points}
        for team, points in team_speed_scores.items()
    ]).sort_values(by="Team-Speed-Punkte", ascending=False)

    st.dataframe(speed_results_df, use_container_width=True)

    st.subheader("🏃‍♂️ Speed-Einzelranking")
    st.dataframe(
        df_speed_sorted[["Teilnehmer", "Team", "Zeit", "Speed-Punkte"]],
        use_container_width=True
    )

    # Für Gesamtauswertung speichern
    st.session_state.speed_scores = team_speed_scores

else:
    st.warning("Bitte  die Teams eintragen.")

    st.header("5️⃣ Gesamtauswertung")

# Check, ob alle Disziplinen vorhanden sind
if all(score_key in st.session_state for score_key in ["speed_scores", "toprope_scores", "boulder_scores"]):

    all_teams = list(st.session_state.teams.keys())

    summary_data = []

    for team in all_teams:
        speed = st.session_state.speed_scores.get(team, 0)
        toprope = st.session_state.toprope_scores.get(team, 0)
        boulder = st.session_state.boulder_scores.get(team, 0)

        total = round((1/5 * speed) + (2/5 * toprope) + (2/5 * boulder), 2)

        summary_data.append({
            "Team": team,
            "Speed": speed,
            "Toprope": toprope,
            "Bouldern": boulder,
            "Gesamtpunktzahl": total
        })

    df_summary = pd.DataFrame(summary_data)
    df_summary = df_summary.sort_values(by="Gesamtpunktzahl", ascending=False).reset_index(drop=True)

    df_summary.index += 1  # Platzierung starten bei 1

    st.subheader("🏁 Endstand")
    st.dataframe(df_summary, use_container_width=True)

else:
    st.info("Bitte erst alle Disziplinen erfassen, um die Gesamtwertung zu berechnen.")

import io

def download_button_csv(df, filename, label):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )
download_button_csv(boulder_results_df, "boulder_teamwertung.csv", "📥 Boulderwertung als CSV herunterladen")
download_button_csv(toprope_results_df, "toprope_teamwertung.csv", "📥 Topropewertung als CSV herunterladen")
download_button_csv(speed_results_df, "speed_teamwertung.csv", "📥 Speed-Teamwertung als CSV herunterladen")
download_button_csv(df_speed_sorted[["Teilnehmer", "Team", "Zeit", "Speed-Punkte"]], "speed_einzelranking.csv", "📥 Speed-Einzelranking als CSV herunterladen")
download_button_csv(df_summary, "gesamtwertung.csv", "📥 Gesamtwertung als CSV herunterladen")
