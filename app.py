from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_super_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ----------------- Models -----------------

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    username = db.Column(db.String(150), unique=True)
    senha_hash = db.Column(db.String(200))

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    quantidade = db.Column(db.Integer)


class Retirada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    quantidade = db.Column(db.Integer)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
    produto = db.relationship('Produto')

# ----------------- Login -----------------

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ----------------- Rotas -----------------

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.check_password(senha):
            login_user(usuario)
            return redirect(url_for('estoque'))
        else:
            flash('Usuário ou senha incorretos')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/estoque')
@login_required
def estoque():
    produtos = Produto.query.all()
    return render_template('estoque.html', produtos=produtos)


@app.route('/retirada/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def retirada(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if request.method == 'POST':
        quantidade = int(request.form['quantidade'])
        if quantidade <= 0 or quantidade > produto.quantidade:
            flash('Quantidade inválida')
            return redirect(url_for('retirada', produto_id=produto.id))

        produto.quantidade -= quantidade
        retirada = Retirada(
            usuario_id=current_user.id,
            produto_id=produto.id,
            quantidade=quantidade
        )
        db.session.add(retirada)
        db.session.commit()
        flash('Retirada realizada com sucesso')
        return redirect(url_for('estoque'))

    return render_template('retirada.html', produto=produto)


@app.route('/historico')
@login_required
def historico():
    registros = Retirada.query.order_by(Retirada.data_hora.desc()).all()
    return render_template('historico.html', registros=registros)


@app.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = int(request.form['quantidade'])
        produto = Produto(nome=nome, quantidade=quantidade)
        db.session.add(produto)
        db.session.commit()
        flash('Produto cadastrado com sucesso')
        return redirect(url_for('estoque'))

    return render_template('cadastro_produto.html')

# ----------------- Rodar App e Criar Banco -----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
