from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import secrets, os
from datetime import datetime
from scripts.code10 import load_env_with_password
from scripts.code20 import decrypt_entry,encrypt_and_store_entry

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'attempts' not in session:
        session['attempts'] = 0

    if request.method == 'POST':
        env_password = request.form.get('env_password', '').strip()

        try:
            env = load_env_with_password(env_password)
            # Нормализуем ключи и значения
            env = {k.strip(): v.strip().strip('"').strip("'") for k, v in env.items()}
        except Exception as e:
            session['attempts'] += 1
            return f"Ошибка при расшифровке env: {e}"

        password = request.form.get('password', '').strip()

        if password == env.get("PASSWORD"):
            session['authenticated'] = True
            session['env'] = env
            session.pop('attempts', None)
            return redirect(url_for('home'))
        else:
            session['attempts'] += 1
            print("Введено:", password)
            print("Из env:", env.get("PASSWORD"))
            if session['attempts'] >= 3:
                return "Доступ заблокирован. Превышено количество попыток."

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    return render_template('index.html')

@app.route('/api/entries')
def api_entries():
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401

    env = session.get('env')
    entries = decrypt_entry(env)  # список словарей
    # Убедимся, что формат правильный: список словарей с ключами id, entry, dateandtime
    return jsonify(entries)


@app.route('/write', methods=['GET', 'POST'])
def write_entry():
    if not session.get('authenticated'):
        return redirect('login')

    if request.method == 'POST':
        env = session['env']
        entry = request.form.get('entry')
        dateandtime = datetime.now().strftime("%d.%m.%Y %H:%M")
        encrypt_and_store_entry(dateandtime,entry,env)

    return render_template('write.html')


if __name__ == "__main__":
    app.run()
