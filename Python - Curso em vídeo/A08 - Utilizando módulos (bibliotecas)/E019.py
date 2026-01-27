#Como eu tentei fazer:
n1=str(input('Nome do primeiro aluno: '))
n2=str(input('Nome do segundo aluno: '))
n3=str(input('Nome do terceiro aluno: '))
n4=str(input('Nome do quarto aluno: '))
import random
'''print(random.randint(n1,n2,n3,n4))'''

#Como ele ensinou:
lista=[n1,n2,n3,n4]
escolhido=random.choice(lista)
print(f'O aluno escolhido foi {escolhido}!')
