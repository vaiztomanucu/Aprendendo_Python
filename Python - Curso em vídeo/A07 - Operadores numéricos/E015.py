km=float(input('Qual a distância percorrida em km pelo carro? '))
d=int(input('Por quantos dias ele foi alugado? '))
pago=(km*0.15)+(d*60)
print(f'O valor a pagar é de R${pago:.2f}!')
