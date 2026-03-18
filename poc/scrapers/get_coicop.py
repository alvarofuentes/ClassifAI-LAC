"""
Generador de catálogo COICOP 2018 (Clasificación del Consumo Individual por Finalidades).
Fuente: UNSD. Se incluyen divisiones (2 dígitos) y grupos (3 dígitos) principales.
Salida: data/raw/coicop_es.csv  — formato: id,text
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "coicop_es.csv"

# Catálogo COICOP 2018 — Divisiones y Grupos en español
# Fuente oficial: https://unstats.un.org/unsd/classifications/Family/Detail/1010
COICOP_CATALOG = [
    # 01 — Alimentos y bebidas no alcohólicas
    ("01", "Alimentos y bebidas no alcohólicas"),
    ("011", "Alimentos"),
    ("0111", "Pan y cereales"),
    ("0112", "Carne"),
    ("0113", "Pescado y mariscos"),
    ("0114", "Leche, queso y huevos"),
    ("0115", "Aceites y grasas"),
    ("0116", "Frutas"),
    ("0117", "Verduras"),
    ("0118", "Azúcar, mermelada, miel, chocolate y confitería"),
    ("0119", "Productos alimenticios N.C.P."),
    ("012", "Bebidas no alcohólicas"),
    ("0121", "Café, té y cacao"),
    ("0122", "Aguas minerales, refrescos y jugos de frutas"),
    # 02 — Bebidas alcohólicas, tabaco y narcóticos
    ("02", "Bebidas alcohólicas, tabaco y narcóticos"),
    ("021", "Bebidas alcohólicas"),
    ("022", "Tabaco"),
    ("023", "Narcóticos"),
    # 03 — Artículos de vestir y calzado
    ("03", "Artículos de vestir y calzado"),
    ("031", "Artículos de vestir"),
    ("0311", "Prendas de vestir de materiales textiles"),
    ("0312", "Prendas de vestir de cuero o de piel"),
    ("0313", "Prendas de vestir de punto"),
    ("0314", "Accesorios de vestir"),
    ("032", "Calzado"),
    ("033", "Reparación y alquiler de artículos de vestir y calzado"),
    # 04 — Alojamiento, agua, electricidad, gas y otros combustibles
    ("04", "Alojamiento, agua, electricidad, gas y otros combustibles"),
    ("041", "Alquileres reales"),
    ("042", "Alquileres imputados"),
    ("043", "Reparación y mantenimiento de la vivienda"),
    ("044", "Suministro de agua y servicios diversos relacionados con la vivienda"),
    ("045", "Electricidad, gas y otros combustibles"),
    ("0451", "Electricidad"),
    ("0452", "Gas"),
    ("0453", "Combustibles líquidos"),
    ("0454", "Combustibles sólidos"),
    ("0455", "Calor"),
    # 05 — Muebles, artículos del hogar y mantenimiento corriente del hogar
    ("05", "Muebles, artículos del hogar y mantenimiento corriente del hogar"),
    ("051", "Muebles y accesorios; alfombras y otros revestimientos del suelo"),
    ("052", "Artículos textiles del hogar"),
    ("053", "Aparatos de calefacción y de cocina"),
    ("054", "Vajilla, cristalería y utensilios del hogar"),
    ("055", "Herramientas y equipo para el hogar y el jardín"),
    ("056", "Bienes y servicios para el mantenimiento corriente del hogar"),
    # 06 — Salud
    ("06", "Salud"),
    ("061", "Productos médicos y farmacéuticos"),
    ("0611", "Productos farmacéuticos"),
    ("0612", "Otros productos médicos"),
    ("0613", "Aparatos y equipo terapéuticos"),
    ("062", "Servicios para pacientes externos"),
    ("063", "Servicios hospitalarios"),
    # 07 — Transporte
    ("07", "Transporte"),
    ("071", "Compra de vehículos"),
    ("072", "Utilización de vehículos personales"),
    ("0721", "Piezas de repuesto y accesorios para vehículos"),
    ("0722", "Combustibles y lubricantes para vehículos personales"),
    ("0723", "Mantenimiento y reparación de vehículos personales"),
    ("073", "Servicios de transporte"),
    ("0731", "Transporte de pasajeros por ferrocarril"),
    ("0732", "Transporte de pasajeros por carretera"),
    ("0733", "Transporte de pasajeros por vía aérea"),
    ("0734", "Transporte de pasajeros por vía marítima y fluvial"),
    ("0735", "Transporte por tubería combinado y otros servicios de transporte"),
    # 08 — Información y comunicación
    ("08", "Información y comunicación"),
    ("081", "Equipo de información y comunicación"),
    ("082", "Servicios de telefonía y fax"),
    ("083", "Servicios de información"),
    # 09 — Esparcimiento, actividades recreativas y culturales
    ("09", "Esparcimiento, actividades recreativas y culturales"),
    ("091", "Equipo audiovisual, fotográfico y de procesamiento de la información"),
    ("092", "Otros artículos recreativos importantes y equipo conexo"),
    ("093", "Otros artículos recreativos y accesorios"),
    ("094", "Servicios recreativos y culturales"),
    ("095", "Diarios, libros y papelería"),
    ("096", "Paquetes turísticos"),
    # 10 — Servicios de educación
    ("10", "Servicios de educación"),
    ("101", "Educación preprimaria y primaria"),
    ("102", "Educación secundaria"),
    ("103", "Educación postsecundaria no terciaria"),
    ("104", "Educación terciaria"),
    ("105", "Educación no definida por nivel"),
    # 11 — Servicios de restaurantes y hoteles
    ("11", "Servicios de restaurantes y hoteles"),
    ("111", "Servicios de alimentos y bebidas"),
    ("112", "Servicios de alojamiento"),
    # 12 — Bienes y servicios diversos
    ("12", "Bienes y servicios diversos"),
    ("121", "Cuidado personal"),
    ("122", "Prostitución"),
    ("123", "Efectos personales N.C.P."),
    ("124", "Protección social"),
    ("125", "Seguros"),
    ("126", "Servicios financieros N.C.P."),
    ("127", "Otros servicios N.C.P."),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in COICOP_CATALOG:
            writer.writerow([code, description])
    print(f"✅ COICOP — {len(COICOP_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
