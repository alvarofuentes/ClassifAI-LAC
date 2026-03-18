"""Generador de catálogo de Ingresos de Cuentas Nacionales (CEPAL_ING).
Basado en el Manual de Cuentas Nacionales de la CEPAL y el SCN 2008.
Clasifica los tipos de ingreso que reciben los hogares en encuestas de ingresos.
Salida: data/raw/cepal_ing_es.csv  — formato: id,text.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "cepal_ing_es.csv"

# Clasificación de Ingresos de Cuentas Nacionales (CEPAL / SCN 2008)
# Alineado con el Sistema de Cuentas Nacionales ONU 2008 y CEPAL
CEPAL_ING_CATALOG = [
    # 1 — Ingresos del trabajo
    ("1", "Ingresos del trabajo"),
    ("11", "Sueldos y salarios"),
    ("111", "Sueldos y salarios en efectivo"),
    ("1111", "Sueldo base o salario ordinario"),
    ("1112", "Horas extras y primas por turno"),
    ("1113", "Bonificaciones y gratificaciones"),
    ("1114", "Comisiones e incentivos"),
    ("1115", "Propinas"),
    ("112", "Sueldos y salarios en especie"),
    ("1121", "Vivienda o alojamiento provisto por el empleador"),
    ("1122", "Vehículo o transporte provisto por el empleador"),
    ("1123", "Alimentación provista por el empleador"),
    ("1124", "Otros bienes y servicios provistos por el empleador"),
    ("12", "Contribuciones sociales del empleador"),
    ("121", "Contribuciones a fondos de pensiones del empleador"),
    ("122", "Contribuciones a seguros de salud del empleador"),
    ("123", "Otras contribuciones del empleador"),
    ("13", "Ingresos laborales del trabajo independiente"),
    ("131", "Beneficios netos del trabajo por cuenta propia"),
    ("132", "Honorarios profesionales"),
    ("133", "Ingresos de pequeños negocios familiares"),
    ("134", "Remuneración en especie por trabajo independiente"),
    # 2 — Rentas de la propiedad
    ("2", "Rentas de la propiedad"),
    ("21", "Rentas de activos financieros"),
    ("211", "Intereses recibidos por depósitos bancarios"),
    ("212", "Dividendos de acciones"),
    ("213", "Rentas de fondos de inversión"),
    ("214", "Intereses recibidos por préstamos otorgados"),
    ("22", "Rentas de activos no financieros"),
    ("221", "Arrendamiento de bienes inmuebles"),
    ("2211", "Alquiler de vivienda principal"),
    ("2212", "Alquiler de locales comerciales"),
    ("2213", "Alquiler de terrenos"),
    ("222", "Arrendamiento de activos producidos"),
    ("2221", "Alquiler de maquinaria y equipo"),
    ("2222", "Alquiler de vehículos"),
    ("23", "Regalías y derechos de autor"),
    ("231", "Regalías por propiedad intelectual"),
    ("232", "Regalías por recursos naturales"),
    # 3 — Transferencias corrientes recibidas
    ("3", "Transferencias corrientes recibidas"),
    ("31", "Transferencias del gobierno"),
    ("311", "Pensiones y jubilaciones del sistema de seguridad social"),
    ("3111", "Pensiones de vejez o jubilación"),
    ("3112", "Pensiones de invalidez"),
    ("3113", "Pensiones de sobrevivientes/viudez"),
    ("312", "Prestaciones de desempleo"),
    ("313", "Asignaciones familiares"),
    ("314", "Transferencias condicionadas en efectivo"),
    ("3141", "Programas de transferencias condicionadas (ej. bolsas de alimentos)"),
    ("3142", "Subsidios habitacionales"),
    ("315", "Otras transferencias del gobierno"),
    ("3151", "Subsidios educativos"),
    ("3152", "Subsidios de salud"),
    ("3153", "Ayudas de emergencia"),
    ("32", "Transferencias de otros hogares"),
    ("321", "Remesas internacionales recibidas"),
    ("3211", "Remesas de familiares en el extranjero"),
    ("322", "Remesas internas recibidas"),
    ("323", "Pensión alimenticia recibida"),
    ("324", "Herencias y legados recibidos"),
    ("325", "Donaciones de otros hogares"),
    ("33", "Transferencias de instituciones sin fines de lucro"),
    ("331", "Ayudas de iglesias y organizaciones religiosas"),
    ("332", "Ayudas de ONG y fundaciones"),
    ("333", "Becas de estudio no gubernamentales"),
    # 4 — Ingresos del capital y otros ingresos
    ("4", "Ingresos del capital y otros ingresos no regulares"),
    ("41", "Ganancias de capital"),
    ("411", "Ganancias por venta de bienes raíces"),
    ("412", "Ganancias por venta de activos financieros"),
    ("413", "Ganancias por venta de otros activos"),
    ("42", "Liquidaciones y pagos únicos del trabajo"),
    ("421", "Indemnizaciones por despido o fin de contrato"),
    ("422", "Liquidación de prestaciones sociales acumuladas"),
    ("43", "Seguros recibidos"),
    ("431", "Cobros de seguros de vida"),
    ("432", "Cobros de seguros de accidente"),
    ("433", "Cobros de seguros de salud"),
    ("44", "Ingresos no habituales varios"),
    ("441", "Premios de loterías y juegos de azar"),
    ("442", "Ingresos por actividades ocasionales o informales"),
    ("443", "Otros ingresos no clasificados"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in CEPAL_ING_CATALOG:
            writer.writerow([code, description])
    print(f"✅ CEPAL_ING — {len(CEPAL_ING_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
