import textwrap
from datetime import datetime
import pytz

class SistemaBancario:
    def __init__(self):
        self.saldo = 0
        self.limite = 500
        self.extrato = ""
        self.numero_saques = 0
        self.LIMITE_SAQUES = 3
        self.usuarios = []
        self.contas = []
        self.agencia = "0001"
        self.transacoes = []

    def menu(self):
        menu = """\n
        ================ MENU ================
        [d]\tDepositar
        [s]\tSacar
        [e]\tExtrato
        [nc]\tNova conta
        [lc]\tListar contas
        [nu]\tNovo usuário
        [t]\tTransferência entre contas
        [q]\tSair
        => """
        return input(textwrap.dedent(menu))

    def depositar(self, valor):
        if valor > 0:
            self.saldo += valor
            transacao = {
                "tipo": "Depósito",
                "valor": valor,
                "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
            }
            self.transacoes.append(transacao)
            self.extrato += f"Depósito:\tR$ {valor:.2f}\n"
            print("\n=== Depósito realizado com sucesso! ===")
            print(f"Novo saldo: R$ {self.saldo:.2f}")
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

    def sacar(self, valor):
        excedeu_saldo = valor > self.saldo
        excedeu_limite = valor > self.limite
        excedeu_saques = self.numero_saques >= self.LIMITE_SAQUES

        if excedeu_saldo:
            print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
        elif excedeu_limite:
            print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
        elif excedeu_saques:
            print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
        elif valor > 0:
            self.saldo -= valor
            transacao = {
                "tipo": "Saque",
                "valor": -valor,
                "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
            }
            self.transacoes.append(transacao)
            self.extrato += f"Saque:\t\tR$ {valor:.2f}\n"
            self.numero_saques += 1
            print("\n=== Saque realizado com sucesso! ===")
            print(f"Novo saldo: R$ {self.saldo:.2f}")
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

    def exibir_extrato(self):
        print("\n================ EXTRATO ================")
        if not self.transacoes:
            print("Não foram realizadas movimentações.")
        else:
            for transacao in self.transacoes:
                print(f"{transacao['tipo']} de R$ {abs(transacao['valor']):.2f} em {transacao['data']}")
        print(f"\nSaldo atual:\tR$ {self.saldo:.2f}")
        print("==========================================")

    def criar_usuario(self):
        cpf = input("Informe o CPF (somente número): ")
        usuario = self.filtrar_usuario(cpf)

        if usuario:
            print("\n@@@ Já existe usuário com esse CPF! @@@")
            return

        nome = input("Informe o nome completo: ")
        data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
        endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

        self.usuarios.append({
            "nome": nome, 
            "data_nascimento": data_nascimento, 
            "cpf": cpf, 
            "endereco": endereco
        })

        print("=== Usuário criado com sucesso! ===")

    def filtrar_usuario(self, cpf):
        for usuario in self.usuarios:
            if usuario["cpf"] == cpf:
                return usuario
        return None

    def criar_conta(self):
        cpf = input("Informe o CPF do usuário: ")
        usuario = self.filtrar_usuario(cpf)

        if usuario:
            numero_conta = len(self.contas) + 1
            self.contas.append({
                "agencia": self.agencia,
                "numero_conta": numero_conta,
                "usuario": usuario
            })
            print("\n=== Conta criada com sucesso! ===")
            print(f"Agência: {self.agencia} | Conta: {numero_conta}")
            return

        print("\n@@@ Usuário não encontrado, fluxo de criação de conta encerrado! @@@")

    def listar_contas(self):
        if not self.contas:
            print("\n@@@ Nenhuma conta cadastrada! @@@")
            return
            
        for conta in self.contas:
            linha = f"""\
                Agência:\t{conta['agencia']}
                C/C:\t\t{conta['numero_conta']}
                Titular:\t{conta['usuario']['nome']}
            """
            print(textwrap.dedent(linha))
            print("=" * 50)

    def transferencia(self):
        print("\n=== TRANSFERÊNCIA ===")
        valor = float(input("Informe o valor para transferência: "))
        
        if valor <= 0:
            print("\n@@@ Valor inválido para transferência! @@@")
            return
            
        if valor > self.saldo:
            print("\n@@@ Saldo insuficiente para transferência! @@@")
            return
            
        destino_agencia = input("Informe a agência de destino: ")
        destino_conta = input("Informe a conta de destino: ")
        
        # Simulação de transferência
        self.saldo -= valor
        transacao = {
            "tipo": "Transferência",
            "valor": -valor,
            "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S"),
            "destino": f"Ag: {destino_agencia} C/C: {destino_conta}"
        }
        self.transacoes.append(transacao)
        self.extrato += f"Transferência:\tR$ {valor:.2f} para Ag: {destino_agencia} C/C: {destino_conta}\n"
        
        print("\n=== Transferência realizada com sucesso! ===")
        print(f"Valor transferido: R$ {valor:.2f}")
        print(f"Para: Agência {destino_agencia}, Conta {destino_conta}")
        print(f"Novo saldo: R$ {self.saldo:.2f}")

    def executar(self):
        while True:
            opcao = self.menu()

            if opcao == "d":
                valor = float(input("Informe o valor do depósito: "))
                self.depositar(valor)

            elif opcao == "s":
                valor = float(input("Informe o valor do saque: "))
                self.sacar(valor)

            elif opcao == "e":
                self.exibir_extrato()

            elif opcao == "nu":
                self.criar_usuario()

            elif opcao == "nc":
                self.criar_conta()

            elif opcao == "lc":
                self.listar_contas()
                
            elif opcao == "t":
                self.transferencia()

            elif opcao == "q":
                print("\n=== Obrigado por usar nosso sistema bancário! ===")
                break

            else:
                print("Operação inválida, por favor selecione novamente a operação desejada.")

if __name__ == "__main__":
    sistema = SistemaBancario()
    sistema.executar()
