import textwrap
from datetime import datetime
import pytz
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

# Exceções personalizadas
class BancoException(Exception):
    pass

class SaldoInsuficienteException(BancoException):
    pass

class LimiteSaqueException(BancoException):
    pass

class ValorInvalidoException(BancoException):
    pass

class ContaNaoEncontradaException(BancoException):
    pass

# Entidades do domínio
class Usuario:
    def __init__(self, nome: str, data_nascimento: str, cpf: str, endereco: str):
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
        self.endereco = endereco
        
    def to_dict(self) -> Dict:
        return {
            "nome": self.nome,
            "data_nascimento": self.data_nascimento,
            "cpf": self.cpf,
            "endereco": self.endereco
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Usuario':
        return cls(
            nome=data["nome"],
            data_nascimento=data["data_nascimento"],
            cpf=data["cpf"],
            endereco=data["endereco"]
        )

class Transacao:
    def __init__(self, tipo: str, valor: float, descricao: str = ""):
        self.tipo = tipo
        self.valor = valor
        self.data = datetime.now(pytz.timezone('America/Sao_Paulo'))
        self.descricao = descricao
        
    def to_dict(self) -> Dict:
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "data": self.data.strftime("%d/%m/%Y %H:%M:%S"),
            "descricao": self.descricao
        }

class Conta:
    def __init__(self, agencia: str, numero: int, usuario: Usuario):
        self.agencia = agencia
        self.numero = numero
        self.usuario = usuario
        self.saldo = 0.0
        self.transacoes: List[Transacao] = []
        self.saques_realizados = 0
        
    def depositar(self, valor: float):
        if valor <= 0:
            raise ValorInvalidoException("Valor de depósito deve ser positivo")
        
        self.saldo += valor
        transacao = Transacao("Depósito", valor)
        self.transacoes.append(transacao)
        
    def sacar(self, valor: float, limite: float, limite_saques: int):
        if valor <= 0:
            raise ValorInvalidoException("Valor de saque deve ser positivo")
        if valor > self.saldo:
            raise SaldoInsuficienteException("Saldo insuficiente")
        if valor > limite:
            raise LimiteSaqueException(f"Valor excede o limite de R$ {limite:.2f} por saque")
        if self.saques_realizados >= limite_saques:
            raise LimiteSaqueException(f"Número máximo de {limite_saques} saques excedido")
        
        self.saldo -= valor
        self.saques_realizados += 1
        transacao = Transacao("Saque", -valor)
        self.transacoes.append(transacao)
        
    def transferir(self, valor: float, conta_destino: 'Conta', descricao: str = ""):
        if valor <= 0:
            raise ValorInvalidoException("Valor de transferência deve ser positivo")
        if valor > self.saldo:
            raise SaldoInsuficienteException("Saldo insuficiente")
        
        self.saldo -= valor
        conta_destino.saldo += valor
        
        transacao_origem = Transacao("Transferência Enviada", -valor, f"Para: {conta_destino}")
        transacao_destino = Transacao("Transferência Recebida", valor, f"De: {self}")
        
        self.transacoes.append(transacao_origem)
        conta_destino.transacoes.append(transacao_destino)
        
    def obter_extrato(self) -> List[Dict]:
        return [transacao.to_dict() for transacao in self.transacoes]
    
    def __str__(self):
        return f"Ag: {self.agencia} C/C: {self.numero} - {self.usuario.nome}"
    
    def to_dict(self) -> Dict:
        return {
            "agencia": self.agencia,
            "numero": self.numero,
            "usuario": self.usuario.to_dict(),
            "saldo": self.saldo,
            "saques_realizados": self.saques_realizados,
            "transacoes": [t.to_dict() for t in self.transacoes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict, usuario: Usuario) -> 'Conta':
        conta = cls(
            agencia=data["agencia"],
            numero=data["numero"],
            usuario=usuario
        )
        conta.saldo = data["saldo"]
        conta.saques_realizados = data["saques_realizados"]
        conta.transacoes = [Transacao(t["tipo"], t["valor"], t.get("descricao", "")) for t in data["transacoes"]]
        return conta

# Interfaces de repositório
class UsuarioRepository(ABC):
    @abstractmethod
    def adicionar(self, usuario: Usuario) -> None:
        pass
    
    @abstractmethod
    def buscar_por_cpf(self, cpf: str) -> Optional[Usuario]:
        pass
    
    @abstractmethod
    def listar_todos(self) -> List[Usuario]:
        pass

class ContaRepository(ABC):
    @abstractmethod
    def adicionar(self, conta: Conta) -> None:
        pass
    
    @abstractmethod
    def buscar_por_numero(self, numero: int) -> Optional[Conta]:
        pass
    
    @abstractmethod
    def buscar_por_agencia_numero(self, agencia: str, numero: int) -> Optional[Conta]:
        pass
    
    @abstractmethod
    def listar_por_usuario(self, cpf: str) -> List[Conta]:
        pass
    
    @abstractmethod
    def listar_todas(self) -> List[Conta]:
        pass
    
    @abstractmethod
    def proximo_numero(self) -> int:
        pass

# Implementações em memória
class UsuarioRepositoryMemory(UsuarioRepository):
    def __init__(self):
        self.usuarios: Dict[str, Usuario] = {}
    
    def adicionar(self, usuario: Usuario) -> None:
        if usuario.cpf in self.usuarios:
            raise BancoException("Já existe usuário com este CPF")
        self.usuarios[usuario.cpf] = usuario
    
    def buscar_por_cpf(self, cpf: str) -> Optional[Usuario]:
        return self.usuarios.get(cpf)
    
    def listar_todos(self) -> List[Usuario]:
        return list(self.usuarios.values())

class ContaRepositoryMemory(ContaRepository):
    def __init__(self):
        self.contas: Dict[str, Conta] = {}  # Chave: "agencia:numero"
        self.ultimo_numero = 0
    
    def adicionar(self, conta: Conta) -> None:
        chave = f"{conta.agencia}:{conta.numero}"
        if chave in self.contas:
            raise BancoException("Conta já existe")
        self.contas[chave] = conta
        if conta.numero > self.ultimo_numero:
            self.ultimo_numero = conta.numero
    
    def buscar_por_numero(self, numero: int) -> Optional[Conta]:
        for conta in self.contas.values():
            if conta.numero == numero:
                return conta
        return None
    
    def buscar_por_agencia_numero(self, agencia: str, numero: int) -> Optional[Conta]:
        chave = f"{agencia}:{numero}"
        return self.contas.get(chave)
    
    def listar_por_usuario(self, cpf: str) -> List[Conta]:
        return [conta for conta in self.contas.values() if conta.usuario.cpf == cpf]
    
    def listar_todas(self) -> List[Conta]:
        return list(self.contas.values())
    
    def proximo_numero(self) -> int:
        self.ultimo_numero += 1
        return self.ultimo_numero

# Serviços de aplicação
class UsuarioService:
    def __init__(self, usuario_repo: UsuarioRepository):
        self.usuario_repo = usuario_repo
    
    def cadastrar_usuario(self, nome: str, data_nascimento: str, cpf: str, endereco: str) -> Usuario:
        # Validações
        if not self.validar_cpf(cpf):
            raise BancoException("CPF inválido")
        
        if not self.validar_data_nascimento(data_nascimento):
            raise BancoException("Data de nascimento inválida. Use o formato dd-mm-aaaa")
        
        # Criar usuário
        usuario = Usuario(nome, data_nascimento, cpf, endereco)
        self.usuario_repo.adicionar(usuario)
        return usuario
    
    def buscar_usuario(self, cpf: str) -> Optional[Usuario]:
        return self.usuario_repo.buscar_por_cpf(cpf)
    
    def listar_usuarios(self) -> List[Usuario]:
        return self.usuario_repo.listar_todos()
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula o primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula o segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        # Verifica se os dígitos calculados conferem com os informados
        return int(cpf[9]) == digito1 and int(cpf[10]) == digito2
    
    @staticmethod
    def validar_data_nascimento(data: str) -> bool:
        try:
            datetime.strptime(data, '%d-%m-%Y')
            return True
        except ValueError:
            return False

class ContaService:
    def __init__(self, conta_repo: ContaRepository, usuario_repo: UsuarioRepository):
        self.conta_repo = conta_repo
        self.usuario_repo = usuario_repo
    
    def criar_conta(self, agencia: str, cpf: str) -> Conta:
        usuario = self.usuario_repo.buscar_por_cpf(cpf)
        if not usuario:
            raise BancoException("Usuário não encontrado")
        
        numero = self.conta_repo.proximo_numero()
        conta = Conta(agencia, numero, usuario)
        self.conta_repo.adicionar(conta)
        return conta
    
    def buscar_conta(self, agencia: str, numero: int) -> Optional[Conta]:
        return self.conta_repo.buscar_por_agencia_numero(agencia, numero)
    
    def listar_contas(self) -> List[Conta]:
        return self.conta_repo.listar_todas()
    
    def listar_contas_por_usuario(self, cpf: str) -> List[Conta]:
        return self.conta_repo.listar_por_usuario(cpf)

class OperacaoBancariaService:
    def __init__(self, conta_repo: ContaRepository):
        self.conta_repo = conta_repo
        self.limite_saque = 500
        self.limite_saques_diarios = 3
    
    def depositar(self, agencia: str, numero: int, valor: float):
        conta = self.conta_repo.buscar_por_agencia_numero(agencia, numero)
        if not conta:
            raise ContaNaoEncontradaException("Conta não encontrada")
        
        conta.depositar(valor)
    
    def sacar(self, agencia: str, numero: int, valor: float):
        conta = self.conta_repo.buscar_por_agencia_numero(agencia, numero)
        if not conta:
            raise ContaNaoEncontradaException("Conta não encontrada")
        
        conta.sacar(valor, self.limite_saque, self.limite_saques_diarios)
    
    def transferir(self, agencia_origem: str, numero_origem: int, 
                  agencia_destino: str, numero_destino: str, valor: float):
        conta_origem = self.conta_repo.buscar_por_agencia_numero(agencia_origem, numero_origem)
        if not conta_origem:
            raise ContaNaoEncontradaException("Conta de origem não encontrada")
        
        conta_destino = self.conta_repo.buscar_por_agencia_numero(agencia_destino, numero_destino)
        if not conta_destino:
            raise ContaNaoEncontradaException("Conta de destino não encontrada")
        
        conta_origem.transferir(valor, conta_destino)
    
    def obter_extrato(self, agencia: str, numero: int) -> List[Dict]:
        conta = self.conta_repo.buscar_por_agencia_numero(agencia, numero)
        if not conta:
            raise ContaNaoEncontradaException("Conta não encontrada")
        
        return conta.obter_extrato()

# Interface de usuário
class BancoInterface:
    def __init__(self):
        self.usuario_repo = UsuarioRepositoryMemory()
        self.conta_repo = ContaRepositoryMemory()
        
        self.usuario_service = UsuarioService(self.usuario_repo)
        self.conta_service = ContaService(self.conta_repo, self.usuario_repo)
        self.operacao_service = OperacaoBancariaService(self.conta_repo)
        
        self.agencia = "0001"
        self.conta_atual = None
    
    def menu_principal(self):
        menu_text = """\n
        ================ MENU PRINCIPAL ================
        [1]\tAcessar Conta
        [2]\tCadastrar Usuário
        [3]\tCriar Conta
        [4]\tListar Contas
        [5]\tListar Usuários
        [q]\tSair
        => """
        return input(textwrap.dedent(menu_text))
    
    def menu_conta(self):
        menu_text = """\n
        ================ MENU DA CONTA ================
        [d]\tDepositar
        [s]\tSacar
        [e]\tExtrato
        [t]\tTransferência
        [q]\tVoltar ao menu principal
        => """
        return input(textwrap.dedent(menu_text))
    
    def acessar_conta(self):
        numero = int(input("Informe o número da conta: "))
        conta = self.conta_service.buscar_conta(self.agencia, numero)
        
        if not conta:
            print("\n@@@ Conta não encontrada! @@@")
            return
        
        self.conta_atual = conta
        print(f"\n=== Conta {conta.numero} acessada com sucesso! ===")
        self.menu_operacoes_conta()
    
    def menu_operacoes_conta(self):
        while self.conta_atual:
            opcao = self.menu_conta()
            
            if opcao == "d":
                self.depositar()
            elif opcao == "s":
                self.sacar()
            elif opcao == "e":
                self.exibir_extrato()
            elif opcao == "t":
                self.transferir()
            elif opcao == "q":
                self.conta_atual = None
                print("\n=== Retornando ao menu principal ===")
            else:
                print("\n@@@ Operação inválida! @@@")
    
    def depositar(self):
        try:
            valor = float(input("Informe o valor do depósito: "))
            self.operacao_service.depositar(self.agencia, self.conta_atual.numero, valor)
            print(f"\n=== Depósito de R$ {valor:.2f} realizado com sucesso! ===")
            print(f"Novo saldo: R$ {self.conta_atual.saldo:.2f}")
        except (ValorInvalidoException, ContaNaoEncontradaException) as e:
            print(f"\n@@@ {e} @@@")
        except ValueError:
            print("\n@@@ Valor inválido! @@@")
    
    def sacar(self):
        try:
            valor = float(input("Informe o valor do saque: "))
            self.operacao_service.sacar(self.agencia, self.conta_atual.numero, valor)
            print(f"\n=== Saque de R$ {valor:.2f} realizado com sucesso! ===")
            print(f"Novo saldo: R$ {self.conta_atual.saldo:.2f}")
        except (ValorInvalidoException, SaldoInsuficienteException, 
                LimiteSaqueException, ContaNaoEncontradaException) as e:
            print(f"\n@@@ {e} @@@")
        except ValueError:
            print("\n@@@ Valor inválido! @@@")
    
    def exibir_extrato(self):
        try:
            transacoes = self.operacao_service.obter_extrato(self.agencia, self.conta_atual.numero)
            
            print("\n================ EXTRATO ================")
            if not transacoes:
                print("Não foram realizadas movimentações.")
            else:
                for transacao in transacoes:
                    sinal = "+" if transacao["valor"] >= 0 else "-"
                    print(f"{transacao['tipo']}: {sinal}R$ {abs(transacao['valor']):.2f} "
                          f"em {transacao['data']} {transacao.get('descricao', '')}")
            
            print(f"\nSaldo atual: R$ {self.conta_atual.saldo:.2f}")
            print("==========================================")
        except ContaNaoEncontradaException as e:
            print(f"\n@@@ {e} @@@")
    
    def transferir(self):
        try:
            agencia_destino = input("Informe a agência de destino: ")
            numero_destino = int(input("Informe o número da conta de destino: "))
            valor = float(input("Informe o valor para transferência: "))
            
            self.operacao_service.transferir(
                self.agencia, self.conta_atual.numero,
                agencia_destino, numero_destino, valor
            )
            
            print(f"\n=== Transferência de R$ {valor:.2f} realizada com sucesso! ===")
            print(f"Para: Agência {agencia_destino}, Conta {numero_destino}")
            print(f"Novo saldo: R$ {self.conta_atual.saldo:.2f}")
        except (ValorInvalidoException, SaldoInsuficienteException, 
                ContaNaoEncontradaException) as e:
            print(f"\n@@@ {e} @@@")
        except ValueError:
            print("\n@@@ Valor inválido! @@@")
    
    def cadastrar_usuario(self):
        try:
            nome = input("Informe o nome completo: ")
            data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
            cpf = input("Informe o CPF (somente número): ")
            endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")
            
            usuario = self.usuario_service.cadastrar_usuario(nome, data_nascimento, cpf, endereco)
            print(f"\n=== Usuário {usuario.nome} criado com sucesso! ===")
        except BancoException as e:
            print(f"\n@@@ {e} @@@")
    
    def criar_conta(self):
        try:
            cpf = input("Informe o CPF do usuário: ")
            conta = self.conta_service.criar_conta(self.agencia, cpf)
            print(f"\n=== Conta criada com sucesso! ===")
            print(f"Agência: {conta.agencia} | Conta: {conta.numero} | Titular: {conta.usuario.nome}")
        except BancoException as e:
            print(f"\n@@@ {e} @@@")
    
    def listar_contas(self):
        contas = self.conta_service.listar_contas()
        
        if not contas:
            print("\n@@@ Nenhuma conta cadastrada! @@@")
            return
        
        print("\n================ CONTAS ================")
        for conta in contas:
            print(f"Agência: {conta.agencia} | Conta: {conta.numero} | Titular: {conta.usuario.nome} | Saldo: R$ {conta.saldo:.2f}")
        print("========================================")
    
    def listar_usuarios(self):
        usuarios = self.usuario_service.listar_usuarios()
        
        if not usuarios:
            print("\n@@@ Nenhum usuário cadastrado! @@@")
            return
        
        print("\n================ USUÁRIOS ================")
        for usuario in usuarios:
            print(f"Nome: {usuario.nome} | CPF: {usuario.cpf} | Nascimento: {usuario.data_nascimento}")
        print("===========================================")
    
    def executar(self):
        while True:
            opcao = self.menu_principal()
            
            if opcao == "1":
                self.acessar_conta()
            elif opcao == "2":
                self.cadastrar_usuario()
            elif opcao == "3":
                self.criar_conta()
            elif opcao == "4":
                self.listar_contas()
            elif opcao == "5":
                self.listar_usuarios()
            elif opcao == "q":
                print("\n=== Obrigado por usar nosso sistema bancário! ===")
                break
            else:
                print("\n@@@ Operação inválida! @@@")

# Ponto de entrada principal
if __name__ == "__main__":
    banco = BancoInterface()
    banco.executar()
