#Como eu tentei fazer:
n1=str(input('Nome do primeiro aluno: '))
n2=str(input('Nome do segundo aluno: '))
n3=str(input('Nome do terceiro aluno: '))
n4=str(input('Nome do quarto aluno: '))
import random
'''lista=[n1,n2,n3,n4]
ordem=random.choices(lista)
print(f'A ordem de apresentação do trabalho será: {ordem}')'''

#Como ele ensinou:
lista=[n1,n2,n3,n4]
random.shuffle(lista)
print(f'A ordem de apresentações do trabalho será:\n{lista}')
