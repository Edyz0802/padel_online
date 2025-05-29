from flask import Flask, render_template
from collections import defaultdict
from trueskill import Rating, TrueSkill

app = Flask(__name__)

ts = TrueSkill(draw_probability=0)  # Nessun pareggio

def leggi_partite(nome_file):
    partite = []
    try:
        with open(nome_file, "r") as f:
            for riga in f:
                dati = riga.strip().split(",")
                if len(dati) == 6:
                    p1a, p1b, p2a, p2b = dati[:4]
                    punteggio1 = int(dati[4])
                    punteggio2 = int(dati[5])
                    partite.append((p1a, p1b, p2a, p2b, punteggio1, punteggio2))
    except FileNotFoundError:
        print(f"File {nome_file} non trovato.")
    return partite

def genera_classifica(partite):
    ratings = defaultdict(lambda: Rating())

    for p in partite:
        p1a, p1b, p2a, p2b, punteggio1, punteggio2 = p

        team1 = [ratings[p1a], ratings[p1b]]
        team2 = [ratings[p2a], ratings[p2b]]

        if punteggio1 > punteggio2:
            ranks = [0, 1]
        else:
            ranks = [1, 0]

        new_ratings = ts.rate([team1, team2], ranks=ranks)

        ratings[p1a], ratings[p1b] = new_ratings[0]
        ratings[p2a], ratings[p2b] = new_ratings[1]

    # Puoi anche usare mu - 3*sigma per un ranking conservativo
    classifica = sorted(ratings.items(), key=lambda x: x[1].mu, reverse=True)
    return classifica

@app.route("/")
def home():
    partite = leggi_partite("partite.txt")
    classifica = genera_classifica(partite)
    return render_template("classifica.html", classifica=classifica)

if __name__ == "__main__":
    app.run(debug=True)
