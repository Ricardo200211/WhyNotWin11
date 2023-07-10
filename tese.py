from datetime import datetime

agora = datetime.now()

data_hora_atual = agora.strftime("%Y-%m-%d %H:%M")

print(data_hora_atual)