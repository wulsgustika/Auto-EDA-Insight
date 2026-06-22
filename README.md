# Auto EDA Insight
### SD-1306 — Data Science Programming
**Institut Teknologi Sains Bandung | Lecturer: Bakti Siregar, M.Sc.**

---

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. (Opsional) Generate sample dataset
```bash
python generate_sample.py
```

### 3. Jalankan aplikasi
```bash
python app.py
```

### 4. Buka browser
```
http://127.0.0.1:5000
```

---

## Struktur Project

```
Auto_EDA_Insight/
├── app.py                    ← Flask application (main entry point)
├── requirements.txt
├── generate_sample.py        ← Sample data generator
├── README.md
│
├── backend/
│   ├── data_loader.py        ← File upload & auto type detection
│   ├── descriptive_stats.py  ← Advanced numerical statistics
│   ├── categorical_analysis.py ← Categorical statistics
│   ├── visualization.py      ← All chart types (Plotly)
│   ├── time_series.py        ← Time series auto-detection & analysis
│   ├── insight_generator.py  ← Intelligent insight generation
│   └── export_report.py      ← PDF, HTML, Excel/CSV export
│
├── frontend/
│   └── templates/
│       ├── index.html        ← Landing page (team intro)
│       └── dashboard.html    ← Main analytics dashboard
│
├── data/
│   ├── raw/                  ← Uploaded files stored here
│   ├── processed/
│   └── sample_dataset/       ← sales_data.xlsx (generated)
│
└── outputs/
    ├── charts/
    ├── reports/
    └── exported_files/       ← PDF, HTML, Excel exports
```

---

## Fitur

| Fitur | Status |
|-------|--------|
| Upload Excel/CSV/TXT | ✅ |
| Auto data type detection | ✅ |
| Data preview & info | ✅ |
| Numerical descriptive statistics (13 metrics) | ✅ |
| Categorical statistics (6 metrics) | ✅ |
| Numerical visualizations (Histogram, Boxplot, Density, QQ, Violin) | ✅ |
| Categorical visualizations (Bar, Pie, Count, Pareto) | ✅ |
| Bivariate/Multivariate (Scatter, Correlation Heatmap, Regression, Bubble) | ✅ |
| Categorical vs Numerical (Boxplot by Cat, Violin by Cat, Grouped Bar, Strip) | ✅ |
| Time Series auto-detection & analytics | ✅ |
| Intelligent Insight Generator (8 types) | ✅ |
| Export PDF Report | ✅ |
| Export HTML Dashboard | ✅ |
| Export CSV / Excel | ✅ |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload dataset file |
| GET | `/api/preview` | Get data preview & info |
| GET | `/api/statistics` | Descriptive statistics |
| GET | `/api/visualizations` | All charts (Plotly JSON) |
| GET | `/api/insights` | Auto-generated insights |
| GET | `/api/timeseries` | Time series analysis |
| GET | `/api/export/csv` | Download CSV |
| GET | `/api/export/excel` | Download Excel |
| GET | `/api/export/pdf` | Download PDF report |
| GET | `/api/export/html` | Download HTML dashboard |
