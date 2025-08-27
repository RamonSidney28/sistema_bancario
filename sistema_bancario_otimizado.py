import textwrap
from datetime import datetime
import pytz

def menu():
    menu_text = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [nu]\tNovo usuário
    [t]\tTransferência
    [q]\tSair
    => """
    return input(textwrap.dedent(menu_text))

def depositar(saldo, valor, extrato, transacoes):
    if valor > 0:
        saldo += valor
        transacao = {
            "tipo": "Depósito",
            "valor": valor,
            "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
        }
        transacoes.append(transacao)
        extrato += f"Depósito:\tR$ {valor:.2f}\n"
        print("\n=== Depósito realizado com sucesso! ===")
        print(f"Novo saldo: R$ {saldo:.2f}")
    else:
        print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
    
    return saldo, extrato

def sacar(*, saldo, valor, extrato, limite, numero_saques, limite_saques, transacoes):
    excedeu_saldo = valor > saldo
    excedeu_limite = valor > limite
    excedeu_saques = numero_saques >= limite_saques

    if excedeu_saldo:
        print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
    elif excedeu_limite:
        print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
    elif excedeu_saques:
        print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
    elif valor > 0:
        saldo -= valor
        transacao = {
            "tipo": "Saque",
            "valor": -valor,
            "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S")
        }
        transacoes.append(transacao)
        extrato += f"Saque:\t\tR$ {valor:.2f}\n"
        numero_saques += 1
        print("\n=== Saque realizado com sucesso! ===")
        print(f"Novo saldo: R$ {saldo:.2f}")
    else:
        print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
    
    return saldo, extrato, numero_saques

def exibir_extrato(saldo, *, transacoes):
    print("\n================ EXTRATO ================")
    if not transacoes:
        print("Não foram realizadas movimentações.")
    else:
        for transacao in transacoes:
            print(f"{transacao['tipo']} de R$ {abs(transacao['valor']):.2f} em {transacao['data']}")
    print(f"\nSaldo atual:\tR$ {saldo:.2f}")
    print("==========================================")

def criar_usuario(usuarios):
    cpf = input("Informe o CPF (somente número): ")
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        print("\n@@@ Já existe usuário com esse CPF! @@@")
        return usuarios

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    usuarios.append({
        "nome": nome, 
        "data_nascimento": data_nascimento, 
        "cpf": cpf, 
        "endereco": endereco
    })

    print("=== Usuário criado com sucesso! ===")
    return usuarios

def filtrar_usuario(cpf, usuarios):
    for usuario in usuarios:
        if usuario["cpf"] == cpf:
            return usuario
    return None

def criar_conta(agencia, numero_conta, usuarios, contas):
    cpf = input("Informe o CPF do usuário: ")
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        contas.append({
            "agencia": agencia,
            "numero_conta": numero_conta,
            "usuario": usuario
        })
        print("\n=== Conta criada com sucesso! ===")
        print(f"Agência: {agencia} | Conta: {numero_conta}")
        return contas, numero_conta + 1

    print("\n@@@ Usuário não encontrado, fluxo de criação de conta encerrado! @@@")
    return contas, numero_conta

def listar_contas(contas):
    if not contas:
        print("\n@@@ Nenhuma conta cadastrada! @@@")
        return
        
    for conta in contas:
        linha = f"""\
            Agência:\t{conta['agencia']}
            C/C:\t\t{conta['numero_conta']}
            Titular:\t{conta['usuario']['nome']}
        """
        print(textwrap.dedent(linha))
        print("=" * 50)

def transferencia(saldo, transacoes, extrato):
    print("\n=== TRANSFERÊNCIA ===")
    valor = float(input("Informe o valor para transferência: "))
    
    if valor <= 0:
        print("\n@@@ Valor inválido para transferência! @@@")
        return saldo, extrato
        
    if valor > saldo:
        print("\n@@@ Saldo insuficiente para transferência! @@@")
        return saldo, extrato
        
    destino_agencia = input("Informe a agência de destino: ")
    destino_conta = input("Informe a conta de destino: ")
    
    saldo -= valor
    transacao = {
        "tipo": "Transferência",
        "valor": -valor,
        "data": datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M:%S"),
        "destino": f"Ag: {destino_agencia} C/C: {destino_conta}"
    }
    transacoes.append(transacao)
    extrato += f"Transferência:\tR$ {valor:.2f} para Ag: {destino_agencia} C/C: {destino_conta}\n"
    
    print("\n=== Transferência realizada com sucesso! ===")
    print(f"Valor transferido: R$ {valor:.2f}")
    print(f"Para: Agência {destino_agencia}, Conta {destino_conta}")
    print(f"Novo saldo: R$ {saldo:.2f}")
    
    return saldo, extrato

def main():
    # Estado inicial do sistema
    saldo = 0
    limite = 500
    extrato = ""
    numero_saques = 0
    LIMITE_SAQUES = 3
    usuarios = []
    contas = []
    agencia = "0001"
    numero_conta = 1
    transacoes = []

    while True:
        opcao = menu()

        if opcao == "d":
            valor = float(input("Informe o valor do depósito: "))
            saldo, extrato = depositar(saldo, valor, extrato, transacoes)

        elif opcao == "s":
            valor = float(input("Informe o valor do saque: "))
            saldo, extrato, numero_saques = sacar(
                saldo=saldo,
                valor=valor,
                extrato=extrato,
                limite=limite,
                numero_saques=numero_saques,
                limite_saques=LIMITE_SAQUES,
                transacoes=transacoes
            )

        elif opcao == "e":
            exibir_extrato(saldo, transacoes=transacoes)

        elif opcao == "nu":
            usuarios = criar_usuario(usuarios)

        elif opcao == "nc":
            contas, numero_conta = criar_conta(agencia, numero_conta, usuarios, contas)

        elif opcao == "lc":
            listar_contas(contas)
            
        elif opcao == "t":
            saldo, extrato = transferencia(saldo, transacoes, extrato)

        elif opcao == "q":
            print("\n=== Obrigado por usar nosso sistema bancário! ===")
            break

        else:
            print("Operação inválida, por favor selecione novamente a operação desejada.")

if __name__ == "__main__":
    main()
