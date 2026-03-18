"""Generador de catálogo CPC Ver.2.1 (Clasificación Central de Productos).
Fuente: UNSD. Se incluyen secciones (1 dígito), divisiones (2) y grupos (3 dígitos).
Un subconjunto representativo de las 9 secciones y sus divisiones principales.
Salida: data/raw/cpc2_es.csv  — formato: id,text.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "cpc2_es.csv"

# CPC Ver.2.1 — Secciones, Divisiones y Grupos principales en español
# Fuente: https://unstats.un.org/unsd/classifications/Econ/cpc
CPC2_CATALOG = [
    # Sección 0 — Productos agrícolas, forestales y pesqueros
    ("0", "Productos agrícolas, forestales y pesqueros"),
    ("01", "Productos de agricultura, horticultura y jardinería"),
    ("011", "Cereales"),
    ("012", "Verduras"),
    ("013", "Frutas y nueces"),
    ("014", "Semillas oleaginosas y frutos oleaginosos"),
    ("015", "Plantas vivas, bulbos, tubérculos y flores cortadas"),
    ("016", "Raíces, tubérculos, cañas de azúcar y remolacha azucarera"),
    ("017", "Plantas usadas en farmacia, perfumería u otros usos"),
    ("018", "Café verde y sin descascarar; té; cacao"),
    ("019", "Otros productos de agricultura"),
    ("02", "Animales vivos y sus productos"),
    ("021", "Bovinos vivos y búfalos"),
    ("022", "Ovinos, caprinos, equinos, asnos, mulas y burdéganos vivos"),
    ("023", "Porcinos vivos"),
    ("024", "Aves de corral vivas"),
    ("025", "Otros animales vivos"),
    ("029", "Productos animales N.C.P."),
    ("03", "Madera, recursos forestales y troncos"),
    ("04", "Pescado y otros productos de pesca"),
    # Sección 1 — Minerales; electricidad, gas y agua
    ("1", "Minerales; electricidad, gas y agua"),
    ("11", "Carbón, lignito y turba"),
    ("12", "Petróleo crudo y gas natural"),
    ("13", "Minerales metálicos"),
    ("131", "Menas de hierro"),
    ("132", "Minerales de uranio y torio"),
    ("133", "Menas de metales no ferrosos"),
    ("14", "Minerales no metálicos"),
    ("15", "Electricidad"),
    ("16", "Gas distribuido"),
    ("17", "Agua"),
    ("18", "Vapor y agua caliente; aire refrigerado; hielo"),
    # Sección 2 — Alimentos, bebidas y tabaco; textiles, prendas de vestir y productos de cuero
    ("2", "Alimentos, bebidas y tabaco; textiles, prendas de vestir y productos de cuero"),
    ("21", "Carne, pescado, fruta, legumbres, aceites y grasas procesados"),
    ("211", "Carne de animales de las especies bovina, ovina, caprina, porcina y equina"),
    ("212", "Carne de aves"),
    ("214", "Productos de matanza N.C.P."),
    ("215", "Pescados y mariscos preparados"),
    ("216", "Frutas y hortalizas preparadas o en conservas"),
    ("217", "Aceites y grasas de origen vegetal y animal"),
    ("22", "Productos lácteos y huevos"),
    ("23", "Productos de molinería; almidones y productos del almidón; alimentos preparados"),
    ("24", "Otros productos alimenticios"),
    ("241", "Productos de panadería y pastelería"),
    ("242", "Azúcar"),
    ("243", "Cacao, chocolate y artículos de confitería"),
    ("244", "Macarrones, fideos, alcuzcuz y productos farináceos similares"),
    ("245", "Comidas y platos preparados"),
    ("249", "Otros productos alimenticios N.C.P."),
    ("25", "Bebidas"),
    ("251", "Bebidas no alcohólicas; aguas minerales y otras aguas embotelladas"),
    ("252", "Vinos de uva"),
    ("253", "Cerveza y malta"),
    ("259", "Otras bebidas alcohólicas"),
    ("26", "Productos de tabaco"),
    ("27", "Hilados e hilos; tejidos"),
    ("28", "Artículos textiles"),
    ("29", "Prendas de vestir; pieles"),
    ("291", "Prendas de vestir"),
    ("292", "Pieles"),
    # Sección 3 — Otros productos manufacturados
    ("3", "Otros productos manufacturados"),
    ("31", "Madera y productos de madera y de corcho (excepto muebles)"),
    ("32", "Pasta de papel, papel y productos de papel; artículos impresos"),
    ("33", "Coque y productos de refinación del petróleo"),
    ("34", "Productos químicos y farmacéuticos"),
    ("341", "Sustancias químicas básicas"),
    ("342", "Abonos y compuestos de nitrógeno"),
    ("343", "Plásticos en formas primarias y caucho sintético"),
    ("346", "Productos farmacéuticos"),
    ("349", "Otros productos químicos"),
    ("35", "Productos de caucho y plástico"),
    ("36", "Productos minerales no metálicos"),
    ("361", "Vidrio y productos de vidrio"),
    ("362", "Productos cerámicos"),
    ("369", "Otros productos minerales no metálicos"),
    ("37", "Metales básicos"),
    ("371", "Hierro, acero y ferroaleaciones"),
    ("372", "Metales no ferrosos"),
    ("38", "Productos metálicos elaborados, excepto maquinaria y equipo"),
    ("39", "Maquinaria y equipo"),
    ("391", "Maquinaria de uso general"),
    ("392", "Maquinaria de uso especial"),
    # Sección 4 — Equipo de transporte; equipo eléctrico y electrónico de uso final
    ("4", "Equipo de transporte; equipo eléctrico y electrónico de uso final; maquinaria NCP"),
    ("41", "Equipo eléctrico"),
    ("42", "Maquinaria y aparatos de oficina y de informática"),
    ("43", "Equipo de radio, televisión y comunicaciones"),
    ("44", "Equipo médico, de precisión e instrumentos ópticos"),
    ("45", "Vehículos automotores, remolques y semirremolques"),
    ("46", "Otro equipo de transporte"),
    ("47", "Muebles; otros bienes manufacturados"),
    # Sección 5 — Construcción y obras de construcción
    ("5", "Construcción y obras de construcción"),
    ("51", "Estructuras prefabricadas"),
    ("53", "Obras de edificación"),
    ("54", "Obras de ingeniería civil"),
    # Sección 6 — Servicios de distribución; servicios de alojamiento, comidas y bebidas
    ("6", "Servicios de distribución; servicios de alojamiento, comidas y bebidas"),
    ("61", "Servicios de venta al por mayor"),
    ("62", "Servicios de venta al por menor"),
    ("63", "Alojamiento"),
    ("64", "Servicios de comidas y bebidas"),
    # Sección 7 — Servicios de transporte; servicios de almacenamiento y comunicaciones
    ("7", "Servicios de transporte; servicios de almacenamiento y comunicaciones"),
    ("71", "Servicios de transporte por carretera y por tubería"),
    ("72", "Servicios de transporte por agua"),
    ("73", "Servicios de transporte aéreo"),
    ("74", "Servicios de apoyo y auxiliares al transporte"),
    ("75", "Servicios postales y de mensajería"),
    ("76", "Servicios de electricidad, gas y agua"),
    # Sección 8 — Servicios financieros y conexos; servicios inmobiliarios; servicios a las empresas
    ("8", "Servicios financieros; servicios inmobiliarios; servicios a las empresas"),
    ("81", "Servicios financieros"),
    ("82", "Servicios de seguros y de fondos de pensiones"),
    ("83", "Servicios auxiliares de intermediación financiera y seguros"),
    ("84", "Servicios inmobiliarios"),
    ("85", "Servicios jurídicos y contables"),
    ("86", "Servicios de investigación y desarrollo"),
    ("87", "Otros servicios para empresas"),
    # Sección 9 — Servicios comunitarios, sociales y personales
    ("9", "Servicios comunitarios, sociales y personales"),
    ("91", "Servicios de administración pública"),
    ("92", "Servicios de educación"),
    ("93", "Servicios de salud humana y servicios sociales"),
    ("94", "Servicios de alcantarillado; gestión de desechos"),
    ("95", "Servicios de organizaciones de asociación"),
    ("96", "Servicios recreativos, culturales y deportivos"),
    ("97", "Otros servicios"),
    ("98", "Servicios domésticos privados"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in CPC2_CATALOG:
            writer.writerow([code, description])
    print(f"✅ CPC2 — {len(CPC2_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
