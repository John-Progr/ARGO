import io
import uuid
import contextlib
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import run_crew, run_move_script

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs: dict = {}


def run_job(job_id: str, amount_usd: float, fidelity: str):
    try:
        jobs[job_id]["status"] = "running"
        # Redirect stdout+stderr so CrewAI/rich emoji output never hits the
        # Windows cp1252 terminal stream and causes a UnicodeEncodeError.
        _buf = io.StringIO()
        with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
            result = run_crew(amount_usd=amount_usd, fidelity=fidelity)
        jobs[job_id]["result"] = result

        rec = result.get("final_recommendation", "").upper()
        if "BUY" in rec or "SELL" in rec:
            jobs[job_id]["status"] = "awaiting_approval"
        else:
            jobs[job_id]["status"] = "done"

    except Exception as e:
        import traceback
        jobs[job_id]["status"] = "error"
        jobs[job_id]["result"] = {"error": str(e), "traceback": traceback.format_exc()}


def run_move_script_agent(job_id: str):
    job = jobs[job_id]
    verdict = job["result"]

    script = run_move_script(
        amount_usd=job["amount_usd"],
        coin=job["coin"],
        recommendation=verdict.get("final_recommendation", ""),
        trade_parameters=verdict.get("trade_parameters", {}),
    )

    jobs[job_id]["move_script"] = script
    jobs[job_id]["status"] = "done"


class AnalyzeRequest(BaseModel):
    amount_usd: float
    fidelity: str


@app.post("/analyze")
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    amount_usd = req.amount_usd
    fidelity = req.fidelity.upper()

    if amount_usd <= 0:
        return {"error": "amount_usd must be greater than 0"}
    if fidelity not in ("LOW", "HIGH"):
        return {"error": "fidelity must be LOW or HIGH"}

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "result": None,
        "amount_usd": amount_usd,
        "fidelity": fidelity,
        "coin": "SUI",
    }

    background_tasks.add_task(run_job, job_id, amount_usd, fidelity)
    return {"job_id": job_id}


@app.post("/approve/{job_id}")
async def approve_move(job_id: str, background_tasks: BackgroundTasks):
    job = jobs.get(job_id)
    if not job or job["status"] != "awaiting_approval":
        return {"error": "Job not found or not awaiting approval"}

    jobs[job_id]["status"] = "generating_script"
    background_tasks.add_task(run_move_script_agent, job_id)
    return {"status": "generating_script"}


@app.post("/reject/{job_id}")
async def reject_move(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}

    jobs[job_id]["status"] = "rejected"
    return {"status": "rejected"}


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}
    return job
