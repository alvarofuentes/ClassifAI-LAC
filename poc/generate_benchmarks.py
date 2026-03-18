"""Script para generar todos los benchmarks sintéticos (Fase 1.5).
Crea archivos CSV de prueba en data/benchmarks/ con el formato:
id_registro, literal, ground_truth, difficulty.

Diferentes niveles de dificultad:
[A] Control: idéntico o muy similar a la descripción oficial
[B] Informal: términos coloquiales o de encuestas reales
[C] Ambiguo/complejo: descripciones largas o que mezclan conceptos
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "data" / "benchmarks"

# --- Muestras para CIIU Rev.4 (Empresas/Ramas de Actividad) ---
CIIU4_SAMPLES = [
    # id_registro, literal, ground_truth, difficulty
    ("b1", "Cultivo de trigo y maíz", "011", "A"),
    ("b2", "Chacra que cría vacas y cerdos", "014", "B"),
    ("b3", "Fábrica de zapatos de cuero", "15", "A"),
    ("b4", "Taller de confección de ropa", "14", "A"),
    ("b5", "Elaboración de pan y tortas", "10", "A"),  # 10 es Alimentos
    ("b6", "Panadería (venta al público)", "47", "B"),  # 47 es Comercio al por menor
    ("b7", "Constructora de edificios residenciales", "41", "A"),
    ("b8", "Tienda de abarrotes y verdulería", "47", "B"),
    ("b9", "Empresa de camiones de carga", "49", "A"),
    ("b10", "Hotel tres estrellas con restaurante", "55", "C"),  # Alojamiento
    ("b11", "Restaurante de comida rápida", "56", "A"),
    ("b12", "Servicio de desarrollo de software", "62", "A"),
    ("b13", "Estudio de abogados y contadores", "69", "A"),
    ("b14", "Escuela primaria estatal", "85", "A"),
    ("b15", "Hospital clínico provincial", "86", "A"),
    ("b16", "Peluquería de barrio", "96", "A"),
]

# --- Muestras para COICOP 2018 (Consumo de hogares) ---
COICOP_SAMPLES = [
    ("c1", "Un kilo de pan marraqueta", "0111", "B"),
    ("c2", "Carne de vacuno para asado", "0112", "B"),
    ("c3", "Botella de Coca-Cola de 2 litros", "0122", "B"),
    ("c4", "Cerveza en lata pack de 6", "021", "A"),
    ("c5", "Pantalón vaquero para niño", "0311", "A"),
    ("c6", "Zapatillas deportivas de mujer", "032", "A"),
    ("c7", "Pago de la cuenta de la luz mensual", "0451", "B"),
    ("c8", "Balón de gas licuado de 15 kilos", "0452", "B"),
    ("c9", "Refrigerador no frost dos puertas", "053", "A"),
    ("c10", "Detergente en polvo para lavar ropa", "056", "B"),
    ("c11", "Caja de Paracetamol 500mg", "0611", "A"),
    ("c12", "Consulta médica médico general", "062", "A"),
    ("c13", "Pasaje en autobús urbano", "0732", "A"),
    ("c14", "Plan de telefonía celular 5G", "082", "B"),
    ("c15", "Televisor Smart TV 55 pulgadas", "091", "A"),
    ("c16", "Mensualidad de colegio particular", "102", "B"),
    ("c17", "Almuerzo menú del día en restaurante", "111", "B"),
    ("c18", "Corte de pelo de hombre", "121", "A"),
]

# --- Muestras para CPC Ver.2.1 (Productos Central) ---
CPC2_SAMPLES = [
    ("p1", "Tomates frescos a granel", "012", "A"),
    ("p2", "Café en grano sin tostar de exportación", "018", "A"),
    ("p3", "Vacas lecheras vivas", "021", "B"),
    ("p4", "Pescado fresco del día", "04", "A"),
    ("p5", "Gas natural por cañería", "12", "A"),
    ("p6", "Electricidad domiciliaria", "15", "A"),
    ("p7", "Carne de cerdo congelada", "211", "A"),
    ("p8", "Lata de atún en aceite", "215", "B"),
    ("p9", "Azúcar blanca refinada", "242", "A"),
    ("p10", "Vino tinto cabernet sauvignon", "252", "B"),
    ("p11", "Aspirina", "346", "B"),  # Productos farmacéuticos
    ("p12", "Gasolina 95 octanos", "33", "B"),  # Coque y refinación
    ("p13", "Silla de madera de pino", "47", "B"),  # Muebles
    ("p14", "Construcción de puente de vigas", "54", "C"),  # Obras de ing civil
    ("p15", "Servicios de guardería infantil", "93", "C"),  # Servicios sociales
]

# --- Muestras para ICCS (Delitos) ---
ICCS_SAMPLES = [
    ("i1", "Asesinato con arma de fuego", "0101", "A"),  # Homicidio intencional
    ("i2", "Muerte por accidente de tránsito chofer ebrio", "0903", "B"),  # Homicidio culposo tráfico
    ("i3", "Amenazas con arma blanca", "0210", "B"),  # Acoso / Amenazas (0210 o similar)
    ("i4", "Robo del celular en la calle con violencia", "0301", "B"),  # Robo con violencia
    ("i5", "Carterista me sacó la billetera en el bus", "0305", "B"),  # Hurto
    ("i6", "Se llevaron mi auto que estaba estacionado", "0302", "B"),  # Sustracción de vehículos
    ("i7", "Entraron a la casa cuando no estábamos", "0303", "B"),  # Robo con fuerza en lugar habitado
    ("i8", "Estafa piramidal por internet", "0402", "B"),  # Fraude informático
    ("i9", "Falsificación de billetes de 100 dólares", "0404", "A"),
    ("i10", "Soborno a un policía de tránsito", "0502", "A"),
    ("i11", "Lavado de activos empresariales", "0406", "A"),
    ("i12", "Tráfico de cocaína en aeropuerto", "0801", "A"),
    ("i13", "Pesca ilegal en reserva protegida", "0701", "A"),  # Delitos ambientales
]

# --- Muestras para CAUTAL (Uso del tiempo) ---
CAUTAL_SAMPLES = [
    ("t1", "Trabajar en la oficina todo el día", "111", "A"),
    ("t2", "Viaje de ida y vuelta al trabajo en metro", "141", "A"),
    ("t3", "Cultivar tomates en la huerta de la casa", "21", "A"),
    ("t4", "Hacer el almuerzo para la familia", "311", "A"),
    ("t5", "Lavar los platos", "312", "A"),
    ("t6", "Barrer y trapear el piso de la cocina", "321", "B"),
    ("t7", "Recoger la ropa de la lavandería", "353", "C"),  # Trámites
    ("t8", "Ayudar a los niños con la tarea de matemáticas", "362", "A"),
    ("t9", "Cuidar a la abuela que está en cama", "371", "B"),
    ("t10", "Ir a clases a la universidad", "512", "A"),
    ("t11", "Ir al culto dominical en la iglesia", "631", "A"),
    ("t12", "Mirar series en Netflix toda la tarde", "721", "B"),
    ("t13", "Jugar fútbol con los amigos en el parque", "741", "B"),
    ("t14", "Dormir de noche 8 horas", "811", "A"),
    ("t15", "Ducharse por la mañana", "831", "A"),
]

# --- Muestras para CEPAL_ING (Ingresos de encuestas) ---
CEPAL_ING_SAMPLES = [
    ("e1", "Sueldo bruto mensual de la fábrica", "1111", "A"),  # Sueldo base
    ("e2", "Pago de horas extras", "1112", "A"),
    ("e3", "Bono de productividad trimestral", "1113", "A"),
    ("e4", "Lo que saqué de vender cosméticos en mi tiempo libre", "131", "C"),  # Beneficios netos cuenta propia
    ("e5", "Intereses por el plazo fijo del banco", "211", "A"),
    ("e6", "Arriendo que me paga el inquilino del departamento", "2211", "B"),
    ("e7", "Pensión de jubilación del estado", "3111", "A"),
    ("e8", "Subsidio de Bono Solidario del gobierno", "3141", "B"),  # Transferencias condicionadas
    ("e9", "Dinero enviado por mi hijo desde Estados Unidos", "3211", "B"),  # Remesas internacionales
    ("e10", "Pensión por alimentos del ex marido", "323", "B"),
    ("e11", "Finiquito por despido de la empresa", "421", "A"),
    ("e12", "Premio que gané en el Kino (lotería)", "441", "B"),
]


def save_benchmark(filename: str, samples: list):
    path = OUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id_registro", "literal", "ground_truth", "difficulty"])
        for sample in samples:
            writer.writerow(sample)
    print(f"✅ Generado: {path.name} ({len(samples)} casos)")


def main():
    print("==================================================")
    print("ClassifAI-LAC — Generando Benchmarks Sintéticos")
    print("==================================================\n")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    save_benchmark("benchmark_ciiu4.csv", CIIU4_SAMPLES)
    save_benchmark("benchmark_coicop.csv", COICOP_SAMPLES)
    save_benchmark("benchmark_cpc2.csv", CPC2_SAMPLES)
    save_benchmark("benchmark_iccs.csv", ICCS_SAMPLES)
    save_benchmark("benchmark_cautal.csv", CAUTAL_SAMPLES)
    save_benchmark("benchmark_cepal_ing.csv", CEPAL_ING_SAMPLES)

    print("\n✅ Todos los benchmarks han sido creados en data/benchmarks/")
    print("El siguiente paso será correr un script unificado de evaluación.")


if __name__ == "__main__":
    main()
