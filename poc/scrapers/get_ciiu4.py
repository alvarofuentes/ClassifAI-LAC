"""Generador de catálogo CIIU Rev.4 (Clasificación Industrial Internacional Uniforme).
Fuente: UNSD / CEPAL. Se usan los grupos de 2-3 dígitos para mantener
un catálogo manejable y representativo de cada rama de actividad.
Salida: data/raw/ciiu4_es.csv  — formato: id,text.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "ciiu4_es.csv"

# Catálogo CIIU Rev.4 — Secciones + Divisiones (2 dígitos) en español
# Fuente oficial: https://unstats.un.org/unsd/classifications/Econ/isic
CIIU4_CATALOG = [
    # A — Agricultura, ganadería, silvicultura y pesca
    ("A", "Agricultura, ganadería, silvicultura y pesca"),
    ("01", "Agricultura, ganadería, caza y actividades de servicios conexas"),
    ("011", "Cultivos no permanentes"),
    ("012", "Cultivos permanentes"),
    ("013", "Propagación de plantas"),
    ("014", "Ganadería"),
    ("015", "Producción mixta"),
    ("016", "Actividades de apoyo a la agricultura y la ganadería"),
    ("017", "Caza ordinaria y mediante trampas y actividades de servicios conexas"),
    ("02", "Silvicultura y extracción de madera"),
    ("021", "Silvicultura y otras actividades forestales"),
    ("022", "Extracción de madera"),
    ("023", "Recolección de productos forestales distintos de la madera"),
    ("024", "Servicios de apoyo a la silvicultura"),
    ("03", "Pesca y acuicultura"),
    ("031", "Pesca"),
    ("032", "Acuicultura"),
    # B — Explotación de minas y canteras
    ("B", "Explotación de minas y canteras"),
    ("05", "Extracción de carbón de piedra y lignito"),
    ("06", "Extracción de petróleo crudo y gas natural"),
    ("07", "Extracción de minerales metalíferos"),
    ("071", "Extracción de minerales de hierro"),
    ("072", "Extracción de minerales metalíferos no ferrosos"),
    ("08", "Explotación de otras minas y canteras"),
    ("09", "Actividades de servicios de apoyo para la explotación de minas y canteras"),
    # C — Industrias manufactureras
    ("C", "Industrias manufactureras"),
    ("10", "Elaboración de productos alimenticios"),
    ("11", "Elaboración de bebidas"),
    ("12", "Elaboración de productos de tabaco"),
    ("13", "Fabricación de productos textiles"),
    ("14", "Fabricación de prendas de vestir"),
    ("15", "Fabricación de cueros y productos conexos"),
    ("16", "Producción de madera y fabricación de productos de madera y corcho"),
    ("17", "Fabricación de papel y de productos de papel"),
    ("18", "Impresión y reproducción de grabaciones"),
    ("19", "Fabricación de coque y productos de la refinación del petróleo"),
    ("20", "Fabricación de sustancias y productos químicos"),
    ("21", "Fabricación de productos farmacéuticos, sustancias químicas medicinales"),
    ("22", "Fabricación de productos de caucho y plástico"),
    ("23", "Fabricación de otros productos minerales no metálicos"),
    ("24", "Fabricación de metales comunes"),
    ("25", "Fabricación de productos elaborados de metal, excepto maquinaria y equipo"),
    ("26", "Fabricación de productos de informática, electrónica y óptica"),
    ("27", "Fabricación de equipo eléctrico"),
    ("28", "Fabricación de maquinaria y equipo N.C.P."),
    ("29", "Fabricación de vehículos automotores, remolques y semirremolques"),
    ("30", "Fabricación de otro equipo de transporte"),
    ("31", "Fabricación de muebles"),
    ("32", "Otras industrias manufactureras"),
    ("33", "Reparación e instalación de maquinaria y equipo"),
    # D — Suministro de electricidad, gas, vapor y aire acondicionado
    ("D", "Suministro de electricidad, gas, vapor y aire acondicionado"),
    ("35", "Suministro de electricidad, gas, vapor y aire acondicionado"),
    # E — Suministro de agua; evacuación de aguas residuales
    ("E", "Suministro de agua; evacuación de aguas residuales, gestión de desechos"),
    ("36", "Captación, tratamiento y distribución de agua"),
    ("37", "Evacuación y tratamiento de aguas residuales"),
    ("38", "Recogida, tratamiento y eliminación de desechos; recuperación de materiales"),
    ("39", "Actividades de descontaminación y otros servicios de gestión de desechos"),
    # F — Construcción
    ("F", "Construcción"),
    ("41", "Construcción de edificios"),
    ("42", "Ingeniería civil"),
    ("43", "Actividades especializadas de construcción"),
    # G — Comercio al por mayor y al por menor
    ("G", "Comercio al por mayor y al por menor; reparación de vehículos"),
    ("45", "Comercio al por mayor y al por menor y reparación de vehículos automotores"),
    ("46", "Comercio al por mayor, excepto el de vehículos automotores y motocicletas"),
    ("47", "Comercio al por menor, excepto el de vehículos automotores y motocicletas"),
    # H — Transporte y almacenamiento
    ("H", "Transporte y almacenamiento"),
    ("49", "Transporte por vía terrestre y por tubería"),
    ("50", "Transporte por vía acuática"),
    ("51", "Transporte aéreo"),
    ("52", "Almacenamiento y actividades de apoyo al transporte"),
    ("53", "Actividades postales y de mensajería"),
    # I — Actividades de alojamiento y de servicio de comidas
    ("I", "Actividades de alojamiento y de servicio de comidas y bebidas"),
    ("55", "Actividades de alojamiento"),
    ("56", "Actividades de servicio de comidas y bebidas"),
    # J — Información y comunicaciones
    ("J", "Información y comunicaciones"),
    ("58", "Actividades de edición"),
    ("59", "Actividades de producción de películas cinematográficas, vídeo y televisión"),
    ("60", "Actividades de programación y transmisión de radio y televisión"),
    ("61", "Telecomunicaciones"),
    ("62", "Programación informática, consultoría de informática y actividades conexas"),
    ("63", "Actividades de servicios de información"),
    # K — Actividades financieras y de seguros
    ("K", "Actividades financieras y de seguros"),
    ("64", "Actividades de servicios financieros, excepto las de seguros y fondos de pensiones"),
    ("65", "Seguros, reaseguros y fondos de pensiones, excepto los planes de seguridad social"),
    ("66", "Actividades auxiliares de las actividades de servicios financieros y de seguros"),
    # L — Actividades inmobiliarias
    ("L", "Actividades inmobiliarias"),
    ("68", "Actividades inmobiliarias"),
    # M — Actividades profesionales, científicas y técnicas
    ("M", "Actividades profesionales, científicas y técnicas"),
    ("69", "Actividades jurídicas y de contabilidad"),
    ("70", "Actividades de oficinas centrales; actividades de consultoría de gestión"),
    ("71", "Actividades de arquitectura e ingeniería; ensayos y análisis técnicos"),
    ("72", "Investigación científica y desarrollo"),
    ("73", "Publicidad y estudios de mercado"),
    ("74", "Otras actividades profesionales, científicas y técnicas"),
    ("75", "Actividades veterinarias"),
    # N — Actividades de servicios administrativos y de apoyo
    ("N", "Actividades de servicios administrativos y de apoyo"),
    ("77", "Actividades de alquiler y arrendamiento"),
    ("78", "Actividades de empleo"),
    ("79", "Actividades de agencias de viajes, operadores turísticos y servicios de reserva"),
    ("80", "Actividades de seguridad e investigación"),
    ("81", "Servicios a edificios y actividades de paisajismo"),
    ("82", "Actividades administrativas de oficina y otras actividades de apoyo a las empresas"),
    # O — Administración pública y defensa
    ("O", "Administración pública y defensa; planes de seguridad social de afiliación obligatoria"),
    ("84", "Administración pública y defensa; planes de seguridad social de afiliación obligatoria"),
    # P — Enseñanza
    ("P", "Enseñanza"),
    ("85", "Enseñanza"),
    # Q — Actividades de atención de la salud humana y de asistencia social
    ("Q", "Actividades de atención de la salud humana y de asistencia social"),
    ("86", "Actividades de atención de la salud humana"),
    ("87", "Actividades de atención en instituciones"),
    ("88", "Actividades de asistencia social sin alojamiento"),
    # R — Actividades artísticas, de entretenimiento y recreativas
    ("R", "Actividades artísticas, de entretenimiento y recreativas"),
    ("90", "Actividades creativas, artísticas y de entretenimiento"),
    ("91", "Actividades de bibliotecas, archivos, museos y otras actividades culturales"),
    ("92", "Actividades de juegos de azar y apuestas"),
    ("93", "Actividades deportivas, de esparcimiento y recreativas"),
    # S — Otras actividades de servicios
    ("S", "Otras actividades de servicios"),
    ("94", "Actividades de asociaciones"),
    ("95", "Reparación de computadoras y enseres domésticos"),
    ("96", "Otras actividades de servicios personales"),
    # T — Hogares privados con personal doméstico
    ("T", "Actividades de los hogares como empleadores de personal doméstico"),
    ("97", "Actividades de los hogares como empleadores de personal doméstico"),
    ("98", "Actividades indiferenciadas de producción de bienes y servicios de hogares privados"),
    # U — Actividades de organizaciones y órganos extraterritoriales
    ("U", "Actividades de organizaciones y órganos extraterritoriales"),
    ("99", "Actividades de organizaciones y órganos extraterritoriales"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in CIIU4_CATALOG:
            writer.writerow([code, description])
    print(f"✅ CIIU4 — {len(CIIU4_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
