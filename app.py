"""
Auto EDA Insight — app.py
SD-1306 Data Science Programming
Institut Teknologi Sains Bandung
Lecturer: Bakti Siregar, M.Sc.
"""

from importlib.resources import path

from flask import Flask, request, jsonify, send_from_directory, send_file, session as flask_session
import os, json, html, traceback
from functools import wraps
import numpy as np
import pandas as pd

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        if isinstance(obj, float) and (obj != obj):  # NaN
            return None
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

from backend.data_loader        import DataLoader
from backend.descriptive_stats  import DescriptiveStats
from backend.categorical_analysis import CategoricalAnalysis
from backend.visualization      import Visualization
from backend.time_series        import TimeSeries
from backend.insight_generator  import InsightGenerator
from backend.export_report      import ExportReport
from backend.auth               import register_user, login_user, get_user, increment_upload, update_user, update_profile_info, update_password

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)
app.json_encoder = CustomJSONEncoder
app.secret_key = "eda_insight_secret_key_2026"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50 MB

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── In-memory data session (per-user) ────────────────────────────────────────
_user_sessions = {}   # { username: { "df": ..., "filepath": ..., ... } }

def _get_session() -> dict:
    """Return the data-session dict for the currently logged-in user."""
    username = flask_session.get("username", "__anonymous__")
    if username not in _user_sessions:
        _user_sessions[username] = {}
    return _user_sessions[username]

def get_df():
    ds = _get_session()

    if "df" in ds:
        return ds["df"]

    if "filepath" in ds and os.path.exists(ds["filepath"]):
        loader = DataLoader(ds["filepath"])
        df = loader.load()

        ds["df"] = df
        return df

    filepath = flask_session.get("last_filepath")

    if filepath and os.path.exists(filepath):
        loader = DataLoader(filepath)
        df = loader.load()

        ds["df"] = df
        ds["filepath"] = filepath

        return df

    # Tidak ada dataset di sesi maupun di sesi browser — beri pesan yang jelas
    # alih-alih diam-diam mengembalikan None (yang sebelumnya menyebabkan error
    # generik "'NoneType' object has no len()" di endpoint statistik/export).
    raise ValueError("Belum ada dataset. Silakan upload file terlebih dahulu.")
    
# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in flask_session:
            return jsonify(success=False, error="Anda harus login terlebih dahulu.", redirect="/login"), 401
        return f(*args, **kwargs)
    return decorated

# ── Static pages ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("frontend/templates", "index.html")

@app.route("/login")
def login_page():
    return send_from_directory("frontend/templates", "login.html")

@app.route("/register")
def register_page():
    return send_from_directory("frontend/templates", "register.html")

@app.route("/profile")
def profile_page():
    return send_from_directory("frontend/templates", "profile.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory("frontend/templates", "dashboard.html")

@app.route("/upload")
def upload_page():
    return send_from_directory("frontend/templates", "upload.html")

@app.route("/report")
def report_page():
    return send_from_directory("frontend/templates", "report.html")

# ── Auth API ──────────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    try:
        data      = request.get_json()
        username  = data.get("username", "")
        password  = data.get("password", "")
        full_name = data.get("full_name", "")
        email     = data.get("email", "")
        result    = register_user(username, password, full_name, email)
        return jsonify(result)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    try:
        data     = request.get_json()
        username = data.get("username", "")
        password = data.get("password", "")
        result   = login_user(username, password)
        if result["success"]:
            flask_session["username"] = result["user"]["username"]
        return jsonify(result)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    flask_session.pop("username", None)
    return jsonify(success=True)

@app.route("/api/auth/me")
def api_me():
    username = flask_session.get("username")
    if not username:
        return jsonify(success=False, logged_in=False)
    user = get_user(username)
    return jsonify(success=True, logged_in=True, user=user)

# ── Upload ────────────────────────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    try:
        if "file" not in request.files:
            return jsonify(success=False, error="Tidak ada file yang dikirim.")
        f = request.files["file"]
        if f.filename == "":
            return jsonify(success=False, error="Nama file kosong.")

        filepath = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(filepath)

        loader = DataLoader(filepath)
        df     = loader.load()
        info   = loader.get_info(df)

        ds = _get_session()
        ds.clear()
        ds["df"]          = df
        ds["filepath"]    = filepath
        ds["filename"]    = f.filename
        ds["upload_time"] = info.get("upload_time", "")

        flask_session["last_filepath"] = filepath
        flask_session["last_filename"] = f.filename

        for k in ("stats", "viz", "insights", "ts"):
            ds.pop(k, None)

        # Track upload count
        username = flask_session.get("username")
        if username:
            increment_upload(username)

        return jsonify(success=True, info=info)

    except Exception as e:
        import traceback
        print(traceback.format_exc())

    return jsonify(
        success=False,
        error=str(e)
    ), 500

# ── Data Preview ──────────────────────────────────────────────────────────────
@app.route("/api/preview")
@login_required
def preview():
    try:
        df    = get_df()
        rows  = int(request.args.get("rows", 10))
        page  = int(request.args.get("page", 1))
        start = (page - 1) * rows
        end   = start + rows

        info = {
            "filename"   : _get_session().get("filename", ""),
            "rows"       : int(len(df)),
            "columns"    : int(len(df.columns)),
            "size_kb"    : round(os.path.getsize(_get_session()["filepath"]) / 1024, 1),
            "upload_time": _get_session().get("upload_time", ""),
            "dtypes"     : {c: str(t) for c, t in df.dtypes.items()},
        }

        slice_df = df.iloc[start:end]

        # Convert datetime columns to string to avoid JSON serialization errors
        slice_df = slice_df.copy()
        for col in slice_df.select_dtypes(include=["datetime", "datetimetz"]).columns:
            slice_df[col] = slice_df[col].astype(str)
        slice_df = slice_df.replace({np.nan: None})
        
        data = {
            "columns"   : list(df.columns),
            "rows"      : slice_df.where(slice_df.notna(), None).values.tolist(),
            "total_rows": len(df),
            "page"      : page,
            "pages"     : (len(df) + rows - 1) // rows,
            "info"      : info,
        }
        return jsonify(success=True, **data)
    except Exception as e:
        return jsonify(success=False, error=str(e))

# ── Statistics ────────────────────────────────────────────────────────────────
@app.route("/api/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    try:
        if request.method == "POST":
            # Frontend mengirim cleaned data → hitung statistik dari data tersebut
            payload = request.get_json(force=True)
            columns = payload.get("columns", [])
            rows    = payload.get("rows", [])
            if not columns or not rows:
                return jsonify(success=False, error="Data cleaned kosong.")
            df = pd.DataFrame(rows, columns=columns)
            # Coba parse kolom numerik yang mungkin dikirim sebagai string
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            ds  = DescriptiveStats(df)
            ca  = CategoricalAnalysis(df)
            stats = {
                "numerical"  : ds.compute(),
                "categorical": ca.compute(),
                "source"     : "cleaned",
            }
            return jsonify(success=True, **stats)
        else:
            # GET → fallback ke raw data (sesi)
            df   = get_df()
            ds   = DescriptiveStats(df)
            ca   = CategoricalAnalysis(df)
            stats = _get_session().get("stats") or {
                "numerical"  : ds.compute(),
                "categorical": ca.compute(),
            }
            _get_session()["stats"] = stats
            stats_with_source = dict(stats, source="raw")
            return jsonify(success=True, **stats_with_source)
    except Exception as e:
        return jsonify(success=False, error=str(e))

# ── Visualizations ────────────────────────────────────────────────────────────
@app.route("/api/visualizations", methods=["GET", "POST"])
@login_required
def visualizations():
    try:
        if request.method == "POST":
            # Frontend mengirim cleaned data → visualisasi dibuat dari data tersebut,
            # sehingga chart "Sesudah Cleaning" benar-benar memakai data yang sudah bersih.
            payload = request.get_json(force=True)
            columns = payload.get("columns", [])
            rows    = payload.get("rows", [])
            if not columns or not rows:
                return jsonify(success=False, error="Data cleaned kosong.")
            df = pd.DataFrame(rows, columns=columns)
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            v   = Visualization(df)
            viz = v.generate_all()
            return jsonify(success=True, visualizations=viz, source="cleaned")
        else:
            # GET → visualisasi dari data asli/raw (sesi), dipakai sebelum cleaning diterapkan
            df  = get_df()
            viz = _get_session().get("viz")
            if not viz:
                v   = Visualization(df)
                viz = v.generate_all()
                _get_session()["viz"] = viz
            return jsonify(success=True, visualizations=viz, source="raw")
    except Exception as e:
        traceback.print_exc()
        return jsonify(success=False, error=str(e))

# ── Insights ──────────────────────────────────────────────────────────────────
@app.route("/api/insights", methods=["GET", "POST"])
@login_required
def insights():
    try:
        if request.method == "POST":
            # Frontend mengirim cleaned data → insight dihitung dari data tersebut
            payload = request.get_json(force=True)
            columns = payload.get("columns", [])
            rows    = payload.get("rows", [])
            if not columns or not rows:
                return jsonify(success=False, error="Data cleaned kosong.")
            df = pd.DataFrame(rows, columns=columns)
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

            raw_df  = get_df()
            ig      = InsightGenerator(df)
            ins     = ig.generate(source="cleaned", raw_row_count=len(raw_df))
            return jsonify(success=True, insights=ins, source="cleaned")
        else:
            # GET → insight dari data asli/raw (sesi)
            df  = get_df()
            ig  = InsightGenerator(df)
            ins = _get_session().get("insights") or ig.generate(source="raw")
            _get_session()["insights"] = ins
            return jsonify(success=True, insights=ins, source="raw")
    except Exception as e:
        return jsonify(success=False, error=str(e))

# ── Time Series ───────────────────────────────────────────────────────────────
@app.route("/api/timeseries")
@login_required
def timeseries():
    try:
        df = get_df()
        ts = _get_session().get("ts")
        if not ts:
            t  = TimeSeries(df)
            ts = t.analyze()
            _get_session()["ts"] = ts
        return jsonify(success=True, timeseries=ts)
    except Exception as e:
        return jsonify(success=False, error=str(e))

# ── Profile Update ────────────────────────────────────────────────────────────
@app.route("/api/auth/update-profile", methods=["POST"])
@login_required
def api_update_profile():
    """Update nama lengkap dan email — tidak perlu password."""
    try:
        data      = request.get_json()
        username  = flask_session.get("username")
        full_name = data.get("full_name", "")
        email     = data.get("email", "")
        result    = update_profile_info(username, full_name=full_name, email=email)
        return jsonify(result)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route("/api/auth/update-password", methods=["POST"])
@login_required
def api_update_password():
    """Update password — wajib verifikasi password lama."""
    try:
        data             = request.get_json()
        username         = flask_session.get("username")
        current_password = data.get("current_password", "")
        new_password     = data.get("new_password", "")
        result           = update_password(username, current_password=current_password, new_password=new_password)
        return jsonify(result)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route("/api/auth/update-avatar", methods=["POST"])
@login_required
def api_update_avatar():
    """Update foto profil."""
    try:
        import base64, uuid
        data        = request.get_json()
        username    = flask_session.get("username")
        avatar_data = data.get("avatar_data")

        if not avatar_data:
            return jsonify(success=False, error="Tidak ada data foto.")

        avatars_dir = os.path.join(os.path.dirname(__file__), "frontend", "static", "assets", "avatars")
        os.makedirs(avatars_dir, exist_ok=True)
        if "," in avatar_data:
            header, encoded = avatar_data.split(",", 1)
            ext = "png" if "png" in header else ("gif" if "gif" in header else ("webp" if "webp" in header else "jpg"))
        else:
            encoded, ext = avatar_data, "jpg"
        img_bytes = base64.b64decode(encoded)
        filename  = f"{username}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath  = os.path.join(avatars_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        avatar_url = f"/static/assets/avatars/{filename}"
        result = update_user(username, avatar_url=avatar_url)
        return jsonify(result)
    except Exception as e:
        return jsonify(success=False, error=str(e))

# ── Export ────────────────────────────────────────────────────────────────────
@app.route("/api/export/<fmt>")
@login_required
def export(fmt):
    try:
        df = get_df()
        ds = _get_session()

        # Pastikan SELURUH isi dashboard (statistik, insight, time series) sudah
        # tersedia di sesi sebelum laporan dibuat. Sebelumnya bagian ini hanya
        # terisi jika user sempat membuka tab tertentu di dashboard terlebih
        # dahulu (mis. tab Time Series) — jika tidak, laporan yang diunduh bisa
        # kehilangan bagian tersebut walau tanpa error. Dengan dihitung di sini,
        # laporan yang diunduh SELALU memuat seluruh isi dashboard.
        if not ds.get("stats"):
            ds["stats"] = {
                "numerical"  : DescriptiveStats(df).compute(),
                "categorical": CategoricalAnalysis(df).compute(),
            }
        if not ds.get("insights"):
            ds["insights"] = InsightGenerator(df).generate(source="raw")
        if "ts" not in ds:
            try:
                ds["ts"] = TimeSeries(df).analyze()
            except Exception:
                # Jangan biarkan kegagalan deteksi time series menggagalkan
                # seluruh proses ekspor — cukup lewati bagian ini.
                ds["ts"] = {"has_timeseries": False, "charts": []}

        exp = ExportReport(df, ds)
        out_dir = os.path.join(os.path.dirname(__file__), "outputs", "exported_files")
        os.makedirs(out_dir, exist_ok=True)

        if fmt == "csv":
            # ZIP berisi seluruh CSV dashboard (dataset, stats, insights, time series)
            path = exp.generate_csv(out_dir)
            return send_file(path, as_attachment=True,
                             download_name="eda_report_full.zip",
                             mimetype="application/zip")

        elif fmt == "excel":
            # Full multi-sheet XLSX
            path = exp.generate_excel(out_dir)
            return send_file(path, as_attachment=True,
                             download_name="eda_report_full.xlsx",
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        elif fmt == "pdf":
            path = exp.generate_pdf(out_dir)
            return send_file(path, as_attachment=True,
                             download_name="eda_report_full.pdf",
                             mimetype="application/pdf")

        elif fmt == "html":
            path = exp.generate_html(out_dir)
            return send_file(path, as_attachment=True, download_name="eda_report_full.html")

        else:
            return jsonify(success=False, error="Format tidak didukung. Gunakan csv, excel, pdf, atau html."), 400

    except Exception as e:
        traceback.print_exc()
        error_html = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<title>Gagal Membuat Laporan</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;background:#021225;color:#F2FFF6;
       display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
  .box{{max-width:520px;padding:32px;background:#061e35;border:1px solid #25C5E9;
       border-radius:16px;text-align:center}}
  h1{{color:#ef4444;font-size:18px;margin:0 0 12px}}
  p{{color:#CAFFDE;font-size:14px;line-height:1.6}}
  a{{color:#25C5E9;text-decoration:none;font-weight:600}}
</style></head>
<body><div class="box">
  <h1>Gagal Membuat Laporan</h1>
  <p>{html.escape(str(e))}</p>
  <p><a href="/dashboard">&larr; Kembali ke Dashboard</a></p>
</div></body></html>"""
        return error_html, 500

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Auto EDA Insight — SD-1306 Data Science Programming")
    print("  Institut Teknologi Sains Bandung")
    print("  Buka: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
