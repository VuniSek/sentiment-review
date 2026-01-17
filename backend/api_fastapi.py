from operator import pos
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import joblib
import io
import re
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

app = FastAPI(title="Sentiment Batch API")

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 5))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
MODEL_PATH = os.getenv("MODEL_PATH", "model/svm_domain_model.pkl")

model = joblib.load(MODEL_PATH)

label_map_rev = {
    0: "negatif",
    1: "netral",
    2: "positif"
}

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

def auto_domain(text: str) -> str:
    text = text.lower()

    if any(k in text for k in ["barang", "produk", "pengiriman", "paket"]):
        return "produk"
    if any(k in text for k in ["kampus", "dosen", "kuliah", "mahasiswa"]):
        return "kampus"
    if any(k in text for k in ["layanan", "pelayanan", "petugas"]):
        return "layanan"
    if any(k in text for k in ["aplikasi", "app", "fitur", "login"]):
        return "aplikasi"

    return "umum"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, 
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "model": "svm_domain_model",
        "mode": "batch csv"
    }


@app.post("/predict-csv")
async def predict_csv(file: UploadFile = File(...)):

    if not file.filename.lower().endswith((".csv", ".xlsx")):
        return JSONResponse(
            status_code=400,
            content={"error": "File harus CSV atau XLSX"}
        )

    file.file.seek(0)

    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(
                file.file,
                encoding="utf-8",
                encoding_errors="ignore",
                sep=None,
                engine="python"
            )
        else:
            df = pd.read_excel(file.file)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Gagal membaca file: {str(e)}"}
        )
    
    df.columns = (
    df.columns
    .str.lower()
    .str.strip()
    .str.replace("\ufeff", "")
    )
    if "text" not in df.columns:
        return JSONResponse(
            status_code=400,
            content={"error": "Kolom wajib: text"}
        )

    df["text"] = df["text"].fillna("").astype(str)

    results = []

    for raw_text in df["text"]:
        cleaned = clean_text(raw_text)

        sentiment = "netral"
        domain = "umum"

        if cleaned and len(cleaned.split()) > 1:
            try:
                domain = auto_domain(cleaned)

                pred = model.predict(pd.DataFrame([{
                    "text": cleaned,
                    "domain": domain
                }]))[0]

                sentiment = label_map_rev.get(pred, "netral")

            except Exception:
                sentiment = "netral"

        results.append({
            "text": raw_text,
            "domain": domain,
            "sentiment": sentiment
        })

    out_df = pd.DataFrame(results)

    summary = out_df["sentiment"].value_counts()

    pos = int(summary.get("positif", 0))
    neu = int(summary.get("netral", 0))
    neg = int(summary.get("negatif", 0))
    total = pos + neu + neg

    summary_df = pd.DataFrame({
        "text": ["RINGKASAN", "positif", "netral", "negatif", "total"],
        "domain": ["", "", "", "", ""],
        "sentiment": ["", pos, neu, neg, total]
    })

    final_df = pd.concat(
        [out_df, summary_df],
        ignore_index=True
    )

    output = io.StringIO()
    final_df.to_csv(output, index=False, encoding="utf-8")
    output.seek(0)


    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=hasil_prediksi.csv"
        }
    )
