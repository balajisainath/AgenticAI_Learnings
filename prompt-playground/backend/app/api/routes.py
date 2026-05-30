import json
import uuid
from fastapi import APIRouter, HTTPException

from app.core.database import get_db
from app.domain.schemas import (
    PromptCreate, PromptUpdate, PromptResponse,
    VersionCreate, VersionResponse,
    TestCaseCreate, TestCaseResponse,
    RunRequest, RunResponse, RateRunRequest,
    CompareRequest, CompareResponse, CompareResult,
    PromptStats, VersionStats,
)
from app.services.prompt_runner import run_prompt, compare_versions

router = APIRouter(prefix="/api/v1", tags=["playground"])


# --- Health ---
@router.get("/health")
async def health():
    return {"status": "ok", "service": "Prompt Testing Playground"}


# --- Prompts CRUD ---
@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts():
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT p.*, 
                   COUNT(pv.id) as version_count,
                   MAX(pv.version_number) as latest_version
            FROM prompts p
            LEFT JOIN prompt_versions pv ON p.id = pv.prompt_id
            GROUP BY p.id
            ORDER BY p.updated_at DESC
        """)
        rows = await cursor.fetchall()
        return [
            PromptResponse(
                id=r["id"], name=r["name"], description=r["description"],
                created_at=r["created_at"], updated_at=r["updated_at"],
                version_count=r["version_count"], latest_version=r["latest_version"],
            ) for r in rows
        ]
    finally:
        await db.close()


@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(payload: PromptCreate):
    db = await get_db()
    try:
        prompt_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO prompts (id, name, description) VALUES (?, ?, ?)",
            (prompt_id, payload.name, payload.description),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        r = await cursor.fetchone()
        return PromptResponse(
            id=r["id"], name=r["name"], description=r["description"],
            created_at=r["created_at"], updated_at=r["updated_at"],
            version_count=0, latest_version=None,
        )
    finally:
        await db.close()


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT p.*, 
                   COUNT(pv.id) as version_count,
                   MAX(pv.version_number) as latest_version
            FROM prompts p
            LEFT JOIN prompt_versions pv ON p.id = pv.prompt_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (prompt_id,))
        r = await cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return PromptResponse(
            id=r["id"], name=r["name"], description=r["description"],
            created_at=r["created_at"], updated_at=r["updated_at"],
            version_count=r["version_count"], latest_version=r["latest_version"],
        )
    finally:
        await db.close()


@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, payload: PromptUpdate):
    db = await get_db()
    try:
        updates = []
        params = []
        if payload.name is not None:
            updates.append("name = ?")
            params.append(payload.name)
        if payload.description is not None:
            updates.append("description = ?")
            params.append(payload.description)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        updates.append("updated_at = datetime('now')")
        params.append(prompt_id)
        await db.execute(f"UPDATE prompts SET {', '.join(updates)} WHERE id = ?", params)
        await db.commit()
        return await get_prompt(prompt_id)
    finally:
        await db.close()


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    db = await get_db()
    try:
        await db.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        await db.commit()
        return {"status": "deleted"}
    finally:
        await db.close()


# --- Versions ---
@router.get("/prompts/{prompt_id}/versions", response_model=list[VersionResponse])
async def list_versions(prompt_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM prompt_versions WHERE prompt_id = ? ORDER BY version_number DESC",
            (prompt_id,),
        )
        rows = await cursor.fetchall()
        return [
            VersionResponse(
                id=r["id"], prompt_id=r["prompt_id"], version_number=r["version_number"],
                system_prompt=r["system_prompt"], user_prompt_template=r["user_prompt_template"],
                model=r["model"], temperature=r["temperature"], notes=r["notes"],
                created_at=r["created_at"],
            ) for r in rows
        ]
    finally:
        await db.close()


@router.post("/prompts/{prompt_id}/versions", response_model=VersionResponse)
async def create_version(prompt_id: str, payload: VersionCreate):
    db = await get_db()
    try:
        # Get next version number
        cursor = await db.execute(
            "SELECT MAX(version_number) as max_ver FROM prompt_versions WHERE prompt_id = ?",
            (prompt_id,),
        )
        row = await cursor.fetchone()
        next_version = (row["max_ver"] or 0) + 1

        version_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO prompt_versions (id, prompt_id, version_number, system_prompt, user_prompt_template, model, temperature, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (version_id, prompt_id, next_version, payload.system_prompt,
             payload.user_prompt_template, payload.model, payload.temperature, payload.notes),
        )
        await db.execute("UPDATE prompts SET updated_at = datetime('now') WHERE id = ?", (prompt_id,))
        await db.commit()

        cursor = await db.execute("SELECT * FROM prompt_versions WHERE id = ?", (version_id,))
        r = await cursor.fetchone()
        return VersionResponse(
            id=r["id"], prompt_id=r["prompt_id"], version_number=r["version_number"],
            system_prompt=r["system_prompt"], user_prompt_template=r["user_prompt_template"],
            model=r["model"], temperature=r["temperature"], notes=r["notes"],
            created_at=r["created_at"],
        )
    finally:
        await db.close()


@router.get("/prompts/{prompt_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(prompt_id: str, version_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM prompt_versions WHERE id = ? AND prompt_id = ?",
            (version_id, prompt_id),
        )
        r = await cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Version not found")
        return VersionResponse(
            id=r["id"], prompt_id=r["prompt_id"], version_number=r["version_number"],
            system_prompt=r["system_prompt"], user_prompt_template=r["user_prompt_template"],
            model=r["model"], temperature=r["temperature"], notes=r["notes"],
            created_at=r["created_at"],
        )
    finally:
        await db.close()


# --- Test Cases ---
@router.get("/prompts/{prompt_id}/test-cases", response_model=list[TestCaseResponse])
async def list_test_cases(prompt_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM test_cases WHERE prompt_id = ? ORDER BY created_at DESC",
            (prompt_id,),
        )
        rows = await cursor.fetchall()
        return [
            TestCaseResponse(
                id=r["id"], prompt_id=r["prompt_id"], name=r["name"],
                variables=json.loads(r["variables"]), created_at=r["created_at"],
            ) for r in rows
        ]
    finally:
        await db.close()


@router.post("/prompts/{prompt_id}/test-cases", response_model=TestCaseResponse)
async def create_test_case(prompt_id: str, payload: TestCaseCreate):
    db = await get_db()
    try:
        tc_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO test_cases (id, prompt_id, name, variables) VALUES (?, ?, ?, ?)",
            (tc_id, prompt_id, payload.name, json.dumps(payload.variables)),
        )
        await db.commit()
        return TestCaseResponse(
            id=tc_id, prompt_id=prompt_id, name=payload.name,
            variables=payload.variables, created_at="",
        )
    finally:
        await db.close()


# --- Run Prompt ---
@router.post("/run", response_model=RunResponse)
async def run_prompt_endpoint(payload: RunRequest):
    try:
        result = await run_prompt(
            version_id=payload.version_id,
            input_text=payload.input_text,
            variables=payload.variables,
            model=payload.model,
            temperature=payload.temperature,
        )
        return RunResponse(**result, test_case_id=None, created_at="")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/runs/{run_id}/rate")
async def rate_run(run_id: str, payload: RateRunRequest):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE runs SET rating = ?, notes = ? WHERE id = ?",
            (payload.rating, payload.notes, run_id),
        )
        await db.commit()
        return {"status": "rated", "run_id": run_id, "rating": payload.rating}
    finally:
        await db.close()


@router.get("/runs/history/{version_id}", response_model=list[RunResponse])
async def get_run_history(version_id: str, limit: int = 20):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM runs WHERE version_id = ? ORDER BY created_at DESC LIMIT ?",
            (version_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            RunResponse(
                id=r["id"], version_id=r["version_id"], test_case_id=r["test_case_id"],
                input_text=r["input_text"], variables=json.loads(r["variables"]),
                output_text=r["output_text"], model_used=r["model_used"],
                temperature=r["temperature"], latency_ms=r["latency_ms"],
                token_count=r["token_count"], rating=r["rating"], notes=r["notes"],
                created_at=r["created_at"],
            ) for r in rows
        ]
    finally:
        await db.close()


# --- Compare ---
@router.post("/compare", response_model=CompareResponse)
async def compare_endpoint(payload: CompareRequest):
    try:
        results = await compare_versions(
            prompt_id=payload.prompt_id,
            version_ids=payload.version_ids,
            input_text=payload.input_text,
            variables=payload.variables,
            model=payload.model,
            temperature=payload.temperature,
        )

        comparison_id = str(uuid.uuid4())
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO comparisons (id, name, prompt_id, version_ids, test_input, variables, results)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (comparison_id, f"Compare {len(payload.version_ids)} versions",
                 payload.prompt_id, json.dumps(payload.version_ids),
                 payload.input_text, json.dumps(payload.variables), json.dumps(results)),
            )
            await db.commit()
        finally:
            await db.close()

        return CompareResponse(
            id=comparison_id,
            name=f"Compare {len(payload.version_ids)} versions",
            prompt_id=payload.prompt_id,
            version_ids=payload.version_ids,
            input_text=payload.input_text,
            variables=payload.variables,
            results=[CompareResult(**r) for r in results],
            created_at="",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Stats ---
@router.get("/prompts/{prompt_id}/stats", response_model=PromptStats)
async def get_stats(prompt_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT name FROM prompts WHERE id = ?", (prompt_id,))
        prompt = await cursor.fetchone()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        cursor = await db.execute(
            """SELECT pv.id, pv.version_number,
                      COUNT(r.id) as total_runs,
                      COALESCE(AVG(CASE WHEN r.rating > 0 THEN r.rating END), 0) as avg_rating,
                      COALESCE(AVG(r.latency_ms), 0) as avg_latency_ms,
                      COALESCE(AVG(r.token_count), 0) as avg_tokens
               FROM prompt_versions pv
               LEFT JOIN runs r ON pv.id = r.version_id
               WHERE pv.prompt_id = ?
               GROUP BY pv.id
               ORDER BY pv.version_number""",
            (prompt_id,),
        )
        rows = await cursor.fetchall()
        versions = [
            VersionStats(
                version_id=r["id"], version_number=r["version_number"],
                total_runs=r["total_runs"], avg_rating=round(r["avg_rating"], 2),
                avg_latency_ms=round(r["avg_latency_ms"], 1),
                avg_tokens=round(r["avg_tokens"], 1),
            ) for r in rows
        ]
        return PromptStats(prompt_id=prompt_id, prompt_name=prompt["name"], versions=versions)
    finally:
        await db.close()
