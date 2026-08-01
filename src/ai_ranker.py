from __future__ import annotations

from datetime import datetime, timezone
import json
import random
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


class StoryTranslation(BaseModel):
    id: str = Field(description="Opaque story ID supplied in the prompt.")
    title_es: str = Field(min_length=4, max_length=180)
    summary_es: str = Field(min_length=20, max_length=520)


class TranslationBatch(BaseModel):
    translations: list[StoryTranslation]


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

    # Stable three-hour shuffle prevents source-page and pre-ranking position bias.
    bucket = int(now.timestamp() // 10_800)
    random.Random(bucket).shuffle(prepared)
    return prepared, id_to_item


def _build_prompt(candidates: list[dict]) -> str:
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
            input=_build_prompt(candidates),
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
        1 for item in ranked
        if item.get("ai_global_importance") is not None
    )
    if evaluated_count < max(3, int(len(items) * 0.7)):
        return items, "Gemini devolvió una evaluación incompleta; se usó ranking local."

    return ranked, None


def _translation_prompt(stories: list[dict]) -> str:
    return f"""
Traduce y edita estas noticias mineras internacionales para un lector chileno.

Reglas:
- Mantén estrictamente los hechos entregados.
- No agregues contexto externo, causas, cifras ni conclusiones no presentes.
- title_es: título natural y profesional en español, sin sensacionalismo.
- summary_es: resumen claro de 2 a 3 oraciones y máximo 90 palabras.
- Conserva nombres propios de compañías, proyectos y lugares.
- Devuelve cada ID exactamente una vez y sin markdown.

Historias:
{json.dumps(stories, ensure_ascii=False, separators=(",", ":"))}
""".strip()


def translate_selected_world_stories(
    items: list[dict],
    *,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> tuple[list[dict], str | None]:
    if not api_key or not items:
        return items, None

    try:
        from google import genai
    except ImportError as exc:
        return items, f"Google GenAI SDK no disponible: {type(exc).__name__}"

    payload: list[dict] = []
    id_to_item: dict[str, dict] = {}

    for index, item in enumerate(items, start=1):
        story_id = f"W{index:02d}"
        id_to_item[story_id] = dict(item)
        payload.append(
            {
                "id": story_id,
                "source": str(item.get("source", "")),
                "title": str(item.get("title", ""))[:280],
                "summary": str(item.get("summary", ""))[:520],
            }
        )

    client: Any = None
    try:
        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(
            model=model,
            input=_translation_prompt(payload),
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": TranslationBatch.model_json_schema(),
            },
        )
        result = TranslationBatch.model_validate_json(interaction.output_text)
    except Exception as exc:
        return items, f"{type(exc).__name__}: {str(exc)[:140]}"
    finally:
        if client is not None and hasattr(client, "close"):
            try:
                client.close()
            except Exception:
                pass

    translated_by_id = {
        translation.id: translation
        for translation in result.translations
        if translation.id in id_to_item
    }

    output: list[dict] = []
    for story_id, item in id_to_item.items():
        translation = translated_by_id.get(story_id)
        merged = dict(item)

        if translation is not None:
            merged["original_title"] = merged.get("title", "")
            merged["original_summary"] = merged.get("summary", "")
            merged["title"] = translation.title_es.strip()
            merged["summary"] = translation.summary_es.strip()
            merged["translated_to_spanish"] = True

        output.append(merged)

    if len(translated_by_id) < len(items):
        return output, "Gemini tradujo solo parte del bloque internacional."

    return output, None
