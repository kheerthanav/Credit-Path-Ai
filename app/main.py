from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, logging, json, re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "predictions.db"
LOG_PATH = BASE_DIR / "predictions.log"

# ----- Logging -----
logger = logging.getLogger("credit_path_ai")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(message)s"))
if not logger.handlers:
    logger.addHandler(fh)

# ----- SQLite -----
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    name TEXT,
    email TEXT,
    input_json TEXT,
    output_json TEXT
)
""")
conn.commit()

# ----- Validation & prediction -----
email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")

def validate_borrower(b: Dict[str, Any]) -> List[str]:
    errors = []
    if not b.get('name'):
        errors.append("missing name")
    email = b.get('email')
    if not email:
        errors.append("missing email")
    elif not email_regex.match(email):
        errors.append("invalid email")
    for fld in ('income','loan_amount','employment_years'):
        v = b.get(fld)
        if v is None:
            errors.append(f"missing {fld}")
        else:
            try:
                if float(v) < 0:
                    errors.append(f"{fld} must be non-negative")
            except:
                errors.append(f"{fld} invalid")
    cs = b.get('credit_score')
    try:
        if cs is None:
            errors.append("missing credit_score")
        else:
            ics = int(cs)
            if ics < 300 or ics > 850:
                errors.append("credit_score out of range 300–850")
    except:
        errors.append("credit_score invalid")
    return errors

def predict_single(b: Dict[str, Any]) -> Dict[str, Any]:
    name = b.get('name') or "Unknown"
    email = (b.get('email') or "").lower()
    income = float(b.get('income') or 0)
    loan = float(b.get('loan_amount') or 0)
    credit = int(b.get('credit_score') or 0)
    emp = float(b.get('employment_years') or 0)
    purpose = b.get('purpose') or ""

    score, reasons = 0.0, []
    if email:
        domain = email.split('@')[-1]
        if any(domain.endswith(x) for x in ['.xyz', '.top', '.club', '.online']):
            score += 2.5; reasons.append(f"suspicious email domain {domain}")
        if re.search(r'free|loan|cash|offer', email):
            score += 1.5; reasons.append("marketing-like email address")
    if income > 0:
        ratio = loan / income
        if ratio > 2.0: score += 3; reasons.append("loan >> income")
        elif ratio > 1.0: score += 1.2; reasons.append("loan > income")
    else:
        score += 1.5; reasons.append("zero/unknown income")
    if credit < 500: score += 1.5; reasons.append("very low credit score")
    elif credit > 800: score -= 0.5
    if emp < 0.5: score += 1; reasons.append("short employment")
    elif emp >= 10: score -= 0.5
    if re.search(r'urgent|advance|investment|quick cash', purpose, re.I):
        score += 2; reasons.append("suspicious purpose phrasing")

    if score >= 4:
        risk, label, rec = "high", "likely_scam", "Do NOT proceed. Verify identity & docs."
    elif score >= 2:
        risk, label, rec = "medium", "possible_scam", "Exercise caution; verify ID & bank details."
    else:
        risk, label, rec = "low", "likely_legit", "Proceed with standard checks."

    return {
        "name": name, "email": email,
        "scam_score": round(score, 2),
        "scam_risk": risk, "scam_label": label,
        "recommendation": rec, "reasons": reasons
    }

def log_prediction(ts, inp, out):
    logger.info(json.dumps({"timestamp": ts, "input": inp, "output": out}))
    cur.execute("INSERT INTO predictions (timestamp,name,email,input_json,output_json) VALUES (?,?,?,?,?)",
                (ts, inp.get('name'), inp.get('email'), json.dumps(inp), json.dumps(out)))
    conn.commit()

def predict_batch(borrowers: List[Dict[str, Any]]):
    results = []
    for b in borrowers:
        errs = validate_borrower(b)
        if errs:
            out = {"error": True, "errors": errs, "name": b.get('name'), "email": b.get('email')}
        else:
            out = predict_single(b); out["error"] = False
        ts = datetime.utcnow().isoformat()
        log_prediction(ts, b, out)
        results.append(out)
    return {"timestamp": datetime.utcnow().isoformat(), "results": results}

# ----- FastAPI App -----
app = FastAPI(title="Credit Path AI - Scam Detector")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/")
def index(): return FileResponse(BASE_DIR / "static" / "credit_path_frontend.html")

@app.post("/predict")
async def predict_endpoint(payload: Dict[str, Any]):
    borrowers = payload.get("borrowers")
    if borrowers is None or not isinstance(borrowers, list):
        raise HTTPException(status_code=400, detail="'borrowers' must be a list")
    try:
        return JSONResponse(predict_batch(borrowers))
    except Exception as e:
        logger.exception("error: %s", str(e))
        raise HTTPException(status_code=500, detail="internal server error")

@app.get("/health")
def health(): return {"status": "ok", "time": datetime.utcnow().isoformat()}
