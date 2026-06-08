from abc import ABC, abstractmethod

# =====================================================================
# 1. PADRÃO COMPORTAMENTAL: STRATEGY
# Define algoritmos intercambiáveis para validar o horário do agendamento
# =====================================================================
class ValidationStrategy(ABC):
    @abstractmethod
    def validar(self, data_hora):
        pass

class ValidacaoHorarioComercial(ValidationStrategy):
    """Estratégia padrão: Consultas normais apenas em horário comercial (08h às 18h)"""
    def validar(self, data_hora):
        if data_hora.hour < 8 or data_hora.hour > 18:
            return False, "Agendamentos comuns só são permitidos em horário comercial (08h às 18h)."
        return True, ""

class ValidacaoPlantaoUrgente(ValidationStrategy):
    """Estratégia alternativa: Casos urgentes/plantões permitem qualquer horário"""
    def validar(self, data_hora):
        return True, ""

class ContextoValidador:
    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy

    def executar(self, data_hora):
        return self._strategy.validar(data_hora)


# =====================================================================
# 2. PADRÃO COMPORTAMENTAL: STATE
# Permite que o agendamento mude seu comportamento quando o status altera
# =====================================================================
class AppointmentState(ABC):
    @abstractmethod
    def cancelar(self, appointment):
        pass

class EstadoAgendado(AppointmentState):
    def cancelar(self, appointment):
        # Se está apenas agendado, muda para cancelado normalmente
        appointment.status = 'cancelado'

class EstadoConcluido(AppointmentState):
    def cancelar(self, appointment):
        # Regra de negócio: Uma consulta que já aconteceu não pode ser cancelada
        raise ValueError("Não é possível cancelar uma consulta que já foi concluída.")

class EstadoCancelado(AppointmentState):
    def cancelar(self, appointment):
        # Se já está cancelado, não faz nada
        pass

def obter_estado_contexto(status_string):
    """Fábrica simples para mapear a string do banco para a classe do Estado"""
    mapeamento = {
        'agendado': EstadoAgendado(),
        'concluido': EstadoConcluido(),
        'cancelado': EstadoCancelado()
    }
    return mapeamento.get(status_string, EstadoAgendado())