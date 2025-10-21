from app import app, db
import os

# Creazione delle directory se non esistono
with app.app_context():
    # Crea il database e le tabelle se non esistono
    db.create_all()

    # Crea la directory per i QR code se non esiste
    qr_dir = os.path.join(app.root_path, 'static', 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    
    # Crea la directory per i CSS se non esiste
    css_dir = os.path.join(app.root_path, 'static', 'css')
    os.makedirs(css_dir, exist_ok=True)

# Questo blocco verrà eseguito solo quando run.py è chiamato direttamente,
# non quando Gunicorn avvia l'app.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')