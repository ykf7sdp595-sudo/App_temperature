"""Lecture des enregistrements et calcul des points de dérating."""
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from math import isfinite
from numbers import Real
import re

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

PALIER = (20, 40, 60, 80, 100, 120)


@dataclass
class Recording:
    name: str
    headers: list
    times: list
    columns: dict
    markers: dict
    warnings: list


def numeric(value):
    return isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)


def read_recording(content, name):
    book = load_workbook(BytesIO(content), read_only=True, data_only=True, keep_links=False)
    try:
        if 'Enregistrement' in book.sheetnames:
            sheet = book['Enregistrement']
        elif name.lower() == 'forme_data.xlsm' and 'Feuil1' in book.sheetnames:
            sheet = book['Feuil1']
        else:
            raise ValueError("Feuille 'Enregistrement' introuvable.")
        rows = sheet.iter_rows(values_only=True)
        header = list(next(rows, ()))
        if len(header) < 2:
            raise ValueError('En-têtes de voies absents.')
        next(rows, None)
        next(rows, None)  # ligne 3 exclue
        columns = {i: [] for i in range(1, len(header)) if i != 15}
        times, markers, warnings = [], {}, []
        seen = set()
        last = None
        rejected = 0
        invalid = 0
        for row_number, row in enumerate(rows, 4):
            raw = row[0] if row else None
            try:
                date = from_excel(raw, book.epoch) if numeric(raw) else raw
            except (ValueError, OverflowError):
                date = None
            if not isinstance(date, datetime) or date in seen or (last is not None and date < last):
                rejected += 1
                continue
            times.append(date)
            seen.add(date)
            last = date
            for i, values in columns.items():
                value = row[i] if i < len(row) else None
                values.append(float(value) if numeric(value) else None)
                if value is not None and not numeric(value):
                    invalid += 1
            marker = row[15] if len(row) > 15 else None
            match = re.search(r'(020|040|060|080|100|120)\s*$', marker) if isinstance(marker, str) else None
            if match:
                temperature = int(match.group(1))
                if temperature in markers:
                    warnings.append(f'Palier {temperature} °C répété : première occurrence conservée.')
                else:
                    markers[temperature] = len(times) - 1
        if rejected:
            warnings.append(f'{rejected} ligne(s) exclue(s) : date absente, doublon ou retour en arrière.')
        if invalid:
            warnings.append(f'{invalid} valeur(s) non numérique(s) ignorée(s).')
        return Recording(name, header, times, columns, markers, warnings)
    finally:
        book.close()


def derating(recordings, current_columns):
    curves, diagnostics = {}, []
    for rec, current in zip(recordings, current_columns):
        values = rec.columns.get(current, [])
        points = {}
        for temp in PALIER:
            index = rec.markers.get(temp)
            if index is not None and index < len(values) and values[index] is not None:
                points[temp] = values[index]
            else:
                diagnostics.append(f'{rec.name} : point {temp} °C indisponible.')
        curves[rec.name] = points
    result = {}
    for temp in PALIER:
        available = [points[temp] for points in curves.values() if temp in points]
        if available:
            result[temp] = (min(available) * 0.8, len(available))
        else:
            diagnostics.append(f'{temp} °C : aucun courant disponible.')
    return curves, result, diagnostics


def active_columns(recording):
    return [i for i, values in recording.columns.items() if any(v is not None and v != 0 for v in values)]

