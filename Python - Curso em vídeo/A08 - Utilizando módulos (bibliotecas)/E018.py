#Como eu tentei fazer:
a=float(input('Digite um ângulo: '))
'''print(f'O ângulo de {a} tem o SENO de {}\nO ângulo de {a} tem o COSSENO de {}\nO ângulo de {a} tem a TANGENTE de {}')'''

#Como ele ensinou:
from math import sin,cos,tan,radians
print(f'O ângulo de {a} tem o SENO de {sin(radians(a)):.2f}\nO ângulo de {a} tem o COSSENO de {cos(radians(a)):.2f}\nO ângulo de {a} tem a TANGENTE de {tan(radians(a)):.2f}')
