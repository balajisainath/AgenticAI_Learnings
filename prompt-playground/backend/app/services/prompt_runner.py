import json
import time
import uuid

from langchain.schema import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.database import get_db
from app.services.llm_factory import build_chat_model


async def execute_prompt(
    system_prompt: str,
    user_prompt_template: str,
    input_text: str,
    variables: dict,
    model: str = "",
    temperature: float = 0.7,
) -> dict:
    settings = get_settings()
    llm = build_chat_model(settings, model_override=model, temperature_override=temperature)
    if not llm:
        raise ValueError(f"Could not initialize LLM. Check API keys for provider: {settings.normalized_provider}")

    # Format the user prompt with variables
    formatted_user_prompt = user_prompt_template
    all_vars = {**variables, "input": input_text}
    for key, value in all_vars.items():
        formatted_user_prompt = formatted_user_prompt.replace(f"{{{{{key}}}}}", str(value))

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=formatted_user_prompt))

    start_time = time.time()
    response = llm.invoke(messages)
    latency_ms = int((time.time() - start_time) * 1000)

    output_text = response.content
    token_count = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        token_count = response.usage_metadata.get("total_tokens", 0)

    return {
        "output_text": output_text,
        "model_used": model or settings.selected_model_name,
        "latency_ms": latency_ms,
        "token_count": token_count,
    }


async def run_prompt(version_id: str, input_text: str, variables: dict, model: str = "", temperature: float = 0.7) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM prompt_versions WHERE id = ?", (version_id,))
        version = await cursor.fetchone()
        if not version:
            raise ValueError(f"Version {version_id} not found")

        result = await execute_prompt(
            system_prompt=version["system_prompt"],
            user_prompt_template=version["user_prompt_template"],
            input_text=input_text,
            variables=variables,
            model=model or version["model"],
            temperature=temperature if temperature != 0.7 else version["temperature"],
        )

        run_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO runs (id, version_id, input_text, variables, output_text, model_used, temperature, latency_ms, token_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, version_id, input_text, json.dumps(variables), result["output_text"],
             result["model_used"], temperature, result["latency_ms"], result["token_count"]),
        )
        await db.commit()

        return {
            "id": run_id,
            "version_id": version_id,
            "input_text": input_text,
            "variables": variables,
            "output_text": result["output_text"],
            "model_used": result["model_used"],
            "temperature": temperature,
            "latency_ms": result["latency_ms"],
            "token_count": result["token_count"],
            "rating": 0,
            "notes": "",
        }
    finally:
        await db.close()


async def compare_versions(prompt_id: str, version_ids: list[str], input_text: str, variables: dict, model: str = "", temperature: float = 0.7) -> list[dict]:
    db = await get_db()
    try:
        results = []
        for vid in version_ids:
            cursor = await db.execute("SELECT * FROM prompt_versions WHERE id = ?", (vid,))
            version = await cursor.fetchone()
            if not version:
                continue

            result = await execute_prompt(
                system_prompt=version["system_prompt"],
                user_prompt_template=version["user_prompt_template"],
                input_text=input_text,
                variables=variables,
                model=model or version["model"],
                temperature=temperature if temperature != 0.7 else version["temperature"],
            )

            run_id = str(uuid.uuid4())
            await db.execute(
                """INSERT INTO runs (id, version_id, input_text, variables, output_text, model_used, temperature, latency_ms, token_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, vid, input_text, json.dumps(variables), result["output_text"],
                 result["model_used"], temperature, result["latency_ms"], result["token_count"]),
            )

            results.append({
                "version_id": vid,
                "version_number": version["version_number"],
                "output_text": result["output_text"],
                "latency_ms": result["latency_ms"],
                "token_count": result["token_count"],
            })

        await db.commit()
        return results
    finally:
        await db.close()
