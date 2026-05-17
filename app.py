from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'muse_trento_secret_key_2024'
DB_NAME = 'biblioteca_muse.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        c = conn.cursor()
        # Tabella Utente (con EMAIL come da Doc 2)
        c.execute('''CREATE TABLE Utente (
            id_utente INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, cognome TEXT, username TEXT UNIQUE, 
            password TEXT, ruolo TEXT, email TEXT)''')
        
        # Tabella Materiale (con POSIZIONE come da Doc 2)
        c.execute('''CREATE TABLE Materiale (
            id_materiale INTEGER PRIMARY KEY AUTOINCREMENT, 
            titolo TEXT, autore TEXT, ISBN TEXT, 
            categoria TEXT, stato TEXT, posizione TEXT)''')
        
        # Tabella Prestito (con DATE come da Doc 2)
        c.execute('''CREATE TABLE Prestito (
            id_prestito INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_utente INTEGER, id_materiale INTEGER, 
            data_inizio TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            data_scadenza TIMESTAMP, 
            stato_prestito TEXT, 
            FOREIGN KEY(id_utente) REFERENCES Utente(id_utente), 
            FOREIGN KEY(id_materiale) REFERENCES Materiale(id_materiale))''')
        
   # Utenti di test con Password Criptate
        users = [
            ('Admin', 'Muse', 'admin', generate_password_hash('museadmin123'), 'amministratore'),
            ('Marco', 'Bibliotecario', 'biblio', generate_password_hash('musebiblio123'), 'bibliotecario'),
            ('Enrico', 'Senter', 'studente', generate_password_hash('musestudente123'), 'utente')
        ]
        c.executemany('INSERT INTO Utente (nome, cognome, username, password, ruolo) VALUES (?, ?, ?, ?, ?)', users)
        
        # 10 Libri iniziali (puoi aggiungerne altri dal pannello admin)
        libri = [
            ('L\'origine delle specie', 'Charles Darwin', '978-1', 'Scienza', 'Disponibile'),
            ('Dal Big Bang ai Buchi Neri', 'Stephen Hawking', '978-2', 'Astrofisica', 'Disponibile'),
            ('Il gene egoista', 'Richard Dawkins', '978-3', 'Biologia', 'Disponibile'),
            ('Sette brevi lezioni di fisica', 'Carlo Rovelli', '978-4', 'Fisica', 'Disponibile'),
            ('Cosmos', 'Carl Sagan', '978-6', 'Astronomia', 'Disponibile'),

            ('L\'ordine del tempo', 'Carlo Rovelli', '978-7', 'Fisica', 'Disponibile'),
            ('Breve storia di quasi tutto', 'Bill Bryson', '978-8', 'Scienza', 'Disponibile'),
            ('Il mondo infestato dai demoni', 'Carl Sagan', '978-9', 'Astronomia', 'Disponibile'),
            ('La realtà non è come ci appare', 'Carlo Rovelli', '978-10', 'Fisica Quantistica', 'Disponibile'),
            ('La biodiversità delle Alpi', 'Marco Avanzini', '978-11', 'Biodiversità', 'Disponibile'),

            ('Geologia delle Dolomiti', 'Michele Lanzinger', '978-12', 'Geologia', 'Disponibile'),
            ('Storia naturale del Trentino', 'Lorenzo Gardin', '978-13', 'Scienze Naturali', 'Disponibile'),
            ('La sesta estinzione', 'Elizabeth Kolbert', '978-14', 'Ecologia', 'Disponibile'),
            ('Spillover', 'David Quammen', '978-15', 'Biologia', 'Disponibile'),
            ('Il futuro del clima', 'Luca Mercalli', '978-16', 'Climatologia', 'Disponibile'),

            ('L\'universo elegante', 'Brian Greene', '978-17', 'Fisica', 'Disponibile'),
            ('Il bosco delle meraviglie', 'Daniele Zovi', '978-18', 'Natura', 'Disponibile'),
            ('Atlante degli animali delle Alpi', 'Franco Pedrotti', '978-19', 'Fauna Alpina', 'Disponibile'),
            ('Evoluzione', 'Telmo Pievani', '978-20', 'Biologia Evolutiva', 'Disponibile'),
            ('La vita segreta degli alberi', 'Peter Wohlleben', '978-21', 'Ecologia', 'Disponibile'),

            ('Origine dell\'universo', 'Margherita Hack', '978-22', 'Astrofisica', 'Disponibile'),
            ('Fisica dell\'impossibile', 'Michio Kaku', '978-23', 'Fisica', 'Disponibile'),
            ('Il pianeta umano', 'Piero Angela', '978-24', 'Divulgazione Scientifica', 'Disponibile'),
            ('DNA: Il segreto della vita', 'James Watson', '978-25', 'Genetica', 'Disponibile'),
            ('Viaggio nella biodiversità', 'Stefano Mancuso', '978-26', 'Botanica', 'Disponibile'),

            ('Foreste tropicali e biodiversità', 'Jane Goodall', '978-27', 'Ambiente', 'Disponibile'),
            ('Animali delle Dolomiti', 'Reinhold Messner', '978-28', 'Fauna', 'Disponibile'),
            ('La montagna vivente', 'Nan Shepherd', '978-29', 'Natura', 'Disponibile'),
            ('Ecologia per il futuro', 'Jeremy Rifkin', '978-30', 'Sostenibilità', 'Disponibile')
        ]
        c.executemany('INSERT INTO Materiale (titolo, autore, ISBN, categoria, stato) VALUES (?,?,?,?,?)', libri)
        conn.commit()
        conn.close()
        
@app.before_request
def setup():
    init_db()

# --- LOGIN/LOGOUT ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Utente WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], pwd):
            session.update({'id': user['id_utente'], 'user': user['username'], 'ruolo': user['ruolo']})
            return redirect(url_for('dashboard'))
        flash('Username o Password errati!!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    stats = {
        'totali': conn.execute('SELECT COUNT(*) FROM Materiale').fetchone()[0],
        'prestiti': conn.execute('SELECT COUNT(*) FROM Materiale WHERE stato != "Disponibile"').fetchone()[0],
        'utenti': conn.execute('SELECT COUNT(*) FROM Utente').fetchone()[0]
    }
    conn.close()
    return render_template('dashboard.html', stats=stats)

# --- CATALOGO E CRUD ---
@app.route('/catalogo')
def catalogo():
    if 'id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    libri = conn.execute('SELECT * FROM Materiale').fetchall()
    conn.close()
    return render_template('catalogo.html', libri=libri)

@app.route('/materiale/nuovo', methods=['GET', 'POST'])
def nuovo_materiale():
    if session.get('ruolo') not in ['amministratore', 'bibliotecario']: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO Materiale (titolo, autore, ISBN, categoria, stato, posizione) VALUES (?,?,?,?,?,?)',
                     (request.form['titolo'], request.form['autore'], request.form['isbn'], request.form['categoria'], 'Disponibile', request.form['posizione']))
        conn.commit()
        conn.close()
        return redirect(url_for('catalogo'))
    return render_template('form_materiale.html', azione="Aggiungi", m=None)

@app.route('/materiale/modifica/<int:id>', methods=['GET', 'POST'])
def modifica_materiale(id):
    if session.get('ruolo') not in ['amministratore', 'bibliotecario']: return redirect(url_for('dashboard'))
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('UPDATE Materiale SET titolo=?, autore=?, ISBN=?, categoria=?, posizione=? WHERE id_materiale=?',
                     (request.form['titolo'], request.form['autore'], request.form['isbn'], request.form['categoria'], request.form['posizione'], id))
        conn.commit()
        conn.close()
        flash('Materiale aggiornato!')
        return redirect(url_for('catalogo'))
    
    m = conn.execute('SELECT * FROM Materiale WHERE id_materiale = ?', (id,)).fetchone()
    conn.close()
    return render_template('form_materiale.html', azione="Modifica", m=m)

@app.route('/materiale/elimina/<int:id>')
def elimina_materiale(id):
    if session.get('ruolo') == 'amministratore':
        conn = get_db_connection()
        conn.execute('DELETE FROM Materiale WHERE id_materiale = ?', (id,))
        conn.commit()
        conn.close()
    return redirect(url_for('catalogo'))

# --- PRESTITI ---
@app.route('/prenota/<int:id>', methods=['POST'])
def prenota(id):
    conn = get_db_connection()
    # Calcolo data scadenza (oggi + 15 giorni come da Doc 2)
    scadenza = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d %H:%M')
    
    conn.execute('UPDATE Materiale SET stato = "In Prestito" WHERE id_materiale = ?', (id,))
    conn.execute('INSERT INTO Prestito (id_utente, id_materiale, data_scadenza, stato_prestito) VALUES (?,?,?,?)', 
                 (session['id'], id, scadenza, 'Attivo'))
    conn.commit()
    conn.close()
    return redirect(url_for('catalogo'))

@app.route('/restituisci/<int:id>', methods=['POST'])
def restituisci(id):
    conn = get_db_connection()
    conn.execute('UPDATE Materiale SET stato = "Disponibile" WHERE id_materiale = ?', (id,))
    conn.execute('UPDATE Prestito SET stato_prestito = "Restituito" WHERE id_materiale = ? AND stato_prestito = "Attivo"', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('catalogo'))

@app.route('/gestione_prestiti')
def gestione_prestiti():
    if session.get('ruolo') not in ['amministratore', 'bibliotecario']: return redirect(url_for('dashboard'))
    conn = get_db_connection()
    query = '''
        SELECT p.*, u.username, u.nome, u.cognome, m.titolo 
        FROM Prestito p 
        JOIN Utente u ON p.id_utente = u.id_utente 
        JOIN Materiale m ON p.id_materiale = m.id_materiale 
        ORDER BY p.data_inizio DESC
    '''
    prestiti = conn.execute(query).fetchall()
    conn.close()
    return render_template('gestione_prestiti.html', prestiti=prestiti)

if __name__ == '__main__':
    app.run(debug=True)
