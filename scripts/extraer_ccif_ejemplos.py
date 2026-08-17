#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae de ccif_2018-cl-alimentos-bebidas.pdf una tabla de ejemplos etiquetados
con su codigo CCIF 2018.CL.

Salida CSV: codigo_ccif, nivel, ejemplo, tipo, frase_original
"""
import re, csv, sys
import pdfplumber

PDF = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/ClassifAI-LAC/ccif_2018-cl-alimentos-bebidas.pdf'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/ccif_2018_cl_ejemplos.csv'

RUNNING = {'ALIMENTOS Y BEBIDAS NO ALCOHÓLICAS',
           'BEBIDAS ALCOHÓLICAS, TABACO Y ESTUPEFACIENTES',
           'SERVICIOS DE RESTAURANTES Y ALOJAMIENTO',
           'PRESENTACIÓN DEL CLASIFICADOR'}

COD = r'\d{2}\.\d\.\d\.\d{2}\.\d{2}'
RE_HEAD = re.compile(r'^(División|Grupo|Clase|Subclase|Producto)\s+(' + COD + r')\s*$')
RE_BLOCK = re.compile(r'^(También incluye|Incluye|Excluye)\s*:\s*$', re.I)
RE_COD = re.compile(COD)


def nivel_de(cod):
    d, g, c, s, p = cod.split('.')
    if p != '00':
        return 'Producto'
    if s != '00':
        return 'Subclase'
    if c != '0':
        return 'Clase'
    if g != '0':
        return 'Grupo'
    return 'División'


# ---------------------------------------------------------------- 1. lineas
def leer_lineas(pdf):
    lineas = []
    with pdfplumber.open(pdf) as doc:
        for pg in doc.pages:
            for ln in (pg.extract_text() or '').split('\n'):
                ln = ln.strip()
                if not ln or ln in RUNNING or re.fullmatch(r'\d{1,4}', ln):
                    continue
                lineas.append(ln)
    return lineas


# ------------------------------------------------- 2. recorrido jerarquico
def recorrer(lineas):
    """Devuelve lista de (codigo_vigente, tipo_bloque, frase_bullet)."""
    registros = []
    cod_actual = None
    bloque = None
    buf = []

    def cerrar():
        nonlocal buf
        if buf:
            frase = ' '.join(buf).strip()
            frase = re.sub(r'\s+', ' ', frase).rstrip(' ;.')
            if frase:
                registros.append((cod_actual, bloque, frase))
        buf = []

    i = 0
    while i < len(lineas):
        ln = lineas[i]
        h = RE_HEAD.match(ln)
        if h:
            cerrar()
            cod_actual = h.group(2)
            bloque = None
            i += 2          # salta la glosa (linea siguiente)
            # glosas de 2 lineas: si la linea saltada no cerraba, no importa
            continue
        b = RE_BLOCK.match(ln)
        if b:
            cerrar()
            bloque = b.group(1).lower()
            i += 1
            continue
        if ln.startswith('-') or ln.startswith('–'):
            cerrar()
            if bloque:
                buf = [ln.lstrip('-– ').strip()]
            i += 1
            continue
        # continuacion de un bullet abierto
        if buf:
            buf.append(ln)
        else:
            # parrafo descriptivo fuera de bullets -> cierra el bloque
            bloque = None
        i += 1
    cerrar()
    return registros


# ------------------------------------------------------ 3. split de frases
MODIF = {'grado', 'grados', 'tipo', 'tipos', 'clase', 'clases', 'calidad',
         'calidades', 'variedad', 'variedades', 'formato', 'formatos',
         'sabor', 'sabores', 'tamaño', 'tamaños', 'corte', 'cortes',
         'presentación', 'presentaciones', 'marca', 'marcas', 'número'}

ADJ_SOLOS = {'largo', 'larga', 'corto', 'corta', 'partido', 'partida',
             'entero', 'entera', 'enteros', 'enteras', 'molido', 'molida',
             'seco', 'seca', 'secos', 'secas', 'fresco', 'fresca', 'frescos',
             'frescas', 'congelado', 'congelada', 'congelados', 'congeladas',
             'crudo', 'cruda', 'cocido', 'cocida', 'natural', 'naturales',
             'instantáneo', 'instantánea', 'pequeño', 'grande', 'mediano',
             'blanco', 'blanca', 'negro', 'negra', 'rojo', 'roja', 'verde',
             'similares', 'otros', 'otras', 'demás', 'etc', 'etcétera',
             'nuevo', 'nueva', 'usado', 'usada', 'simple', 'doble',
             'caliente', 'frío', 'fría', 'dulce', 'salado', 'salada'}
ADJ_SOLOS |= {'refrigerado', 'refrigerada', 'enfriado', 'enfriada',
              'envasado', 'envasada', 'precocido', 'precocida',
              'deshidratado', 'deshidratada', 'endulzado', 'endulzada',
              'saborizado', 'saborizada', 'descremado', 'descremada'}
ADJ_SOLOS |= {a + 's' for a in ADJ_SOLOS} | {a + 'es' for a in ADJ_SOLOS}
# sustantivos de clasificacion que quedan sueltos al partir enumeraciones
ADJ_SOLOS |= {'denominación', 'denominaciones', 'presentación',
              'presentaciones', 'variante', 'variantes', 'combinación',
              'combinaciones', 'origen', 'orígenes', 'modalidad',
              'modalidades', 'versión', 'versiones', 'formato', 'formatos',
              'estén', 'sean', 'vengan', 'estar', 'ser', 'similares'}

INICIO_MALO = re.compile(
    r'^(?:que|cuando|donde|si|sea|sean|ya|así|tal|tales|siempre|aunque|'
    r'salvo|excepto|incluso|además|también|etc|es|son|su|sus|'
    r'de|del|en|con|sin|para|por|al|a|los|las|el|la|un|una|lo|se|no|'
    r'más|menos|pero|como|entre|sobre|desde|hasta|durante|mediante|según|'
    r'incluid[oa]s?|incluyendo|excluid[oa]s?|siendo|estando|cuy[oa]s?|'
    r'destinad[oa]s?|provenientes|obtenid[oa]s?)\b', re.I)


MAP_PROT = {',': '\x00', ';': '\x01', ' ': '\x02', '/': '\x03', ':': '\x04'}
MAP_REST = {v: k for k, v in MAP_PROT.items()}


def proteger(frase):
    """Neutraliza separadores dentro de parentesis (incluye espacios, para que
    ' y ' / ' o ' tampoco corten dentro del parentesis)."""
    out, prof = [], 0
    for ch in frase:
        if ch == '(':
            prof += 1
            out.append(ch)
            continue
        if ch == ')':
            prof = max(0, prof - 1)
            out.append(ch)
            continue
        out.append(MAP_PROT[ch] if (prof > 0 and ch in MAP_PROT) else ch)
    return ''.join(out)


def restaurar(s):
    for k, v in MAP_REST.items():
        s = s.replace(k, v)
    return s


def equilibrar(s):
    """Elimina parentesis sueltos en los extremos."""
    while s.count(')') > s.count('(') and s.endswith(')'):
        s = s[:-1].strip()
    while s.count('(') > s.count(')') and s.startswith('('):
        s = s[1:].strip()
    if s.count('(') > s.count(')'):
        s = s[:s.rindex('(')].strip(' .,;:')
    if s.count(')') > s.count('('):
        s = s.replace(')', '').strip()
    return s


RE_SEP = re.compile(r'\s*;\s*|\s*,\s*|\s*:\s*|\s+y\s+|\s+e\s+|\s+o\s+|\s+u\s+|\s*/\s*')

STOP_SOLO = {'con', 'sin', 'de', 'del', 'en', 'para', 'por', 'al', 'a', 'y',
             'o', 'u', 'e', 'etc', 'más', 'menos', 'solo', 'sólo', 'cuyo',
             'cuya', 'su', 'sus', 'lo', 'la', 'el', 'los', 'las', 'un', 'una',
             'ya', 'sea', 'entre', 'tanto', 'así', 'tal', 'tales', 'mismo',
             'misma', 'otro', 'otra', 'ambos', 'ambas', 'ello', 'esto', 'ese',
             'este', 'esta', 'esa', 'aquel', 'cual', 'cuales', 'donde',
             'ambas', 'todo', 'toda', 'todos', 'todas', 'cada', 'ni', 'que'}


RE_EJEMPLIF = re.compile(
    r'\s+(?:como|por ejemplo|tales como|tal como|entre ellos|entre otros|'
    r'es decir|a saber|denominad[oa]s?)[,:]?\s+', re.I)

HEREDAR_DE = False


def dividir(frase):
    f = proteger(frase)
    # quita muletillas de encabezado de lista
    f = re.sub(r'^(por ejemplo|tales como|como|a saber)[,:]?\s+', '', f, flags=re.I)
    partes = []
    for bruto in RE_SEP.split(f):
        for sub in RE_EJEMPLIF.split(restaurar(bruto)):
            partes.append(sub.strip(' .;:'))
    items, vistos = [], set()
    cabeza = [None]
    for p in partes:
        if not p or len(p) < 3:
            continue
        pl = p.lower()
        if not re.search(r'[a-záéíóúñü]', pl):
            continue
        if INICIO_MALO.match(pl):
            continue
        toks = re.findall(r'[\wáéíóúñü]+', pl)
        if not toks:
            continue
        if toks[0] in MODIF and len(toks) <= 2:
            continue
        if len(toks) == 1 and (toks[0] in ADJ_SOLOS or toks[0] in STOP_SOLO):
            continue
        if pl in ('etc', 'etcétera', 'n.c.p', 'ncp'):
            continue
        p = equilibrar(re.sub(r'\s+', ' ', p).strip(' .;:,'))
        p = re.sub(r'\s+(?:y|o|e|u)$', '', p, flags=re.I).strip(' .;:,')
        # elipsis del nucleo: "mermelada de durazno, mora, naranja"
        #                  -> "mermelada de mora", "mermelada de naranja"
        if HEREDAR_DE:
            if not items:   # solo el primer item de la vineta fija el nucleo
                m = re.fullmatch(r'(.{3,}? de )([\wáéíóúñü-]+)', p)
                cabeza[0] = m.group(1) if m else None
            elif cabeza[0] and re.fullmatch(r'[\wáéíóúñü-]+', p) and len(p) > 3:
                p = cabeza[0] + p
        pl = p.lower()
        if len(p) < 3 or (len(re.findall(r'[\wáéíóúñü]+', pl)) == 1
                          and pl in (ADJ_SOLOS | STOP_SOLO)):
            continue
        if p and pl not in vistos:
            vistos.add(pl)
            items.append(p)
    return items


# ---------------------------------------------------------------- 4. main
def main():
    lineas = leer_lineas(PDF)
    regs = recorrer(lineas)
    filas = []
    sin_codigo = []
    for cod_ctx, bloque, frase in regs:
        if bloque and bloque.startswith('excluye'):
            tipo = 'excluido'
            cods = RE_COD.findall(frase)
            if not cods:
                sin_codigo.append((cod_ctx, frase))
                continue
            cod = cods[-1]
            # limpia la referencia de codigo del texto
            texto = re.sub(r'\s*\((?:[^()]*' + COD + r'[^()]*)\)\s*$', '', frase).strip(' .;,')
            texto = re.sub(r'\s*\(\s*(?:división|grupo|clase|subclase|producto)?\s*'
                           + COD + r'\s*\)', '', texto, flags=re.I).strip(' .;,')
        else:
            tipo = 'incluido'
            cod = cod_ctx
            texto = frase
        if not cod:
            continue
        for it in dividir(texto):
            filas.append({'codigo_ccif': cod, 'nivel': nivel_de(cod),
                          'ejemplo': it, 'tipo': tipo, 'frase_original': frase})

    # dedup exacto (mismo codigo + ejemplo + tipo)
    vistos, out = set(), []
    for f in filas:
        k = (f['codigo_ccif'], f['ejemplo'].lower(), f['tipo'])
        if k in vistos:
            continue
        vistos.add(k)
        out.append(f)

    with open(OUT, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=['codigo_ccif', 'nivel', 'ejemplo',
                                           'tipo', 'frase_original'])
        w.writeheader()
        w.writerows(out)

    print('bullets:', len(regs), '| filas:', len(out),
          '| exclusiones sin codigo:', len(sin_codigo))
    for c, f in sin_codigo[:15]:
        print('   SINCOD', c, '|', f[:110])


if __name__ == '__main__':
    main()
