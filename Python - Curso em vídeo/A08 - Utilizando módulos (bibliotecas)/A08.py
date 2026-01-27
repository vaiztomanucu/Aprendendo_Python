#import doce - importa todos os "doces"
#from doce import "pudim" - dentro dos "doces", importa apenas o "pudim"
import math
num=int(input('Digite um número: '))
raiz=math.sqrt(num)
print(f'A raíz de {num} é igual a {raiz:.0f}.')
#Se eu importasse apenas o sqrt, poderia utilizar de outra forma, a seguir:
#from math import sqrt
#raiz=sqrt(num)
#para importar mais de uma função utilizar ','. EX:from math import sqrt,floor

import random
n=random.random()
print(n)
N=random.randint(1,10)
print(N)
#import+CTRL+SPACE para mostrar as bibliotecas padrões do python
#Para importar demais bibliotecas, utilizar import+"o nome da biblioteca" e clicar na lâmpada vermelha para instalar
#Para encontrar bibliotecas, exemplos e comandos basta acessar o python.org e ir em PyPI
import emoji
print(emoji.emojize("Olá, Mundo :smiling_face_with_sunglasses:"))
#print(emoji.EMOJI_DATA) para ver os nomes dos emojis
