#Adição = +
#Subtração = -
#Multiplicação = *
#Divisão = /
#Potência = **
#Divisão Inteira = //
#Resto da Divisão = %

#Ordem de precedência:
#1 -> ()
#2 -> **
#3 -> *,/,//,%
#4 -> +,-

n1=int(input('Digite um valor: '))
n2=int(input('Digite outro valor: '))
print(f'A soma vale {n1+n2}')

m=n1*n2
d=n1/n2
di=n1//n2
rd=n1%n2
e=n1**n2
print(f'Multiplicação = {m}\nDivisão = {d}\nDivisão inteira = {di}\nResto da divisão = {rd}\nExponenciação = {e}')

print('DESAFIOS DE AULA:')
N=int(input('Digite um número: '))
print(f'O número escolhido foi {N}, seu antecessor é {N-1} e seu sucessor é {N+1}!')
print(f'O dobro de {N} é {N*2}\nO triplo é {N*3}\nSua raiz quadrada é {N**(1/2)}')
N1=float(input('Quanto foi sua primeira nota? '))
N2=float(input('E a segunda? '))
print(f'Conforme as suas notas, sua média é {(N1+N2)/2}!')
M=float(input('Quantos metros tem essa parede? '))
print(f'Correspondente a {M*100}cm e {M*1000}mm')
print(f'A tabuada de {N} é:\n{N}x1 = {N*1}\n{N}x2 = {N*2}\n{N}x3 = {N*3}\n{N}x4 = {N*4}\n{N}x5 = {N*5}\n{N}x6 = {N*6}\n{N}x7 = {N*7}\n{N}x8 = {N*8}\n{N}x9 = {N*9}\n{N}x10 = {N*10} ')
Q=float(input('Quanto você tem na carteira? '))
print(f'Uau, com R${Q} você pode comprar US${Q//3.27}!')
A=float(input('Qual a altura dessa parede? '))
L=float(input('E a largura? '))
print(f'Sua área é de {A*L}, para pintar toda ela precisaremos de {A*L/2}m² de tinta.')
T=float(input('Quanto custa esse Jordan? '))
print(f'Ele custa R${T}, mas está com 5% de desconto, saindo por R${T*0.95}')
S=float(input('Quanto é o seu salário hoje? '))
print(f'Parabéns, você acaba de receber um aumento de 15%, a partir do próximo mês seu salário será R${S*1.15}')
