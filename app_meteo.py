import streamlit as st
import urllib.request
import json
import datetime

# --- Configuration ---
LAT = 48.853  # Secteur : BPI / Sainte-Geneviève
LON = 2.349
SEUIL_PLUIE_LEGERE = 0.3
SEUIL_PLUIE_MOYENNE = 1.0
SEUIL_PLUIE_FORTE = 5.0

# --- Design de la page ---
st.set_page_config(page_title="Radar Tactique", page_icon="🌂", layout="centered")

def get_previsions():
    # forecast_days=2 pour éviter les bugs si tu consultes l'app à 23h
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=precipitation,precipitation_probability,weathercode,windspeed_10m"
        f"&forecast_days=2"
        f"&timezone=Europe/Paris"
        f"&models=best_match"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None

def code_meteo_label(code):
    codes = {
        0: "Ciel dégagé", 1: "Peu nuageux", 2: "Partiellement nuageux", 3: "Couvert",
        45: "Brouillard", 48: "Brouillard givrant",
        51: "Bruine légère", 53: "Bruine modérée", 55: "Bruine dense",
        61: "Pluie légère", 63: "Pluie modérée", 65: "Pluie forte",
        71: "Neige légère", 73: "Neige modérée", 75: "Neige forte",
        80: "Averses légères", 81: "Averses modérées", 82: "Averses fortes",
        95: "Orage", 96: "Orage avec grêle", 99: "Orage fort avec grêle",
    }
    return codes.get(code, f"Code {code}")

def main():
    st.title("🌂 Radar Tactique - Paris")
    st.markdown("**Secteur :** BPI / Bibliothèque Sainte-Geneviève")
    
    data = get_previsions()
    if not data:
        st.error("Impossible de récupérer les données Météo. Vérifie ta connexion.")
        return

    maintenant = datetime.datetime.now()
    times = data["hourly"]["time"]
    pluies = data["hourly"]["precipitation"]
    probas = data["hourly"]["precipitation_probability"]
    vents = data["hourly"]["windspeed_10m"]
    codes = data["hourly"]["weathercode"]

    # --- Extraction pour la décision immédiate (3h) ---
    fenetre = []
    for i, t_str in enumerate(times):
        t = datetime.datetime.fromisoformat(t_str)
        if t >= maintenant.replace(minute=0, second=0, microsecond=0) and t <= maintenant + datetime.timedelta(hours=3):
            fenetre.append({"heure": t, "pluie": pluies[i], "proba": probas[i], "vent": vents[i]})

    if not fenetre:
        st.warning("Données temporelles non alignées.")
        return

    pluie_maintenant = fenetre[0]["pluie"]
    proba_pluie = fenetre[0]["proba"]
    vent_maintenant = fenetre[0]["vent"]

    st.subheader("Situation Actuelle")
    col1, col2, col3 = st.columns(3)
    col1.metric("Pluie", f"{pluie_maintenant} mm/h")
    col2.metric("Probabilité", f"{proba_pluie} %")
    col3.metric("Vent", f"{vent_maintenant} km/h")

    st.markdown("---")
    st.subheader("Décision Tactique")

    if pluie_maintenant < SEUIL_PLUIE_LEGERE and proba_pluie < 30:
        st.success("✅ **PARTIR MAINTENANT**\n\nPas de pluie détectée. Conditions optimales pour sortir de la bibliothèque.")
    elif pluie_maintenant < SEUIL_PLUIE_LEGERE and proba_pluie >= 30:
        st.warning("🟡 **PARTIR MAINTENANT (avec vigilance)**\n\nPas de pluie immédiate, mais le risque augmente. Garde un imperméable accessible.")
    elif pluie_maintenant < SEUIL_PLUIE_MOYENNE:
        st.warning("🟡 **BRUINE EN COURS**\n\nPartir si urgence, sinon attendre environ 30-60 min que la cellule passe.")
    else:
        st.error(f"🔴 **NE PAS SORTIR MAINTENANT**\n\nPluie forte ({pluie_maintenant} mm/h). Reste à l'abri pour le moment.")

    st.markdown("---")
    
    # --- Création du tableau des prévisions (12h) ---
    st.subheader("📅 Prévisions Heure par Heure (Prochaines 12h)")
    
    tableau_previsions = []
    for i, t_str in enumerate(times):
        t = datetime.datetime.fromisoformat(t_str)
        if t < maintenant.replace(minute=0, second=0, microsecond=0):
            continue
        if t > maintenant + datetime.timedelta(hours=12):
            break
            
        pluie_val = pluies[i]
        label = code_meteo_label(codes[i])
        
        # Indicateur visuel
        if pluie_val >= SEUIL_PLUIE_FORTE:
            indic = "🔴"
        elif pluie_val >= SEUIL_PLUIE_MOYENNE:
            indic = "🟠"
        elif pluie_val >= SEUIL_PLUIE_LEGERE:
            indic = "🟡"
        else:
            indic = "🟢"

        tableau_previsions.append({
            "Heure": t.strftime('%Hh%M'),
            "Pluie (mm/h)": f"{pluie_val:.1f}",
            "Proba (%)": f"{probas[i]}",
            "Vent (km/h)": f"{vents[i]:.1f}",
            "Conditions": f"{indic} {label}"
        })

    # Affichage propre du tableau dans Streamlit
    st.table(tableau_previsions)

if __name__ == "__main__":
    main()
