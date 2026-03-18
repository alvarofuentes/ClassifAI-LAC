"""
Generador de catálogo ICCS (International Classification of Crime for Statistical Purposes).
Fuente: UNODC. Versión 1.0. Se incluyen niveles 1 (categorías) y 2 (subcategorías).
Salida: data/raw/iccs_es.csv  — formato: id,text
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "data" / "raw" / "iccs_es.csv"

# ICCS 1.0 — Categorías y subcategorías en español
# Fuente: https://www.unodc.org/unodc/en/data-and-analysis/statistics/iccs.html
ICCS_CATALOG = [
    # 01 — Actos que causan muerte o lesiones a personas
    ("01", "Actos que causan muerte o lesiones a la persona"),
    ("0101", "Homicidio intencional"),
    ("0102", "Homicidio no intencional"),
    ("0103", "Feminicidio/femicidio"),
    ("0104", "Lesiones intencionales"),
    ("0105", "Lesiones no intencionales"),
    ("0106", "Participación voluntaria en una pelea"),
    ("0107", "Actos peligrosos o imprudentes que causan la muerte o lesiones"),
    ("0108", "Tráfico de personas"),
    # 02 — Actos que perjudican la integridad personal y atentan contra la libertad y actos sexuales
    ("02", "Actos contra la integridad personal, libertad y actos con connotación sexual"),
    ("0201", "Violación"),
    ("0202", "Agresión sexual"),
    ("0203", "Actos sexuales sin penetración"),
    ("0204", "Actos sexuales mediante engaño y abuso de autoridad"),
    ("0205", "Acoso sexual"),
    ("0206", "Explotación sexual"),
    ("0207", "Producción y distribución de material de abuso sexual infantil"),
    ("0208", "Privación coercitiva de libertad"),
    ("0209", "Privación no coercitiva de libertad"),
    ("0210", "Acoso"),
    ("0211", "Actos de violencia doméstica o familiar"),
    # 03 — Actos de apoderamiento indebido de bienes
    ("03", "Actos de apoderamiento indebido de bienes"),
    ("0301", "Robo con violencia o intimidación"),
    ("0302", "Sustracción de vehículos de motor o a motor"),
    ("0303", "Robo con fuerza en las cosas en lugar habitado o destinado a la habitación"),
    ("0304", "Robo con fuerza en las cosas en otro lugar"),
    ("0305", "Hurto"),
    ("0306", "Apropiación indebida y abuso de confianza"),
    ("0307", "Extorsión"),
    ("0308", "Usurpación de identidad"),
    # 04 — Actos fraudulentos o engañosos
    ("04", "Actos fraudulentos o engañosos"),
    ("0401", "Fraude"),
    ("0402", "Fraude informático y ciberfraude"),
    ("0403", "Fraude en seguros"),
    ("0404", "Falsificación de moneda y otros instrumentos de pago"),
    ("0405", "Falsificación de documentos"),
    ("0406", "Blanqueo de dinero"),
    ("0407", "Delitos de quiebra e insolvencia"),
    # 05 — Actos perjudiciales para el ordenamiento y la autoridad pública
    ("05", "Actos perjudiciales para el ordenamiento y la autoridad pública"),
    ("0501", "Corrupción"),
    ("0502", "Cohecho y soborno"),
    ("0503", "Malversación y apropiación indebida de funciones públicas"),
    ("0504", "Tráfico de influencias"),
    ("0505", "Abuso de poder"),
    ("0506", "Obstrucción a la justicia"),
    ("0507", "Delitos contra el sistema judicial"),
    # 06 — Actos perjudiciales para el orden público, la moral o la convivencia
    ("06", "Actos perjudiciales para el orden público, la moral o la convivencia"),
    ("0601", "Participación en un grupo delictivo organizado"),
    ("0602", "Terrorismo"),
    ("0603", "Tráfico ilícito de armas de fuego"),
    ("0604", "Delitos de odio basados en la discriminación"),
    ("0605", "Delitos contra la privacidad"),
    ("0606", "Pornografía"),
    ("0607", "Juegos de azar ilegales"),
    ("0608", "Disturbios y revueltas"),
    ("0609", "Ofensas al pudor"),
    # 07 — Actos perjudiciales para el medioambiente
    ("07", "Actos perjudiciales para el medioambiente"),
    ("0701", "Delitos contra el medioambiente"),
    ("0702", "Tráfico ilícito de especies de flora y fauna silvestres"),
    ("0703", "Delitos relacionados con residuos peligrosos"),
    ("0704", "Delitos contra el patrimonio cultural"),
    ("0705", "Contaminación ambiental"),
    # 08 — Delitos relacionados con sustancias controladas
    ("08", "Delitos relacionados con sustancias controladas"),
    ("0801", "Tráfico de drogas"),
    ("0802", "Posesión de drogas"),
    ("0803", "Cultivo y fabricación de drogas"),
    ("0804", "Tráfico de precursores de drogas"),
    # 09 — Delitos contra seguridad vial
    ("09", "Delitos relacionados con la seguridad vial y el uso de vehículos"),
    ("0901", "Conducción bajo los efectos del alcohol o drogas"),
    ("0902", "Conducción peligrosa"),
    ("0903", "Homicidio culposo en tráfico"),
    ("0904", "Uso ilícito de vehículos"),
    # 10 — Otros delitos
    ("10", "Otros delitos contra la persona y contra la propiedad"),
    ("1001", "Otros delitos contra la persona"),
    ("1002", "Otros delitos contra la propiedad"),
    ("1003", "Delitos informáticos"),
    ("1004", "Uso no autorizado de datos personales"),
]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text"])
        for code, description in ICCS_CATALOG:
            writer.writerow([code, description])
    print(f"✅ ICCS — {len(ICCS_CATALOG)} entradas escritas en: {OUT_PATH}")


if __name__ == "__main__":
    main()
