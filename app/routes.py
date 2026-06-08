import os, re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from . import db
from .models import User, Professional, Appointment
# Adicione esta linha no topo do seu routes.py junto com os outros imports
from .patterns import ContextoValidador, ValidacaoHorarioComercial, obter_estado_contexto

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        usuario = User.query.filter_by(email=email).first()

        if not usuario or not check_password_hash(usuario.senha_hash, password):
            flash("E-mail ou senha inválidos.", "error")
            return redirect(url_for('main.index'))
        
        session['usuario_id'] = usuario.id
        return redirect(url_for('main.profissionais'))

    return render_template('index.html')

@bp.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():  
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        nascimento = request.form.get('nascimento')
        senha = request.form.get('senha')
        senha2 = request.form.get('senha2')

        if senha != senha2:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('main.cadastrar'))

        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "error")
            return redirect(url_for('main.cadastrar'))
            
        foto = request.files.get('foto')
        if foto and foto.filename:
            cpf_limpo = re.sub(r'\D', '', cpf)
            os.makedirs('static/assets/usuario', exist_ok=True)
            foto.save(f'static/assets/usuario/{cpf_limpo}.png')

        nascimento_date = datetime.strptime(nascimento, '%Y-%m-%d').date() if nascimento else None

        novo_usuario = User(
            nome=nome,
            cpf=cpf,
            email=email,
            telefone=telefone,
            nascimento=nascimento_date,
            senha_hash=generate_password_hash(senha)
        )
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for('main.index'))
    return render_template('cadastrar.html')

@bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para editar seu perfil.", "error")
        return redirect(url_for('main.index'))
        
    usuario = User.query.get(session['usuario_id'])
    
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.telefone = request.form.get('telefone')
        nascimento = request.form.get('nascimento')
        usuario.nascimento = datetime.strptime(nascimento, '%Y-%m-%d').date() if nascimento else None
        
        senha = request.form.get('senha')
        senha2 = request.form.get('senha2')
        if senha and senha == senha2:
            usuario.senha_hash = generate_password_hash(senha)
            
        foto = request.files.get('foto')
        remover_foto = request.form.get('remover_foto')
        cpf_limpo = re.sub(r'\D', '', usuario.cpf)
        caminho_foto = os.path.join('static', 'assets', 'usuario', f'{cpf_limpo}.png')
        
        if remover_foto == '1':
            if os.path.exists(caminho_foto):
                try: os.remove(caminho_foto)
                except: pass
        elif foto and foto.filename:
            os.makedirs('static/assets/usuario', exist_ok=True)
            foto.save(caminho_foto)
            
        db.session.commit()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('main.perfil'))
        
    return render_template('perfil.html', usuario=usuario)

@bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    return render_template('recuperar-senha.html')

@bp.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if 'usuario_id' not in session:
        if request.method == 'POST':
            return {"erro": "Não autorizado"}, 401
        flash("Você precisa estar logado para agendar.", "error")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        dados = request.get_json()
        prof_id = dados.get('profissional_id')
        data_hora_str = dados.get('data_hora')
        data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S')
        
        # =====================================================================
        # -> INTEGRAÇÃO DO PADRÃO COMPORTAMENTAL: STRATEGY
        # =====================================================================
        # Instancia o contexto definindo a estratégia de Horário Comercial
        validador = ContextoValidador(ValidacaoHorarioComercial())
        eh_valido, mensagem = validador.executar(data_hora)
        
        # Se a estratégia rejeitar o horário, retorna o erro direto para o Front-end
        if not eh_valido:
            return {"erro": mensagem}, 400
        # =====================================================================
        
        novo_agendamento = Appointment(
            paciente_id=session['usuario_id'],
            profissional_id=prof_id,
            data_hora=data_hora,
            status='agendado'
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        return {"sucesso": True}

    prof_id = request.args.get('id', type=int)
    if not prof_id:
        return redirect(url_for('main.profissionais'))
    
    profissional = Professional.query.get(prof_id)
    agendamentos = Appointment.query.filter_by(profissional_id=prof_id).all()
    
    return render_template('agendar.html', profissional=profissional, agendamentos=agendamentos)

@bp.route('/agendamentos')
def agendamentos():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para ver seus agendamentos.", "error")
        return redirect(url_for('main.index'))
    
    lista_agendamentos = Appointment.query.filter_by(paciente_id=session['usuario_id']).order_by(Appointment.data_hora).all()
    return render_template('agendamentos.html', agendamentos=lista_agendamentos)

@bp.route('/cancelar_agendamento/<int:id>', methods=['POST'])
def cancelar_agendamento(id):
    if 'usuario_id' not in session:
        return {"erro": "Não autorizado"}, 401
    
    agendamento = Appointment.query.get_or_404(id)
    if agendamento.paciente_id != session['usuario_id']:
        return {"erro": "Não autorizado"}, 401
        
    # ---> APLICAÇÃO DO PADRÃO STATE <---
    # Deixamos de simplesmente deletar e passamos a gerenciar o estado do objeto
    try:
        estado_atual = obter_estado_contexto(agendamento.status)
        estado_atual.cancelar(agendamento) # O estado decide o que acontece
        db.session.commit()
        return {"sucesso": True}
    except ValueError as e:
        return {"erro": str(e)}, 400

def seed_db():
    if User.query.filter_by(email="admin@elassaude.com").first() is None:
        admin_user = User(
            nome="Administrador",
            cpf="000.000.000-00",
            email="admin@elassaude.com",
            senha_hash=generate_password_hash("admin"),
            is_admin=True
        )
        db.session.add(admin_user)

    if Professional.query.count() == 0:
        profs = [
            {"nome": "Dra. Maria Silva", "crm": "CRM-PE 54321", "area": "Ginecologia", "foto_url": "assets/usuario/usuario.png"},
            {"nome": "Dra. Ana Pereira", "crm": "CRM-PE 12345", "area": "Obstetrícia", "foto_url": "assets/usuario/usuario.png"},
            {"nome": "Dra. Carla Mendes", "crm": "CRM-PE 98765", "area": "Endocrinologia", "foto_url": "assets/usuario/usuario.png"},
            {"nome": "Dra. Maria Souza", "crm": "CRM-PE 45678", "area": "Dermatologia", "foto_url": "assets/usuario/usuario.png"}
        ]
        for p in profs:
            db.session.add(Professional(nome=p['nome'], crm=p.get('crm'), area=p['area'], foto_url=p['foto_url']))
            
    db.session.commit()

@bp.route('/profissionais')
def profissionais():
    lista_profissionais = Professional.query.all()
    return render_template('profissionais.html', profissionais=lista_profissionais)

@bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'usuario_id' not in session:
        return redirect(url_for('main.index'))
    user = User.query.get(session['usuario_id'])
    if not user.is_admin:
        return redirect(url_for('main.profissionais'))
        
    if request.method == 'POST':
        
        nome = request.form.get('nome')
        crm = request.form.get('crm')
        area = request.form.get('area')
        foto = request.files.get('foto')
        
        foto_url = "assets/usuario/usuario.png"
        if foto and foto.filename:
            fname = secure_filename(foto.filename)
            os.makedirs('static/assets/profissionais', exist_ok=True)
            foto.save(f'static/assets/profissionais/{fname}')
            foto_url = f"assets/profissionais/{fname}"
            
        pro = Professional(nome=nome, crm=crm, area=area, foto_url=foto_url)
        db.session.add(pro)
        db.session.commit()
        flash("Profissional cadastrado com sucesso!", "success")
        return redirect(url_for('main.admin'))
        
    profissionais = Professional.query.all()
    return render_template('admin.html', profissionais=profissionais)

@bp.route('/admin/delete/<int:id>', methods=['POST'])
def admin_delete(id):
    if 'usuario_id' not in session: return redirect(url_for('main.index'))
    user = User.query.get(session['usuario_id'])
    if not user.is_admin: return redirect(url_for('main.profissionais'))
    
    pro = Professional.query.get_or_404(id)
    
    # Exclui todos os agendamentos vinculados antes de deletar o profissional
    for a in pro.agendamentos:
        db.session.delete(a)
    db.session.commit()
        
    if pro.foto_url and "usuario.png" not in pro.foto_url:
        path = os.path.join('static', pro.foto_url)
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
            
    db.session.delete(pro)
    db.session.commit()
    flash("Profissional e seus agendamentos foram removidos com sucesso!", "success")
    return redirect(url_for('main.admin'))

@bp.route('/admin/cancelar_agendamento/<int:id>', methods=['POST'])
def admin_cancel_appointment(id):
    if 'usuario_id' not in session: return redirect(url_for('main.index'))
    user = User.query.get(session['usuario_id'])
    if not user.is_admin: return redirect(url_for('main.profissionais'))
    
    agendamento = Appointment.query.get_or_404(id)
    prof_id = agendamento.profissional_id
    
    db.session.delete(agendamento)
    db.session.commit()
    
    flash("Consulta cancelada com sucesso!", "success")
    return redirect(url_for('main.admin_edit', id=prof_id))

@bp.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit(id):
    if 'usuario_id' not in session: return redirect(url_for('main.index'))
    user = User.query.get(session['usuario_id'])
    if not user.is_admin: return redirect(url_for('main.profissionais'))
    
    pro = Professional.query.get_or_404(id)
    
    if request.method == 'POST':
        pro.nome = request.form.get('nome')
        pro.crm = request.form.get('crm')
        pro.area = request.form.get('area')
        remover_foto = request.form.get('remover_foto')
        foto = request.files.get('foto')
        
        if remover_foto == '1':
            if pro.foto_url and "usuario.png" not in pro.foto_url:
                old_path = os.path.join('static', pro.foto_url)
                if os.path.exists(old_path):
                    try: os.remove(old_path)
                    except: pass
            pro.foto_url = "assets/usuario/usuario.png"
            
        elif foto and foto.filename:
            if pro.foto_url and "usuario.png" not in pro.foto_url:
                old_path = os.path.join('static', pro.foto_url)
                if os.path.exists(old_path):
                    try: os.remove(old_path)
                    except: pass
                    
            fname = secure_filename(foto.filename)
            os.makedirs('static/assets/profissionais', exist_ok=True)
            foto.save(f'static/assets/profissionais/{fname}')
            pro.foto_url = f"assets/profissionais/{fname}"
            
        db.session.commit()
        flash("Profissional atualizado com sucesso!", "success")
        return redirect(url_for('main.admin'))
        
    return render_template('admin_edit.html', p=pro)

    lista_profissionais = Professional.query.all()
    return render_template('profissionais.html', profissionais=lista_profissionais)
