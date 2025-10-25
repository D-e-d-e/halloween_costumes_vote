from flask import render_template, request, redirect, url_for, flash, make_response, session
from app import app, db
from app.models import Costume, Vote, Voter
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import os
import uuid

# --- Funzione per generare QR code ---
def generate_qr_code_image(costume_id, base_url):
    # L'URL a cui il QR reindirizzerà quando scansionato
    # Usiamo url_for per generare l'URL per la pagina di voto
    vote_url = url_for('vote_page', costumeId=costume_id, _external=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # Livello di correzione errori alto
        box_size=10,
        border=4,
    )
    qr.add_data(vote_url)
    qr.make(fit=True)

    # Crea un'immagine con moduli arrotondati per un look più moderno
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())

    # Percorso dove salvare l'immagine del QR code
    filename = f"qr_code_{costume_id}.png"
    filepath = os.path.join(app.root_path, 'static', 'qr_codes', filename)
    
    # Assicurati che la directory esista
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    img.save(filepath)
    # Ritorna il percorso relativo che Flask può usare per servire il file statico
    return os.path.join('qr_codes', filename) # Esempio: 'qr_codes/qr_code_xyz.png'

# --- Routes per le pagine HTML (Frontend base) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Il nome del costume è obbligatorio!', 'danger')
            return redirect(url_for('index'))

        new_costume = Costume(name=name, description=description)
        db.session.add(new_costume)
        db.session.commit() # Commit per avere l'ID

        # Genera il QR code e salva il percorso
        qr_code_path = generate_qr_code_image(new_costume.id, request.url_root)
        new_costume.qr_code_path = qr_code_path
        db.session.commit()

        flash(f'Costume "{name}" aggiunto con successo e QR code generato!', 'success')
        return redirect(url_for('index'))
    
    costumes = Costume.query.all()
    # Preparare i dati per la visualizzazione dei QR code
    costumes_with_qr_urls = []
    for costume in costumes:
        # url_for('static', filename=...) genera l'URL corretto per il file statico
        qr_static_url = url_for('static', filename=costume.qr_code_path) if costume.qr_code_path else None
        costumes_with_qr_urls.append({
            'id': costume.id,
            'name': costume.name,
            'description': costume.description,
            'qr_static_url': qr_static_url
        })

    return render_template('index.html', costumes=costumes_with_qr_urls)

@app.route('/vote_page')
def vote_page():
    costume_id = request.args.get('costumeId')
    if not costume_id:
        flash('ID del costume mancante per la votazione.', 'danger')
        return redirect(url_for('index')) # Reindirizza alla pagina principale

    costume = Costume.query.get(costume_id)
    if not costume:
        flash('Costume non trovato.', 'danger')
        return redirect(url_for('index'))
    
    # Prepara la risposta per impostare il cookie
    response = make_response(render_template('vote_page.html', costume=costume))

    voter_identifier = request.cookies.get('voter_id')
        # Se il votante non ha ancora un cookie o non esiste nel DB
    if not voter_identifier or not Voter.query.filter_by(identifier=voter_identifier).first():
        if request.method == 'POST':
            nickname = request.form.get('nickname')
            if not nickname:
                flash('Devi inserire un nickname per votare!', 'warning')
                return render_template('nickname_entry.html', costume=costume)

            # genera un ID univoco e salva nel DB
            voter_identifier = str(uuid.uuid4())
            new_voter = Voter(identifier=voter_identifier, nickname=nickname)
            db.session.add(new_voter)
            db.session.commit()

            # imposta cookie
            response = make_response(redirect(url_for('vote_page', costumeId=costume_id)))
            response.set_cookie('voter_id', voter_identifier, max_age=3600*24*30, httponly=True, samesite='Lax')
            return response

        # Se GET -> mostra il form per il nickname
        return render_template('nickname_entry.html', costume=costume)

    # Se già registrato, mostra la pagina di voto
    response = make_response(render_template('vote_page.html', costume=costume))
    return response

@app.route('/vote/<string:costume_id>', methods=['POST'])
def submit_vote(costume_id):
    voter_identifier = request.cookies.get('voter_id')

    if not voter_identifier:
        flash('Impossibile identificare il tuo voto. Assicurati che i cookie siano abilitati.', 'danger')
        return redirect(url_for('vote_page', costumeId=costume_id))

    costume = Costume.query.get(costume_id)
    if not costume:
        flash('Costume non trovato.', 'danger')
        return redirect(url_for('index'))

    # Controlla se il votante ha già votato per questo costume
    existing_vote = Vote.query.filter_by(costume_id=costume_id, voter_identifier=voter_identifier).first()
    if existing_vote:
        flash('Hai già votato per questo costume!', 'warning')
        return redirect(url_for('vote_page', costumeId=costume_id))

    new_vote = Vote(costume_id=costume_id, voter_identifier=voter_identifier)
    db.session.add(new_vote)
    db.session.commit()

    flash('Voto registrato con successo!', 'success')
    return redirect(url_for('vote_page', costumeId=costume_id))


@app.route('/results', methods=['GET', 'POST'])
def results():
    # Questo è il PIN definito nel tuo .env (o config.py)
    CORRECT_PIN = os.getenv("RESULTS_PIN", "0000") # Usa un default se non trovato

    # Controlla se il PIN è già nella sessione (significa che è stato inserito correttamente)
    if 'results_access_granted' in session and session['results_access_granted']:
        # L'utente ha già inserito il PIN, mostra i risultati
        costumes = Costume.query.all()
        results_data = []
        for costume in costumes:
            votes = Vote.query.filter_by(costume_id=costume.id).all()
            vote_details = []
            for vote in votes:
                voter = Voter.query.filter_by(identifier=vote.voter_identifier).first()
                vote_details.append(voter.nickname if voter else "Anonimo")
            results_data.append({
                "name": costume.name,
                "vote_count": len(votes),
                "voters": vote_details
            })
        results_data.sort(key=lambda x: x['vote_count'], reverse=True)
        return render_template('results.html', results=results_data)
    
    # Se non ha il permesso, mostra il form per il PIN
    if request.method == 'POST':
        entered_pin = request.form.get('pin')
        if entered_pin == CORRECT_PIN:
            session['results_access_granted'] = True # Concedi l'accesso per la sessione
            flash('PIN corretto! Accesso alla classifica concesso.', 'success')
            return redirect(url_for('results')) # Reindirizza alla stessa pagina per mostrare i risultati
        else:
            flash('PIN errato. Riprova.', 'danger')
            return render_template('results_pin_entry.html') # Ritorna al form se il PIN è sbagliato
    
    # Se è una richiesta GET e non ha il permesso, mostra il form per il PIN
    return render_template('results_pin_entry.html')

