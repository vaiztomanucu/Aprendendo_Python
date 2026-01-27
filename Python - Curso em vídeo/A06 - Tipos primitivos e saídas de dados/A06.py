#int = números inteiros - EX:(7,-4,0,4988)
#float = números reais / pontos flutuantes - EX:(4.5,0.076,-15.223,7.0)
#bool = valores lógicos ou booleanos - EX:(True,False)
#str = valores caractéries - EX:('Olá','7.5','')

n1=int(input('Digite um valor: '))
n2=int(input('Digite outro valor: '))
s=n1+n2
print(f'A soma entre {n1} e {n2} vale {s}!')

n=input('Digite algo: ')
print(n.isnumeric()) #é numérico?
print(n.isalpha()) #é alfabético?
print(n.isalnum()) #é alfanumérico?
print(n.isdecimal()) #é decimal?
print(n.isupper()) #tem apenas maiúsculas?
print(n.islower()) #tem apenas minúsculas?

