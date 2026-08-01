from __future__ import annotations

from datetime import datetime, timezone
import json
import random
import re
from typing import Any

from pydantic import BaseModel, Field


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"


class CandidateEvaluation(BaseModel):
    id: str = Field(description="Opaque candidate ID supplied in the prompt.")
    global_importance: int = Field(ge=0, le=100)
    reader_relevance: int = Field(ge=0, le=100)
    substantive_value: int = Field(ge=0, le=100)
    event_key: str = Field(min_length=3, max_length=140)
    reason: str = Field(min_length=3, max_length=180)


class EditorialEvaluation(BaseModel):
    evaluations: list[CandidateEvaluation]


class EditedStory(BaseModel):
    id: str = Field(description="Opaque story ID supplied in the prompt.")
    title_es: str = Field(min_length=4, max_length=190)
    summary_es: str = Field(min_length=20, max_length=760)


class EditorialBatch(BaseModel):
    stories: list[EditedStory]


def _age_hours(item: dict, now: datetime) -> float | None:
    published = item.get("published_at")
    if published is None:
        return None
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    return max(
        0.0,
        (
            now.astimezone(timezone.utc)
            - published.astimezone(timezone.utc)
        ).total_seconds()
        / 3600,
    )


def _candidate_payload(
    items: list[dict],
    now: datetime,
) -> tuple[list[dict], dict[str, dict]]:
    prepared: list[dict] = []
    id_to_item: dict[str, dict] = {}

    for index, item in enumerate(items, start=1):
        candidate_id = f"N{index:02d}"
        copy = dict(item)
        copy["_ai_id"] = candidate_id
        id_to_item[candidate_id] = copy

        age = _age_hours(item, now)
        prepared.append(
            {
                "id": candidate_id,
                "region": str(item.get("region", "")),
                "source": str(item.get("source", "")),
                "title": str(item.get("title", ""))[:280],
                "summary": str(item.get("summary", ""))[:420],
                "hours_since_publication": round(age, 1) if age is not None else None,
            }
        )

    # Stable three-hour shuffle prevents position bias.
    bucket = int(now.timestamp() // 10_800)
    random.Random(bucket).shuffle(prepared)
    return prepared, id_to_item


def _build_ranking_prompt(candidates: list[dict]) -> str:
    return f"""
Actúa como editor jefe de un briefing minero profesional de lectura inferior a cinco minutos.
Evalúa TODAS las noticias de forma independiente. La posición es aleatoria: no premies las
primeras noticias ni asumas que el orden expresa importancia.

Lector objetivo:
- Estudiante de Ingeniería Civil de Minas en Chile.
- Prioridades: minería subterránea, cobre, planificación minera, geomecánica, seguridad,
  automatización, IA aplicada, productividad, proyectos e inversiones de gran escala,
  mercado del cobre y hechos que cambien decisiones operacionales o económicas.

Criterios:
1. global_importance: magnitud económica u operacional, toneladas, inversión, producción,
   regulación, accidentes graves, cambios de mercado, proyectos estructurales o tecnología real.
2. reader_relevance: utilidad concreta para el lector descrito.
3. substantive_value: premia cifras, decisiones, resultados y consecuencias. Penaliza premios,
   ceremonias, nombramientos, promoción y notas sin hechos concretos.
4. event_key: noticias sobre el mismo hecho deben usar EXACTAMENTE la misma clave.
5. Usa solo título, resumen, fuente, región y antigüedad entregados. No inventes ni navegues.
6. Devuelve cada ID exactamente una vez.

Candidatos:
{json.dumps(candidates, ensure_ascii=False, separators=(",", ":"))}
""".strip()


def evaluate_with_gemini(
    items: list[dict],
    *,
    now: datetime,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> tuple[list[dict], str | None]:
    if not api_key or not items:
        return items, None

    try:
        from google import genai
    except ImportError as exc:
        return items, f"Google GenAI SDK no disponible: {type(exc).__name__}"

    candidates, id_to_item = _candidate_payload(items, now)
    client: Any = None

    try:
        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(
            model=model,
            input=_build_ranking_prompt(candidates),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": EditorialEvaluation.model_json_schema(),
            },
        )
        result = EditorialEvaluation.model_validate_json(interaction.output_text)
    except Exception as exc:
        return items, f"{type(exc).__name__}: {str(exc)[:140]}"
    finally:
        if client is not None and hasattr(client, "close"):
            try:
                client.close()
            except Exception:
                pass

    evaluations: dict[str, CandidateEvaluation] = {}
    for evaluation in result.evaluations:
        if evaluation.id in id_to_item and evaluation.id not in evaluations:
            evaluations[evaluation.id] = evaluation

    ranked: list[dict] = []
    for candidate_id, item in id_to_item.items():
        evaluation = evaluations.get(candidate_id)
        merged = dict(item)
        merged.pop("_ai_id", None)

        if evaluation is not None:
            merged.update(
                {
                    "ai_global_importance": evaluation.global_importance,
                    "ai_reader_relevance": evaluation.reader_relevance,
                    "ai_substantive_value": evaluation.substantive_value,
                    "ai_event_key": evaluation.event_key,
                    "ai_reason": evaluation.reason,
                }
            )

        ranked.append(merged)

    evaluated_count = sum(
        1
        for item in ranked
        if item.get("ai_global_importance") is not None
    )
    if evaluated_count < max(3, int(len(items) * 0.7)):
        return items, "Gemini devolvió una evaluación incompleta; se usó ranking local."

    return ranked, None


def _editorial_payload(
    items: list[dict],
) -> tuple[list[dict], dict[str, dict]]:
    payload: list[dict] = []
    id_to_item: dict[str, dict] = {}

    for index, item in enumerate(items, start=1):
        story_id = f"E{index:02d}"
        id_to_item[story_id] = dict(item)
        payload.append(
            {
                "id": story_id,
                "region": str(item.get("region", "")),
                "source": str(item.get("source", "")),
                "category": str(item.get("category", "")),
                "title": str(item.get("title", ""))[:300],
                "summary": str(item.get("summary", ""))[:700],
            }
        )

    return payload, id_to_item


def _build_editorial_prompt(stories: list[dict]) -> str:
    return f"""
Actúa como editor de Radar Minero, un briefing móvil profesional para un estudiante chileno
de Ingeniería Civil de Minas. Edita TODAS las historias seleccionadas en español claro.

Objetivo de cada tarjeta:
- Entender el hecho central en menos de 20 segundos.
- Mantener un tono sobrio, técnico y periodístico.
- Dar una extensión visual consistente entre tarjetas.

Reglas para title_es:
1. Entre 7 y 18 palabras cuando la información lo permita.
2. Conserva empresa, proyecto, mineral o país esenciales.
3. Usa verbo concreto; elimina frases promocionales, mayúsculas innecesarias y clickbait.
4. No agregues hechos ni interpretaciones.

Reglas para summary_es:
1. Apunta a 55-85 palabras, en 2 o 3 oraciones.
2. Explica qué ocurrió, quién está involucrado y qué cambia operacional o económicamente.
3. Incluye cifras, fechas, ubicaciones y consecuencias SOLO si aparecen en el material entregado.
4. Si el material es demasiado breve, escribe 30-50 palabras y NO rellenes con suposiciones.
5. No uses frases como “la noticia destaca”, “este artículo aborda” o “según el comunicado”.
6. No emitas opinión, recomendación ni una sección separada de “por qué importa”.
7. No copies una oración larga literalmente; reformula sin alterar el significado.
8. Las historias internacionales deben quedar traducidas a español natural.
9. Devuelve cada ID exactamente una vez y sin markdown.

Material disponible:
{json.dumps(stories, ensure_ascii=False, separators=(",", ":"))}
""".strip()


def _normalized_number_tokens(value: str) -> set[str]:
    tokens = re.findall(
        r"(?<![A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\d+(?:[.,]\d+)*(?:\s?%)?",
        value or "",
    )
    normalized: set[str] = set()

    for token in tokens:
        compact = re.sub(r"\s+", "", token)
        percent = compact.endswith("%")
        compact = compact.rstrip("%")
        digits = re.sub(r"[.,]", "", compact).lstrip("0") or "0"
        normalized.add(digits + ("%" if percent else ""))

    return normalized


def _word_count(value: str) -> int:
    return len(re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ'-]+\b", value or ""))


def _is_grounded_edit(
    *,
    original: dict,
    edited: EditedStory,
) -> tuple[bool, str | None]:
    title = " ".join(edited.title_es.split()).strip()
    summary = " ".join(edited.summary_es.split()).strip()

    title_words = _word_count(title)
    summary_words = _word_count(summary)

    if not 4 <= title_words <= 24:
        return False, "extensión de título fuera de rango"
    if not 25 <= summary_words <= 105:
        return False, "extensión de resumen fuera de rango"

    source_text = f"{original.get('title', '')} {original.get('summary', '')}"
    output_text = f"{title} {summary}"

    source_numbers = _normalized_number_tokens(source_text)
    output_numbers = _normalized_number_tokens(output_text)
    invented_numbers = output_numbers - source_numbers

    if invented_numbers:
        return False, "introdujo cifras no presentes en la fuente"

    banned_phrases = (
        "la noticia destaca",
        "este artículo",
        "este articulo",
        "en conclusión",
        "en conclusion",
        "por qué importa",
        "por que importa",
    )
    lowered = summary.lower()
    if any(phrase in lowered for phrase in banned_phrases):
        return False, "incluyó lenguaje editorial no deseado"

    return True, None


def _apply_editorial_edits(
    items: list[dict],
    edits: list[EditedStory],
) -> tuple[list[dict], int, list[str]]:
    id_to_item = {
        f"E{index:02d}": dict(item)
        for index, item in enumerate(items, start=1)
    }
    edit_by_id: dict[str, EditedStory] = {}

    for edit in edits:
        if edit.id in id_to_item and edit.id not in edit_by_id:
            edit_by_id[edit.id] = edit

    output: list[dict] = []
    edited_count = 0
    rejection_reasons: list[str] = []

    for story_id, item in id_to_item.items():
        edit = edit_by_id.get(story_id)
        merged = dict(item)

        if edit is not None:
            valid, reason = _is_grounded_edit(original=item, edited=edit)
            if valid:
                merged["source_title"] = merged.get("title", "")
                merged["source_summary"] = merged.get("summary", "")
                merged["title"] = " ".join(edit.title_es.split()).strip()
                merged["summary"] = " ".join(edit.summary_es.split()).strip()
                merged["editorialized"] = True
                edited_count += 1
            elif reason:
                rejection_reasons.append(f"{story_id}: {reason}")

        output.append(merged)

    return output, edited_count, rejection_reasons


def editorialize_selected_stories(
    items: list[dict],
    *,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> tuple[list[dict], str | None, int]:
    """
    Edit only the final selected feed in one grouped request.

    Any story that fails factual or length validation keeps its original text.
    """
    if not api_key or not items:
        return items, None, 0

    try:
        from google import genai
    except ImportError as exc:
        return items, f"Google GenAI SDK no disponible: {type(exc).__name__}", 0

    payload, _ = _editorial_payload(items)
    client: Any = None

    try:
        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(
            model=model,
            input=_build_editorial_prompt(payload),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": EditorialBatch.model_json_schema(),
            },
        )
        result = EditorialBatch.model_validate_json(interaction.output_text)
    except Exception as exc:
        return items, f"{type(exc).__name__}: {str(exc)[:140]}", 0
    finally:
        if client is not None and hasattr(client, "close"):
            try:
                client.close()
            except Exception:
                pass

    output, edited_count, rejection_reasons = _apply_editorial_edits(
        items,
        result.stories,
    )

    if edited_count == len(items):
        return output, None, edited_count

    if edited_count == 0:
        return items, "Gemini no entregó resúmenes editoriales válidos; se conservó el texto original.", 0

    detail = rejection_reasons[0] if rejection_reasons else "respuesta parcial"
    return (
        output,
        f"Gemini editó {edited_count}/{len(items)} historias; el resto conservó su texto original ({detail}).",
        edited_count,
    )
