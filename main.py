import maritalk
import os
import telebot
import random
import requests
from dotenv import load_dotenv
from datetime import date

class Chat:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        # self.esperando_mensagem = True
        self.meta_calorica = 0
        self.contagem_calorias = 0
        self.dieta = ""
        # aqui é uma maracutaia que eu fiz, para permitir vários chats rodarem ao mesmo tempo, as funções setup_dieta e setup_calorias são divididas em partes
        # e essas variáveis controlam para qual parte o programa vai
        # a ideia é: pega a primeira mensagem (setup_parte1 = True), faz a primeira parte da função (setup_parte1 = False), 
        # pega a proxima mensagem (setup_parte2 = True), faz a segunda parte da função (setup_parte2 = False)
        # não sei como fazer isso de uma forma melhor
        self.setup_calorias_parte1 = False
        self.setup_calorias_parte2 = False
        self.setup_dieta = False
        self.setup_dieta_feedback = False
        self.meta_atingida = False

chats: list[Chat] = []
prompt_direcionamento = """A partir do input do usuário, decida se ele quer contar calorias ou mudar a dieta.
        O usuário quer contar calorias caso ele fale sobre alguma refeição que fez.
        Se ele quiser mudar as calorias ou a dieta, digite somente 0. Se ele quiser contar calorias digite somente 1.
        Se o usuário citar algum alimento ou refeição, digite somente 1.
        Lembrando: se ele quiser mudar a dieta, digite somente 0. Se ele quiser contar calorias digite somente 1.
        Se ele digitar algo que não esteja relacionado a nenhuma dessas duas coisas (calorias e dieta), então retorne 'ERRO'.

        Usuário: Eu quero mudar a dieta.
        Resposta: 0
        
        Usuário: Eu comi um prato de feijão.
        Resposta: 1
        
        Usuário: Fui numa festa ontem.
        Resposta: ERRO

        Usuário: Não estou gostando da minha dieta.
        Resposta: 0
        
        Usuário: Peito de frango.
        Resposta: 1

        Usuário: Comi um peito de frango.
        Resposta: 1

        Usuário: Não gosto de tal refeição da minha dieta.
        Resposta: 0
        """
tabela_nutricional = {
    "arroz":130,
    "feijão":155,
    "frango":239,
    "linguíça":325,
    "alface":15,
    "tomate":18,
    "pasta de amendoim":588,
    "ovo":143,
    "carne vermelha":235,
    "berinjela":20,
    "macarrão":158,
    "hamburguer":300,
    "queijo":402,
    "batata inglesa cozida":52,
    "batata doce cozida":77,
    "batata frita":312,
    "pizza":266
}

if __name__ == "__main__":
    # setup inicial da maritaca e do telegram
    load_dotenv()
    CHAVE_MARITACA = os.getenv("CHAVE_MARITACA")
    CHAVE_TELEGRAM = os.getenv("CHAVE_TELEGRAM")
    model = maritalk.MariTalk(key=CHAVE_MARITACA,model="sabia-3")
    bot = telebot.TeleBot(CHAVE_TELEGRAM)

    # setup das variáveis
    data = date.today() 

    def get_chat(chat_id: int) -> Chat or None:
        for chat in chats:
            if chat.chat_id == chat_id:
                return chat
        return None

    def setup_calorias(chat,message, parte): # conferir valor de cut e de bulking (eu botei +500 e -500) e conferir calorias
        if parte == 0:
            prompt_calculo_calorias = """Você é um bot que calcula a quantidade de calorias diárias gastas pelo usuário a partir das informações dadas por ele.
            A partir das informações dadas pelo usuário, calcule a quantidade de calorias diárias gastas por ele e retorne SOMENTE o número de calorias. 
            Não retorne NADA além do número de calorias. Caso falte informações, faça a sua melhor aproximação da quantidade de calorias gastas pelo usuário.
            NUNCA deixe de retornar apenas o número de calorias, mesmo que talvez esse número esteja errado.

            Usuário: Tenho 18 anos, 1.75 centimetros de altura, peso 75 quilos e pratico exercícios moderados (musculação) uma vez por semana e sou homem.
            Resposta: 2100
            
            Usuário: Tenho 19 anos, 1.78 centimetros de altura, peso 72 quilos e sou homem.
            Resposta: 2300
            """

            chat.meta_calorica = int(model.generate(prompt_calculo_calorias+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"])
            
            # preparando para a segunda parte da função
            chat.setup_calorias_parte1 = False
            chat.setup_calorias_parte2 = True
            bot.send_message(message.chat.id,"Você quer emagrecer ou ganhar massa muscular?")
        elif parte == 1:
            prompt_objetivo = """A partir da resposta do usuário, decida se ele quer emagrecer (cut) ou ganhar massa muscular (bulk).
            Caso ele queira emagrecer (cut), retorne -500.
            Caso ele queira ganhar massa muscular (bulk), retorne 500.
            Nunca retorne algo além de 500 ou -500. Caso você não consiga determinar se ele quer emagrecer ou ganhar massa muscular, retorne 0.
            """

            objetivo = model.generate(prompt_objetivo+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"]

            chat.meta_calorica += int(objetivo)
            bot.send_message(message.chat.id, f"Você comeu 0 de {chat.meta_calorica} calorias.")
            
            # preparando para a primeira parte da função setup_dieta
            bot.send_message(message.chat.id, "Agora, vou fazer a sua dieta. Você pode fazer quaisquer sugestões que desejar (Ex: Não bote iogurte na dieta).")
            chat.setup_calorias_parte2 = False
            chat.setup_dieta = True # esta comentado pq a setup dieta não está feita ainda
    
    def setup_dieta(chat,message,parte):
        if parte == 0:
            # faça aqui a primeira dieta
            prompt_dieta_inicial = f"""Faça uma dieta baseando-se no seguinte modelo:

            Café da manhã (aproximadamente 600 kcal):
            2 fatias de pão integral (140 kcal)
            2 colheres de sopa de pasta de amendoim natural (180 kcal)
            1 banana média (105 kcal)
            2 ovos mexidos com azeite de oliva (200 kcal)

            Lanche da manhã (aproximadamente 300 kcal):
            1 iogurte grego natural sem açúcar (150 kcal)
            1 punhado de amêndoas (30g) (150 kcal)

            Almoço (aproximadamente 700 kcal):
            150g de peito de frango grelhado (240 kcal)
            1 xícara de arroz integral cozido (220 kcal)
            1/2 xícara de feijão preto (100 kcal)
            Salada à vontade (alface, tomate, pepino, cenoura) com 1 colher de sopa de azeite de oliva (120 kcal)
            1 batata-doce média assada (120 kcal)

            Lanche da tarde (aproximadamente 300 kcal):
            1 fatia de pão integral (70 kcal)
            2 colheres de sopa de guacamole (100 kcal)
            1 ovo cozido (70 kcal)
            1 fruta (maçã ou pêra) (60 kcal)

            Jantar (aproximadamente 500 kcal):
            150g de salmão grelhado (300 kcal)
            1 xícara de quinoa cozida (120 kcal)
            Salada verde à vontade com azeite e limão (80 kcal)

            Ceia (aproximadamente 200 kcal):
            1 copo de leite desnatado ou vegetal (120 kcal)
            2 colheres de sopa de aveia (80 kcal)
            Total: 2400 calorias
            
            Agora faça uma dieta de {chat.meta_calorica} calorias seguindo as seguintes sugestões: {message}"""
            
            dieta_inicial = model.generate(prompt_dieta_inicial,max_tokens=1000)["answer"]
            bot.send_message(message.chat.id, dieta_inicial)
            bot.send_message(message.chat.id,"Você gostou da dieta? Se não, fale o que mudar (Ex: Não gostei, tire o ovo).")

            chat.dieta = dieta_inicial
            chat.setup_dieta = False
            chat.setup_dieta_feedback = True
        elif parte == 1:            
            prompt_atualizações_dieta = f"""Determine se a resposta dada foi positiva ou negativa em relação a uma dieta. Caso seja positiva
            retorne 1 e somente 1, caso seja negativa retorne 0 e somente 0.
            Lembrando: Se a resposta for positiva em relação a dieta digite apenas 1, se não for digite apenas 0.
            Usuário: Eu gostei
            Resposta: 1
            
            Usuário: Eu não gostei, tire o ovo
            Resposta: 0
            
            Usuário: ok
            Resposta: 1
            """
            
            try:
                avaliacao_dieta = int(model.generate(prompt_atualizações_dieta, max_tokens=100 ,stopping_tokens=["\n"])["answer"])
                if(avaliacao_dieta==1):
                    chat.setup_dieta_feedback = False
                    bot.send_message(message.chat.id, "Tudo Pronto! Caso você queira mudar a sua dieta só me fale algo como 'Quero mudar minha dieta'. Agora, para cada refeição que você fizer, me diga o que comeu que eu irei contabiliza-la na sua contagem calórica diária.")
                    return
                elif(avaliacao_dieta==0):
                    # faz alguma nova dieta usando message
                    chat.setup_dieta_feedback = True
                    return
            except Exception as e:
                bot.send_message(message.chat.id, "Houve um erro! Caso você ainda não esteja satisfeito com a sua dieta digite 'Quero mudar minha dieta' ou algo equivalente.")
                chat.setup_dieta_feedback = False
                return

            chat.setup_dieta_feedback = False
                
    def pastebin_create(message,info):
        # Your API developer key (from Pastebin)
        api_dev_key = os.getenv("CHAVE_PASTEBIN")
        # The content of your paste
        api_paste_code = info
        # Optional paste name/title
        api_paste_name = str(random.randint(0,9999))
        # Optional paste settings (0 = public, 1 = unlisted, 2 = private)
        api_paste_private = '1'
        # Optional paste expiration date ('10M' = 10 minutes, '1H' = 1 hour, '1D' = 1 day, 'N' = never)
        api_paste_expire_date = '1D'
        # Option to create a new paste
        api_option = 'paste'

        # URL for Pastebin API
        url = 'https://pastebin.com/api/api_post.php'

        # Prepare the data for the POST request
        data = {
            'api_dev_key': api_dev_key,
            'api_paste_code': api_paste_code,
            'api_paste_name': api_paste_name,
            'api_paste_private': api_paste_private,
            'api_paste_expire_date': api_paste_expire_date,
            'api_option': api_option
        }

        # Send the POST request to the Pastebin API
        response = requests.post(url, data=data)
        return response

    def contagem_calorias(chat,message):
        
        # Pegar mensagem com os alimentos passada pelo usuário
        alimentos_consumidos = message.text.lower()
        
        # Maritalk inteligente nos fará os calculos
        prompt_calculo_calorias = f"""Calcule a quantidade de calorias dos seguintes alimentos: {alimentos_consumidos}.
        Retorne apenas o número indicando quantas calorias foram consumidas.
        Calcule tomando como base o dicionário {tabela_nutricional}, os valores deste dicionário foram calculados para 100g de cada alimento faça operações caso
        necessário para saber quantas calorias há em 300 gramas ou menos de determinado alimento, por exemplo 300 gramas de arroz são 3*130 = 390 calorias.
        Caso você dê uma resposta, não encaminhe para o erro em hipótese alguma."""

        # Resposta da I.A.
        try: 
            calorias_calculadas = model.generate(prompt_calculo_calorias, max_tokens=150, stopping_tokens=["\n"])["answer"]
            calorias_totais = int(calorias_calculadas)
            
            # Soma as calorias que a Maritaca calculou ao total diário
            chat.contagem_calorias += calorias_totais
            bot.send_message(message.chat.id, f"Você acaba de consumir {calorias_totais} calorias. Total do dia: {chat.contagem_calorias} de {chat.meta_calorica}. Continue assim e vai ficar monstrão!! \U0001F4AA")
            
            if chat.contagem_calorias >= chat.meta_calorica and chat.meta_atingida == False:
                bot.send_message(message.chat.id, "Parabéns! Sua meta diária calórica foi alcançada.")
                chat.meta_atingida = True
            elif chat.meta_atingida :
                bot.send_message(message.chat.id, "Que isso, vai sair comendo tudo agora? Já bateu suas metas, relaxa...")
        
        except Exception as e:
            bot.send_message(message.chat.id, "Desculpe-me, não consegui acompanhar essa dieta monstra. Por favor, tente novamente.")
            print(f"Erro ao calcular calorias: {e}")
        
    @bot.message_handler(func=lambda message: True) # o motivo de o bot não funcionar por comandos (/start) é porque eu achei
    # que seria mais interessante fazer o usuário interagir com o bot somente com linguagem natural, já que isso implicaria usar mais a maritaca
    def direcionamento(message):
        global prompt_direcionamento, data
        chat = get_chat(message.chat.id)

        # setup inicial da dieta e meta calórica
        if chat is None: 
            novo_chat = Chat(message.chat.id)
            chats.append(novo_chat)
            bot.reply_to(message, "Olá, eu sou o ChiquinhoGaviãoBOT, O bot de nutrição e eu vou te ajudar a alcançar o seu shape dos sonhos. Para isso, eu vou calcular a sua meta diária de calorias e fazer uma dieta para você.")
            bot.send_message(message.chat.id,"Digite: Eu quero fazer minha dieta.")
            return
        
        # expliquei o porquê eu fiz isso na class chat, mas basicamente é um controle de fluxo para saber em que parte da função o programa deve ir
        # surge do problema do programa ter que rodar vários chats ao mesmo tempo e funcionar mensagem por mensagem
        if chat.setup_calorias_parte1:
            setup_calorias(chat,message,0)
            return
        elif chat.setup_calorias_parte2:
            setup_calorias(chat,message,1)
            return
        elif chat.setup_dieta:
            setup_dieta(chat,message,0)
            return
        elif chat.setup_dieta_feedback:
            setup_dieta(chat,message,1)
            return

        # reseta a contagem para cada dia novo
        if (data != date.today()): 
            chat.contagem_calorias = 0
            chat.meta_atingida = False
            data = date.today()

        # após o setup inicial da dieta e da meta calórica, o usuário só pode fazer duas coisas: mudar a dieta ou contar calorias
        # a variável direcao serve para dizer ao programa se o usuário quer mudar a dieta (0) ou contar calorias (1)
        # cabe ao modelo analisar a mensagem e decidir o que o usuário quer fazer
        direcao = model.generate(prompt_direcionamento+message.text,max_tokens=200,stopping_tokens=["\n"])["answer"]
        print(direcao)

        if (direcao=='ERRO'):
            bot.send_message(message.chat.id,"Você digitou algo que não me interessa. Só me interesso por contar calorias e montar dietas!")
            return
        
        try:
            direcao = int(direcao)
        except:
            bot.send_message(message.chat.id,"Algo de errado ocorreu, digite a sua mensagem novamente!")
            return
        
        if (direcao==1):
            contagem_calorias(chat,message)
        elif (direcao==0):
            bot.send_message(message.chat.id,"Para calcular a sua meta calórica, digite a sua idade, peso, altura e sexo.")
            chat.setup_calorias_parte1 = True

    bot.infinity_polling()
