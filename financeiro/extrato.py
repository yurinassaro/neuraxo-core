"""
Parser de extratos bancários em CSV, XLSX e PDF.
Retorna lista de dicts: [{'data': date, 'descricao': str, 'valor': Decimal}, ...]
Valor positivo = entrada, negativo = saída.
"""
import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import openpyxl
import pdfplumber


def parse_valor_br(valor_str):
    """Converte valor em formato BR (1.234,56) ou US (1234.56) para Decimal."""
    if not valor_str:
        return None
    s = str(valor_str).strip()
    # Remove R$, espaços
    s = re.sub(r'[R$\s]', '', s)
    if not s:
        return None
    # Detecta formato BR: última vírgula como decimal
    if ',' in s and '.' in s:
        # 1.234,56 -> 1234.56
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        # 1234,56 -> 1234.56
        s = s.replace(',', '.')
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def parse_data_br(data_str):
    """Tenta parsear data em vários formatos brasileiros."""
    if not data_str:
        return None
    if isinstance(data_str, (date, datetime)):
        if isinstance(data_str, datetime):
            return data_str.date()
        return data_str
    s = str(data_str).strip()
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


PALAVRAS_DATA = ['data', 'date', 'dt', 'data mov', 'data movimento', 'data lançamento',
                 'release_date', 'release date']
PALAVRAS_DESC = ['descricao', 'descrição', 'historico', 'histórico', 'description',
                 'lancamento', 'lançamento', 'detalhe', 'memo',
                 'transaction_type', 'transaction type', 'tipo']
PALAVRAS_VALOR = ['valor', 'value', 'amount', 'quantia', 'vlr', 'credito', 'crédito',
                  'transaction_net_amount', 'net_amount', 'net amount']
PALAVRAS_SAIDA = ['debito', 'débito', 'saida', 'saída']


def _detectar_colunas(headers):
    """
    Detecta quais colunas são data, descrição e valor.
    Retorna dict com índices: {'data': int, 'descricao': int, 'valor': int, 'valor_saida': int|None}
    """
    headers_lower = [str(h).lower().strip() for h in headers]
    col = {'data': None, 'descricao': None, 'valor': None, 'valor_saida': None}

    for i, h in enumerate(headers_lower):
        if col['data'] is None and any(p in h for p in PALAVRAS_DATA):
            col['data'] = i
        elif col['descricao'] is None and any(p in h for p in PALAVRAS_DESC):
            col['descricao'] = i
        elif col['valor_saida'] is None and any(p in h for p in PALAVRAS_SAIDA):
            col['valor_saida'] = i
        elif col['valor'] is None and any(p in h for p in PALAVRAS_VALOR):
            col['valor'] = i

    # Fallback: se não detectou, tenta por posição típica (data, desc, valor)
    if col['data'] is None and len(headers) >= 3:
        col['data'] = 0
    if col['descricao'] is None and len(headers) >= 3:
        col['descricao'] = 1
    if col['valor'] is None and len(headers) >= 3:
        col['valor'] = len(headers) - 1

    return col


def _is_header_row(row):
    """Verifica se uma linha parece ser um header de dados (tem palavras-chave de colunas)."""
    if not row:
        return False
    cells = [str(c).lower().strip() for c in row if c is not None]
    todas_palavras = PALAVRAS_DATA + PALAVRAS_DESC + PALAVRAS_VALOR + PALAVRAS_SAIDA
    matches = sum(1 for c in cells if any(p in c for p in todas_palavras))
    return matches >= 2


def _encontrar_header(rows):
    """
    Encontra a linha de header real nos dados.
    Extratos como Mercado Pago têm linhas de resumo antes do header real.
    Retorna (indice_header, header_row).
    """
    for i, row in enumerate(rows):
        if row and _is_header_row(row):
            return i, row
    return 0, rows[0] if rows else []


def _rows_para_lancamentos(rows):
    """Converte linhas (list de lists) em lista de lançamentos."""
    if not rows or len(rows) < 2:
        return []

    # Encontra a linha de header real (pode não ser a primeira)
    header_idx, headers = _encontrar_header(rows)
    col = _detectar_colunas(headers)
    lancamentos = []

    for row in rows[header_idx + 1:]:
        if not row or all(c is None or not str(c).strip() for c in row):
            continue

        try:
            data = parse_data_br(row[col['data']]) if col['data'] is not None and col['data'] < len(row) else None
            descricao = str(row[col['descricao']]).strip() if col['descricao'] is not None and col['descricao'] < len(row) else ''
            valor = parse_valor_br(row[col['valor']]) if col['valor'] is not None and col['valor'] < len(row) else None

            # Coluna separada de débito
            if col['valor_saida'] is not None and col['valor_saida'] < len(row):
                val_saida = parse_valor_br(row[col['valor_saida']])
                if val_saida and val_saida > 0:
                    valor = -val_saida
                elif valor is None:
                    continue

            if data and valor and descricao:
                lancamentos.append({
                    'data': data,
                    'descricao': descricao[:300],
                    'valor': valor,
                })
        except (IndexError, TypeError):
            continue

    return lancamentos


def parse_csv(file_obj):
    """Parseia extrato CSV. Aceita ; ou , como delimitador."""
    content = file_obj.read()
    if isinstance(content, bytes):
        for encoding in ('utf-8', 'latin-1', 'cp1252'):
            try:
                content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

    # Detecta delimitador
    dialect = csv.Sniffer().sniff(content[:2000], delimiters=',;\t')
    reader = csv.reader(io.StringIO(content), dialect)
    rows = [row for row in reader if row]
    return _rows_para_lancamentos(rows)


def parse_xlsx(file_obj):
    """Parseia extrato XLSX."""
    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))
    wb.close()
    return _rows_para_lancamentos(rows)


def parse_pdf(file_obj):
    """Parseia extrato PDF extraindo tabelas."""
    lancamentos = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    lancamentos.extend(_rows_para_lancamentos(table))

    # Se não encontrou tabelas, tenta extrair texto linha por linha
    if not lancamentos:
        lancamentos = _parse_pdf_texto(file_obj)

    return lancamentos


def _parse_pdf_texto(file_obj):
    """Fallback: extrai lançamentos do texto do PDF por regex."""
    lancamentos = []
    # Padrão típico: DD/MM/YYYY  DESCRIÇÃO  VALOR
    padrao = re.compile(
        r'(\d{2}/\d{2}/\d{4})\s+'  # data
        r'(.+?)\s+'                  # descrição
        r'(-?\s*[\d.,]+)\s*$'        # valor
    )
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.split('\n'):
                m = padrao.search(line.strip())
                if m:
                    data = parse_data_br(m.group(1))
                    descricao = m.group(2).strip()
                    valor = parse_valor_br(m.group(3))
                    if data and valor and descricao:
                        lancamentos.append({
                            'data': data,
                            'descricao': descricao[:300],
                            'valor': valor,
                        })
    return lancamentos


def parse_extrato(file_obj, filename):
    """Parseia extrato baseado na extensão do arquivo."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if ext == 'csv':
        return parse_csv(file_obj)
    elif ext in ('xlsx', 'xls'):
        return parse_xlsx(file_obj)
    elif ext == 'pdf':
        return parse_pdf(file_obj)
    else:
        raise ValueError(f'Formato não suportado: .{ext}. Use CSV, XLSX ou PDF.')
