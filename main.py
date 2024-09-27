import maritalk
import os
import os

# está com problema na parte de calcular as calorias, então algumas vezes é necessário reiniciar o programa para funcionar, além disso o programa não considerar o fator se quer emagrecer ou engordar
# não é uma prioridade, já que tem como fazer hardcoded
# (1): Otimizar os prompts, acertar a formatação das mensagens, conferir e melhorar acurácia etc...
# (2): passar para o telegram
# (3): conferir a dieta, eu não conferi ela
# (4): opção de mudar a dieta e/ou a meta de calorias
# (5): para depois: fazer o bagulho de todo o dia ele resetar a contagem de calorias
# (6): para depois: do jeito que está até o (5) está tudo fixo, ou seja, se você muda a quantidade de calorias ela muda pra sempre. Fazer, então, ser possível
# o usuário mudar de apenas um dia (para compensar pelo dia anterior) 
model = maritalk.MariTalk(key="",model="sabia-3")
prompt_calculo_calorias = """Dado a string 'INFORMAÇÃO', cálcule a quantidade de calorias diárias gastas e retorne somente e apenas o número de calorias calculado (e mais nada). Caso falte informações suficientes, digite 'ERRO' mais quais informações faltaram.
    Exemplos:
    Exemplo 1: INFORMAÇÃO: Tenho 18 anos, 1.75 centimetros de altura, peso 75 quilos e pratico exercícios moderados (musculação) uam vez por semana e sou homem.
    RESPOSTA: 2100
    
    Exemplo 2 (falta informação): INFORMAÇÃO: Tenho 18 anos.
    RESPOSTA: ERRO. Falta altura, peso e sexo."""
setup_finalizado = False
calorias = 0
calorias_contagem = 0
prompt_input = "INFORMAÇÃO:"+input("Digite sua idade, seu peso, sua altura, seu sexo, o quanto você pesa e o tipo e a frequência de exercícios. Exemplo: Tenho 18 anos, peso 70 quilos, tenho 1.75 de altura, sou homem, faço musculação moderada duas vezes por semana. \n")
while(not setup_finalizado):
    resposta = model.generate(prompt_calculo_calorias+" "+prompt_input,max_tokens=200,stopping_tokens=["\n"])["answer"]
    if (resposta[:4]=="ERRO"):
        print(resposta)
        prompt_input += input("Apenas digite o que falta: ")
        continue
    calorias = int(resposta) + 400
    setup_finalizado = True
    print(calorias)
    
prompt_dieta = f"Faça uma dieta diária para se atingir {calorias} calorias."
dieta = model.generate(prompt_dieta,max_tokens=1000,stopping_tokens=["\n"])["answer"]
print(dieta)

promt_contagem = "Para qualquer refeição feita pelo usuário, retorne apenas e somente a quantidade de calorias desta refeição. Não seja muito exato, caso não consiga calcula faça uma suposição imprecisa da quantidade de calorias. Caso falte informações suficientes, chute um valor de calorias, nunca em hipótese alguma retorne algo além do número de calorias. Exemplo: USUÁRIO: Comi um peito de frango, um prato de arroz e um prato de feijão. RESPOSTA: 500. Exemplo 2 (falta informações): Usuário: Comi um filé de frango RESPOSTA: 250"
while(True):
    prompt_refeicao = input()
    contagem = model.generate(promt_contagem+" "+prompt_refeicao,max_tokens=10,stopping_tokens=["\n"])["answer"]
    while (contagem[:4]=="ERRO"):
        print(contagem)
        prompt_refeicao += input("Apenas digite o que falta: ")
        contagem = model.generate(promt_contagem+" "+prompt_refeicao,max_tokens=50,stopping_tokens=["\n"])["answer"]
        continue
    calorias_contagem += int(contagem)
    print(calorias_contagem)
    if (calorias_contagem >= calorias):
        print("Parabéns. Você atingiu a sua meta diária de calorias.")
    