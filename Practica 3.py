print(f"Bienvenido a Lineage 2")

class Personaje:
    def __init__(self, Nombre, Sexo, Clase, Tipo_Arma):
        self.Nombre = Nombre
        self.Sexo = Sexo
        self.Clase = Clase
        self.Tipo_Arma = Tipo_Arma

    def clase_creada(self):
        print("Clase creada con extio!")



Nombre = input("Ingrese nombre del personaje: ")
Sexo = input("Sexo del personaje: ")
Clase = input("Tipo de clase del personaje: ")
Tipo_Arma = input("Tipo de arma del personaje: ")

Mi_Personaje = Personaje(Nombre, Sexo, Clase, Tipo_Arma)

print(f"""Caracteristicas de su personaje: 
      Nombre del prsonaje: {Nombre} 
      Tipo de clase: {Clase}
      Tipo de Arma: {Tipo_Arma}""")


seleciona = input("Desea crear esta clase ? ")
if(seleciona.lower() == "si"):
    Mi_Personaje.clase_creada()

print("Ingresando al juego....")

