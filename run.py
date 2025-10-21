from app import app, db
from app.models import User
import os

# Funzione per inizializzare il database e creare l'utente admin
def init_db_and_admin():
    with app.app_context():
        db.create_all() # Crea tutte le tabelle definite nei modelli

        # Crea un utente admin predefinito se non esiste
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin')
            admin_user.set_password('Dedee__001') 
            db.session.commit()
            print("Utente 'admin' creato con password 'adminpassword'. CAMBIALA!")
        else:
            print("Utente 'admin' esiste già.")

        # Assicurati che le directory per i file statici esistano
        qr_dir = os.path.join(app.root_path, 'static', 'qr_codes')
        os.makedirs(qr_dir, exist_ok=True)
        
        css_dir = os.path.join(app.root_path, 'static', 'css')
        os.makedirs(css_dir, exist_ok=True)
        print("Directory statiche verificate/create.")

# Questo blocco avvia l'app in locale.
# Render userà il Procfile per avviare Gunicorn, che non passa per questo blocco.
if __name__ == '__main__':
    # Esegui l'inizializzazione del DB solo all'avvio locale diretto
    init_db_and_admin()
    app.run(debug=True, host='0.0.0.0')