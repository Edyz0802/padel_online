import os
from collections import defaultdict
from flask import Flask, render_template
from trueskill import TrueSkill

app = Flask(__name__)

# Inizializza TrueSkill
ts = TrueSkill(draw_probability=0.1)  # 10% di pareggio

# Funzione per leggere partite da file
def leggi_partite(nome_file):
    partite = []
    with open(nome_file, "r") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#"):
                continue
            campi = [c.strip() for c in riga.split(",")]
            # campi: data, gioc1, gioc2, gioc3, gioc4, vincitori, risultato set
            if len(campi) < 7:
                continue
            partite.append({
                "data": campi[0],
                "giocatori_team1": [campi[1], campi[2]],
                "giocatori_team2": [campi[3], campi[4]],
                "vincitori": campi[5].lower(),
                "set": campi[6]
            })
    return partite

# Calcola classifica con TrueSkill e statistiche
def genera_classifica(partite):
    ratings = defaultdict(ts.create_rating)
    stats = defaultdict(lambda: {"giocate":0, "vittorie":0, "sconfitte":0, "pareggi":0})

    for p in partite:
        team1 = [ratings[g] for g in p["giocatori_team1"]]
        team2 = [ratings[g] for g in p["giocatori_team2"]]

        # Aggiorna partite giocate
        for g in p["giocatori_team1"] + p["giocatori_team2"]:
            stats[g]["giocate"] += 1

        # Gestione esito
        vincitori = p["vincitori"]
        if vincitori == "pareggio":
            ratings_team1, ratings_team2 = ts.rate(team1, team2, ranks=[0,0])
            # Aggiorna pareggi
            for g in p["giocatori_team1"] + p["giocatori_team2"]:
                stats[g]["pareggi"] += 1
        else:
            # Chi ha vinto?
            if set(p["giocatori_team1"]) == set(vincitori.split("+")):
                ranks = [0, 1]
                for g in p["giocatori_team1"]:
                    stats[g]["vittorie"] += 1
                for g in p["giocatori_team2"]:
                    stats[g]["sconfitte"] += 1
            else:
                ranks = [1, 0]
                for g in p["giocatori_team1"]:
                    stats[g]["sconfitte"] += 1
                for g in p["giocatori_team2"]:
                    stats[g]["vittorie"] += 1

            ratings_team1, ratings_team2 = ts.rate(team1, team2, ranks=ranks)

        # Aggiorna i ratings dei giocatori
        for i, g in enumerate(p["giocatori_team1"]):
            ratings[g] = ratings_team1[i]
        for i, g in enumerate(p["giocatori_team2"]):
            ratings[g] = ratings_team2[i]

    # Prepara lista con dati utili per la classifica
    lista_classifica = []
    for giocatore, rating in ratings.items():
        mu = rating.mu
        sigma = rating.sigma
        punteggio = mu - 3 * sigma  # TrueSkill conservative estimate
        lista_classifica.append({
            "nome": giocatore,
            "mu": round(mu, 2),
            "sigma": round(sigma, 2),
            "punteggio": round(punteggio, 2),
            "giocate": stats[giocatore]["giocate"],
            "vittorie": stats[giocatore]["vittorie"],
            "sconfitte": stats[giocatore]["sconfitte"],
            "pareggi": stats[giocatore]["pareggi"]
        })

    # Ordina per punteggio decrescente
    lista_classifica.sort(key=lambda x: x["punteggio"], reverse=True)
    return lista_classifica

@app.route("/")
def home():
    partite = leggi_partite("partite.txt")
    classifica = genera_classifica(partite)
    return render_template("classifica.html", classifica=classifica)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
