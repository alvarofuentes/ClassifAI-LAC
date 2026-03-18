"""
Generador de catálogo CAUTAL (Clasificación de Actividades de Uso del Tiempo para América Latina).
Fuente: CEPAL. Se incluyen divisiones y grupos de actividades de tiempo diario de las personas.
Salida: data/raw/cautal_es.csv  — formato: id,text
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "cautal_es.csv"

# CAUTAL — Clasificación completa en español
# Fuente: CEPAL, División de Estadísticas
# https://repositorio.cepal.org/handle/11362/36906
CAUTAL_CATALOG = [
    # 1 — Trabajo remunerado y actividades relacionadas
    ("1", "Trabajo remunerado y actividades relacionadas"),
    ("11", "Trabajo remunerado en el empleo principal"),
    ("111", "Trabajo remunerado en el empleo principal realizado en el lugar de trabajo"),
    ("112", "Trabajo remunerado en el empleo principal realizado fuera del lugar de trabajo"),
    ("12", "Trabajo remunerado en otros empleos"),
    ("121", "Trabajo remunerado en otros empleos realizados en el lugar de trabajo"),
    ("122", "Trabajo remunerado en otros empleos realizados fuera del lugar de trabajo"),
    ("13", "Búsqueda de empleo"),
    ("131", "Búsqueda de empleo en el empleo principal"),
    ("132", "Búsqueda de otros empleos"),
    ("14", "Actividades relacionadas con el trabajo"),
    ("141", "Desplazamiento al lugar de trabajo y desde él"),
    ("142", "Capacitación remunerada y otras actividades relacionadas con el trabajo"),
    # 2 — Trabajo no remunerado en la producción de bienes para uso final propio
    ("2", "Trabajo no remunerado en la producción de bienes para uso final propio"),
    ("21", "Producción de cultivos para uso propio"),
    ("22", "Crianza de animales y producción de productos de origen animal para uso propio"),
    ("23", "Pesca y recolección para uso propio"),
    ("24", "Extracción y recolección de agua, leña y otros combustibles para uso propio"),
    ("25", "Construcción, mantenimiento mayor y reparaciones de la vivienda propia"),
    # 3 — Trabajo doméstico no remunerado y cuidados para el propio hogar
    ("3", "Trabajo doméstico no remunerado y cuidados para el propio hogar y sus miembros"),
    ("31", "Preparación de comidas y bebidas para el hogar"),
    ("311", "Preparación y cocción de alimentos"),
    ("312", "Servir comidas y bebidas y limpieza posterior a la preparación de alimentos"),
    ("313", "Conservación, fermentación, deshidratación y preparación de alimentos"),
    ("32", "Limpieza y mantenimiento del hogar"),
    ("321", "Limpieza y orden de los espacios e instalaciones del hogar"),
    ("322", "Limpieza de los aparatos y enseres del hogar"),
    ("33", "Lavandería y cuidado de ropa del hogar"),
    ("331", "Lavado y planchado de ropa"),
    ("332", "Costura, tejido y reparación de ropa"),
    ("34", "Gestión del hogar"),
    ("341", "Gestión de pagos y contabilidad del hogar"),
    ("342", "Planificación y organización de la vida familiar"),
    ("35", "Compras, trámites y servicios del hogar"),
    ("351", "Compras de alimentos, bebidas y otros bienes de consumo del hogar"),
    ("352", "Adquisición de servicios para el hogar"),
    ("353", "Trámites y diligencias"),
    ("36", "Cuidado de niños y niñas del hogar"),
    ("361", "Cuidado físico y supervisión de niños y niñas del hogar"),
    ("362", "Enseñanza y capacitación de niños y niñas del hogar"),
    ("363", "Actividades de juego y ocio con niños y niñas del hogar"),
    ("364", "Acompañamiento de niños y niñas del hogar"),
    ("37", "Cuidado de personas adultas mayores, enfermas o con discapacidad del hogar"),
    ("371", "Cuidado físico de personas adultas mayores del hogar"),
    ("372", "Asistencia a personas con enfermedad o discapacidad del hogar"),
    # 4 — Trabajo no remunerado para otros hogares, la comunidad y voluntariado
    ("4", "Trabajo no remunerado para otros hogares, la comunidad y el voluntariado"),
    ("41", "Trabajo doméstico y de cuidados no remunerado para otros hogares"),
    ("411", "Limpieza y mantenimiento para otros hogares"),
    ("412", "Cuidado de niños de otros hogares"),
    ("413", "Cuidado de personas adultas mayores de otros hogares"),
    ("42", "Trabajo no remunerado para la comunidad y voluntariado"),
    ("421", "Trabajo voluntario en organizaciones formales"),
    ("422", "Trabajo voluntario informal para la comunidad"),
    # 5 — Aprendizaje y formación
    ("5", "Aprendizaje y formación"),
    ("51", "Educación formal"),
    ("511", "Asistencia a clases, cursos y prácticas de educación básica, media y técnica"),
    ("512", "Asistencia a clases y cursos de educación superior"),
    ("52", "Tareas y estudio fuera de clases"),
    ("521", "Estudio y tareas escolares fuera del horario escolar"),
    ("53", "Otras actividades de aprendizaje"),
    ("531", "Cursos de idiomas, informática y capacitación no formal"),
    # 6 — Sociabilidad, participación cívica y práctica religiosa
    ("6", "Sociabilidad, participación cívica y práctica religiosa"),
    ("61", "Sociabilidad"),
    ("611", "Visitas y encuentros sociales presenciales"),
    ("612", "Comunicación social telefónica o en línea"),
    ("62", "Participación en actividades políticas y cívicas"),
    ("621", "Participación en reuniones y asambleas comunitarias"),
    ("622", "Participación en actividades políticas"),
    ("63", "Práctica religiosa"),
    ("631", "Asistencia a servicios religiosos"),
    # 7 — Cultura, ocio y aficiones
    ("7", "Cultura, ocio y aficiones"),
    ("71", "Entretenimiento y cultura"),
    ("711", "Asistencia a eventos culturales y espectáculos"),
    ("712", "Visita a museos, parques y sitios de interés"),
    ("72", "Ocio pasivo en el hogar"),
    ("721", "Ver televisión y videos"),
    ("722", "Escuchar radio y música"),
    ("723", "Lectura por placer"),
    ("73", "Aficiones y juegos"),
    ("731", "Actividades artísticas y manualidades"),
    ("732", "Juegos de mesa, videojuegos y juegos de azar"),
    ("74", "Deportes y actividades al aire libre"),
    ("741", "Práctica de deportes y actividad física"),
    ("742", "Caminatas y actividades al aire libre"),
    # 8 — Cuidados personales y mantenimiento de la salud
    ("8", "Cuidados personales y mantenimiento de la salud"),
    ("81", "Dormir"),
    ("811", "Sueño nocturno"),
    ("812", "Siesta y otros períodos de descanso"),
    ("82", "Comer y beber"),
    ("821", "Comidas principales"),
    ("822", "Meriendas y refrigerios"),
    ("83", "Higiene personal"),
    ("831", "Baño, ducha y aseo personal"),
    ("832", "Arreglo personal y cuidado del cabello"),
    ("84", "Atención de la salud"),
    ("841", "Visitas médicas y tratamientos de salud"),
    ("842", "Actividades de rehabilitación y fisioterapia"),
    # 9 — Tiempo no clasificado en otra categoría
    ("9", "Tiempo no especificado o no clasificado"),
    ("91", "Desplazamientos no relacionados con el trabajo"),
    ("911", "Desplazamientos personales"),
    ("912", "Esperas y tiempos muertos"),
    ("99", "Tiempo no especificado"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in CAUTAL_CATALOG:
            writer.writerow([code, description])
    print(f"✅ CAUTAL — {len(CAUTAL_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
