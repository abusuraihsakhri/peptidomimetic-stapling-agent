"""Sequence-position enumeration for potential i,i+4 and i,i+7 staples.

This is a geometric index screen, not an assessment of staple synthesis,
conformational stability, hydrophobicity, binding, or membrane permeability.
"""
from typing import Dict, List, Sequence

AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")


def enumerate_staple_sites(sequence: str, spacings: Sequence[int] = (4, 7)) -> List[Dict[str, object]]:
    """Return one-based position pairs for canonical peptide sequences.

    Positions are candidates for further analysis only; no stereochemical,
    steric, biological or chemical compatibility is inferred.
    """
    if not isinstance(sequence, str):
        raise ValueError("Sequence must be text")
    cleaned = "".join(sequence.split()).upper()
    if not cleaned or len(cleaned) > 500:
        raise ValueError("Sequence length must be between 1 and 500 residues")
    if any(residue not in AMINO_ACIDS for residue in cleaned):
        raise ValueError("Use canonical one-letter amino-acid codes only")
    if not spacings or any(type(spacing) is not int or spacing not in (4, 7) for spacing in spacings):
        raise ValueError("Spacings must be 4, 7, or both")
    results = []
    for spacing in dict.fromkeys(spacings):
        for index in range(len(cleaned) - spacing):
            between = cleaned[index:index + spacing + 1]
            results.append({
                "start_position": index + 1,
                "end_position": index + spacing + 1,
                "spacing": f"i,i+{spacing}",
                "native_residues": f"{cleaned[index]}-{cleaned[index + spacing]}",
                "contains_proline": "P" in between,
            })
    return results
