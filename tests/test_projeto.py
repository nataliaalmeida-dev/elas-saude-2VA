import unittest
from datetime import datetime
from app import create_app
from app.models import db, User, Professional, Appointment
from app.patterns import ContextoValidador, ValidacaoHorarioComercial, obter_estado_contexto

class ElasSaudeTestSuite(unittest.TestCase):

    def setUp(self):
        """Configura o ambiente isolado para cada execução de teste usando banco em memória."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        # Usamos SQLite em memória para os testes rodarem instantaneamente sem poluir o PostgreSQL real
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        """Limpa o banco de dados e encerra o contexto após cada teste."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # =========================================================================
    # BLOCO 1: TESTES DOS PADRÕES DE PROJETO COMPORTAMENTAIS (10 TESTES / ASSERÇÕES)
    # =========================================================================
    def test_padroes_comportamentais(self):
        # --- Testando o Padrão STRATEGY ---
        validador = ContextoValidador(ValidacaoHorarioComercial())
        
        # 1. Horário comercial válido (10:00)
        valido_comercial, msg1 = validador.executar(datetime(2026, 5, 20, 10, 0, 0))
        self.assertTrue(valido_comercial)
        
        # 2. Mensagem de erro deve ser vazia em caso de sucesso
        self.assertEqual(msg1, "")
        
        # 3. Horário inválido antes do expediente (06:00 da manhã)
        invalido_cedo, msg2 = validador.executar(datetime(2026, 5, 20, 6, 0, 0))
        self.assertFalse(invalido_cedo)
        
        # 4. Mensagem de erro deve alertar sobre o horário permitido
        self.assertIn("horário comercial", msg2)
        
        # 5. Horário inválido tarde da noite (23:00)
        invalido_noite, msg3 = validador.executar(datetime(2026, 5, 20, 23, 0, 0))
        self.assertFalse(invalido_noite)

        # --- Testando o Padrão STATE ---
        appt = Appointment(status='agendado')
        
        # 6. Mapeamento do estado inicial 'agendado' deve retornar a classe correta
        estado_agendado = obter_estado_contexto(appt.status)
        self.assertEqual(estado_agendado.__class__.__name__, "EstadoAgendado")
        
        # 7. Cancelar um agendamento inicial deve mudar o status para 'cancelado'
        estado_agendado.cancelar(appt)
        self.assertEqual(appt.status, 'cancelado')
        
        # 8. Mapeamento do estado 'concluido' deve retornar a classe correta
        appt.status = 'concluido'
        estado_concluido = obter_estado_contexto(appt.status)
        self.assertEqual(estado_concluido.__class__.__name__, "EstadoConcluido")
        
        # 9. Tentar cancelar uma consulta concluída deve disparar um erro (regra de negócio do State)
        with self.assertRaises(ValueError):
            estado_concluido.cancelar(appt)
            
        # 10. Mapeamento de um estado desconhecido ou padrão 'cancelado'
        estado_cancelado = obter_estado_contexto('cancelado')
        self.assertEqual(estado_cancelado.__class__.__name__, "EstadoCancelado")


    # =========================================================================
    # BLOCO 2: TESTES DE MODELOS, VALIDAÇÕES E BANCO DE DADOS (10 TESTES / ASSERÇÕES)
    # =========================================================================
    def test_modelos_e_banco_de_dados(self):
        # Criando instâncias de teste
        user = User(nome="Ana Costa", cpf="11122233344", email="ana@elas.com", senha_hash="pbkdf2...")
        prof = Professional(nome="Dra. Juliana", area="Ginecologia", crm="CRM-PE 9999")
        
        db.session.add(user)
        db.session.add(prof)
        db.session.commit()

        # 11. Verificação se o ID do usuário foi gerado corretamente pelo banco
        self.assertIsNotNone(user.id)
        
        # 12. Verificação se o ID do profissional foi gerado corretamente pelo banco
        self.assertIsNotNone(prof.id)
        
        # 13. Verificação do valor padrão do campo administrativo
        self.assertFalse(user.is_admin)
        
        # 14. Verificação se a data de criação do usuário foi preenchida automaticamente
        self.assertIsNotNone(user.criado_em)

        # Criando um agendamento associando ambos
        agenda = Appointment(paciente_id=user.id, profissional_id=prof.id, data_hora=datetime(2026, 6, 1, 14, 0), status='agendado')
        db.session.add(agenda)
        db.session.commit()

        # 15. Verificação se o relacionamento de agendamentos no usuário funciona
        self.assertEqual(len(user.agendamentos), 1)
        
        # 16. Verificação se o relacionamento de agendamentos no profissional funciona
        self.assertEqual(len(prof.agendamentos), 1)
        
        # 17. Verificação da integridade da chave estrangeira do paciente
        self.assertEqual(user.agendamentos[0].paciente_id, user.id)
        
        # 18. Verificação da integridade da chave estrangeira do profissional
        self.assertEqual(prof.agendamentos[0].profissional_id, prof.id)
        
        # 19. Verificação se as propriedades do relacionamento (backref) trazem os dados corretos
        self.assertEqual(agenda.profissional.nome, "Dra. Juliana")
        
        # 20. Verificação se o status padrão foi gravado corretamente no banco
        self.assertEqual(agenda.status, 'agendado')


    # =========================================================================
    # BLOCO 3: TESTES DE ROTAS, AUTENTICAÇÃO E INTEGRAÇÃO (10 TESTES / ASSERÇÕES)
    # =========================================================================
    def test_rotas_e_integracao(self):
        # 21. A rota da página inicial (Login) deve responder com sucesso (Status 200)
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        
        # 22. A página de listagem de profissionais deve estar acessível publicamente
        res_profs = self.client.get('/profissionais')
        self.assertEqual(res_profs.status_code, 200)
        
        # 23. A página de perfil exige login, logo deve redirecionar (Status 302)
        res_perfil = self.client.get('/perfil')
        self.assertEqual(res_perfil.status_code, 302)
        
        # 24. A página de gerenciamento administrativo exige login e redireciona anonimos
        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 302)
        
        # 25. Envio do formulário de cadastro de usuário válido via POST
        res_cadastro = self.client.post('/cadastrar', data=dict(
            nome="Carla Lima", cpf="555.555.555-55", email="carla@elas.com",
            telefone="988887777", nascimento="1990-01-01", senha="123", senha2="123"
        ))
        # Cadastro com sucesso redireciona para a tela inicial
        self.assertEqual(res_cadastro.status_code, 302)
        
        # 26. Verificação se o usuário realmente entrou no banco após a requisição POST
        usuario_salvo = User.query.filter_by(email="carla@elas.com").first()
        self.assertIsNotNone(usuario_salvo)
        
        # 27. Verificação se o nome foi gravado de forma correta via formulário
        self.assertEqual(usuario_salvo.nome, "Carla Lima")
        
        # 28. Tentativa de cadastro com senhas divergentes deve falhar/redirecionar
        res_falha_senha = self.client.post('/cadastrar', data=dict(
            nome="Invalido", cpf="000", email="erro@elas.com", senha="123", senha2="999"
        ))
        self.assertEqual(res_falha_senha.status_code, 302)
        
        # 29. Requisição de agendamento por API (POST) sem estar logado deve retornar erro 401
        res_agenda_bloqueada = self.client.post('/agendar', json=dict(profissional_id=1, data_hora="2026-06-01 14:00:00"))
        self.assertEqual(res_agenda_bloqueada.status_code, 401)
        
        # 30. A rota de recuperação de senha deve carregar com sucesso
        res_recuperar = self.client.get('/recuperar-senha')
        self.assertEqual(res_recuperar.status_code, 200)

if __name__ == '__main__':
    unittest.main()