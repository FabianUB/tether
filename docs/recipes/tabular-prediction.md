# Tabular Prediction

Build a machine learning prediction interface for CSV/tabular data using scikit-learn.

## Overview

Users can:

1. Upload a CSV file
2. Select target column to predict
3. Train a model automatically
4. Make predictions on new data
5. View model performance metrics

**Use cases:**

- House price prediction
- Customer churn prediction
- Sales forecasting
- Credit scoring
- Any structured data prediction

## Dependencies

### Backend (Python)

Add to `backend/pyproject.toml`:

```toml
dependencies = [
    # ... existing deps
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "joblib>=1.3.0",
]
```

Install:

```bash
cd backend && uv sync
```

### Frontend

```bash
pnpm add recharts
```

## Backend Implementation

### 1. ML Service

Create `backend/app/services/ml.py`:

```python
import json
from pathlib import Path
from typing import Any, Literal, Optional

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class MLService:
    def __init__(self, models_dir: str = "./data/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.model: Optional[Pipeline] = None
        self.model_info: Optional[dict] = None
        self.feature_names: list[str] = []
        self.task_type: Optional[Literal["classification", "regression"]] = None

    def analyze_dataset(self, df: pd.DataFrame) -> dict:
        """Analyze a dataset and return column information."""
        columns = []

        for col in df.columns:
            dtype = str(df[col].dtype)
            nunique = df[col].nunique()
            null_count = df[col].isnull().sum()

            # Determine column type
            if dtype in ["int64", "float64"]:
                col_type = "numeric"
            elif dtype == "bool" or nunique == 2:
                col_type = "binary"
            elif nunique < 20:
                col_type = "categorical"
            else:
                col_type = "text"

            columns.append(
                {
                    "name": col,
                    "dtype": dtype,
                    "type": col_type,
                    "unique_values": nunique,
                    "null_count": int(null_count),
                    "sample_values": df[col].dropna().head(5).tolist(),
                }
            )

        return {
            "rows": len(df),
            "columns": columns,
            "suggested_targets": [
                c["name"]
                for c in columns
                if c["type"] in ["numeric", "binary", "categorical"]
            ],
        }

    def train(
        self,
        df: pd.DataFrame,
        target_column: str,
        test_size: float = 0.2,
    ) -> dict:
        """Train a model on the dataset."""
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]

        self.feature_names = X.columns.tolist()

        # Determine task type
        if y.dtype in ["int64", "float64"] and y.nunique() > 10:
            self.task_type = "regression"
        else:
            self.task_type = "classification"

        # Identify column types
        numeric_features = X.select_dtypes(include=["int64", "float64"]).columns
        categorical_features = X.select_dtypes(include=["object", "bool"]).columns

        # Build preprocessor
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric_features,
                ),
                (
                    "cat",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical_features,
                ),
            ]
        )

        # Select model based on task
        if self.task_type == "regression":
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        else:
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)

        # Build pipeline
        self.model = Pipeline(
            [
                ("preprocessor", preprocessor),
                ("model", model),
            ]
        )

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Train
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)

        if self.task_type == "regression":
            metrics = {
                "r2_score": round(r2_score(y_test, y_pred), 4),
                "mae": round(mean_absolute_error(y_test, y_pred), 4),
                "rmse": round(mean_squared_error(y_test, y_pred, squared=False), 4),
            }
        else:
            metrics = {
                "accuracy": round(accuracy_score(y_test, y_pred), 4),
                "f1_score": round(
                    f1_score(y_test, y_pred, average="weighted"), 4
                ),
            }

        # Get feature importance
        feature_importance = self._get_feature_importance()

        # Store model info
        self.model_info = {
            "task_type": self.task_type,
            "target_column": target_column,
            "feature_names": self.feature_names,
            "metrics": metrics,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        return {
            **self.model_info,
            "feature_importance": feature_importance,
        }

    def _get_feature_importance(self) -> list[dict]:
        """Extract feature importance from the model."""
        if self.model is None:
            return []

        # Get feature names after preprocessing
        preprocessor = self.model.named_steps["preprocessor"]
        model = self.model.named_steps["model"]

        # Get transformed feature names
        feature_names = []

        for name, transformer, columns in preprocessor.transformers_:
            if name == "num":
                feature_names.extend(columns)
            elif name == "cat":
                encoder = transformer.named_steps["encoder"]
                if hasattr(encoder, "get_feature_names_out"):
                    feature_names.extend(encoder.get_feature_names_out(columns))

        # Get importances
        importances = model.feature_importances_

        # Match names to importances
        result = []
        for i, importance in enumerate(importances):
            name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
            result.append({"feature": name, "importance": round(float(importance), 4)})

        # Sort by importance
        result.sort(key=lambda x: x["importance"], reverse=True)

        return result[:20]  # Top 20 features

    def predict(self, data: list[dict]) -> list[Any]:
        """Make predictions on new data."""
        if self.model is None:
            raise ValueError("No model trained. Train a model first.")

        df = pd.DataFrame(data)

        # Ensure columns match
        missing_cols = set(self.feature_names) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        # Reorder columns to match training
        df = df[self.feature_names]

        predictions = self.model.predict(df)

        return predictions.tolist()

    def save(self, name: str) -> str:
        """Save the trained model."""
        if self.model is None:
            raise ValueError("No model to save")

        model_path = self.models_dir / f"{name}.joblib"
        info_path = self.models_dir / f"{name}.json"

        joblib.dump(self.model, model_path)

        with open(info_path, "w") as f:
            json.dump(
                {
                    **self.model_info,
                    "feature_names": self.feature_names,
                    "task_type": self.task_type,
                },
                f,
            )

        return str(model_path)

    def load(self, name: str) -> dict:
        """Load a saved model."""
        model_path = self.models_dir / f"{name}.joblib"
        info_path = self.models_dir / f"{name}.json"

        if not model_path.exists():
            raise ValueError(f"Model '{name}' not found")

        self.model = joblib.load(model_path)

        with open(info_path) as f:
            info = json.load(f)
            self.model_info = info
            self.feature_names = info["feature_names"]
            self.task_type = info["task_type"]

        return self.model_info

    def list_models(self) -> list[str]:
        """List all saved models."""
        return [p.stem for p in self.models_dir.glob("*.joblib")]
```

### 2. ML Routes

Create `backend/app/routes/ml.py`:

```python
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.ml import MLService

router = APIRouter(prefix="/ml", tags=["ml"])

# Initialize ML service
ml_service = MLService()


class TrainRequest(BaseModel):
    target_column: str
    test_size: float = 0.2


class PredictRequest(BaseModel):
    data: list[dict[str, Any]]


# Store uploaded dataset temporarily
_current_dataset: pd.DataFrame | None = None


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    """Upload a CSV dataset for analysis."""
    global _current_dataset

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        _current_dataset = pd.read_csv(tmp_path)
        analysis = ml_service.analyze_dataset(_current_dataset)

        return {
            "status": "success",
            "filename": file.filename,
            **analysis,
        }
    finally:
        Path(tmp_path).unlink()


@router.post("/train")
async def train_model(request: TrainRequest) -> dict:
    """Train a model on the uploaded dataset."""
    global _current_dataset

    if _current_dataset is None:
        raise HTTPException(400, "No dataset uploaded. Upload a CSV first.")

    if request.target_column not in _current_dataset.columns:
        raise HTTPException(400, f"Column '{request.target_column}' not found")

    result = ml_service.train(
        _current_dataset,
        target_column=request.target_column,
        test_size=request.test_size,
    )

    return {"status": "success", **result}


@router.post("/predict")
async def predict(request: PredictRequest) -> dict:
    """Make predictions using the trained model."""
    try:
        predictions = ml_service.predict(request.data)
        return {"predictions": predictions}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/save/{name}")
async def save_model(name: str) -> dict:
    """Save the current model."""
    try:
        path = ml_service.save(name)
        return {"status": "success", "path": path}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/load/{name}")
async def load_model(name: str) -> dict:
    """Load a saved model."""
    try:
        info = ml_service.load(name)
        return {"status": "success", **info}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/models")
async def list_models() -> dict:
    """List all saved models."""
    return {"models": ml_service.list_models()}
```

### 3. Register Routes

In `backend/app/main.py`, add:

```python
from app.routes.ml import router as ml_router

app.include_router(ml_router)
```

## Frontend Implementation

### 1. Dataset Upload & Analysis

Create `frontend/components/DatasetUpload.tsx`:

```tsx
import { useState } from "react";

interface ColumnInfo {
  name: string;
  dtype: string;
  type: string;
  unique_values: number;
  null_count: number;
  sample_values: unknown[];
}

interface DatasetAnalysis {
  rows: number;
  columns: ColumnInfo[];
  suggested_targets: string[];
}

interface DatasetUploadProps {
  apiUrl: string;
  onAnalysis: (analysis: DatasetAnalysis) => void;
}

export function DatasetUpload({ apiUrl, onAnalysis }: DatasetUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${apiUrl}/ml/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Upload failed");
      }

      const result = await response.json();
      onAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".csv"
        onChange={handleUpload}
        disabled={uploading}
      />
      {uploading && <span> Uploading...</span>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
```

### 2. Model Training Component

Create `frontend/components/ModelTrainer.tsx`:

```tsx
import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface TrainingResult {
  task_type: string;
  metrics: Record<string, number>;
  feature_importance: { feature: string; importance: number }[];
  train_samples: number;
  test_samples: number;
}

interface ModelTrainerProps {
  apiUrl: string;
  suggestedTargets: string[];
  onTrained: (result: TrainingResult) => void;
}

export function ModelTrainer({
  apiUrl,
  suggestedTargets,
  onTrained,
}: ModelTrainerProps) {
  const [target, setTarget] = useState(suggestedTargets[0] || "");
  const [training, setTraining] = useState(false);
  const [result, setResult] = useState<TrainingResult | null>(null);

  const handleTrain = async () => {
    setTraining(true);

    try {
      const response = await fetch(`${apiUrl}/ml/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_column: target }),
      });

      const data = await response.json();
      setResult(data);
      onTrained(data);
    } catch (err) {
      console.error(err);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "1rem" }}>
        <label>
          Target column:{" "}
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {suggestedTargets.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={handleTrain}
          disabled={training || !target}
          style={{ marginLeft: "1rem" }}
        >
          {training ? "Training..." : "Train Model"}
        </button>
      </div>

      {result && (
        <div>
          <h3>Results ({result.task_type})</h3>

          <div style={{ marginBottom: "1rem" }}>
            <strong>Metrics:</strong>
            <ul>
              {Object.entries(result.metrics).map(([key, value]) => (
                <li key={key}>
                  {key}: {value}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <strong>Feature Importance (Top 10):</strong>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={result.feature_importance.slice(0, 10)}
                layout="vertical"
                margin={{ left: 100 }}
              >
                <XAxis type="number" />
                <YAxis type="category" dataKey="feature" width={100} />
                <Tooltip />
                <Bar dataKey="importance" fill="var(--color-primary)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 3. Prediction Form

Create `frontend/components/PredictionForm.tsx`:

```tsx
import { useState } from "react";

interface PredictionFormProps {
  apiUrl: string;
  featureNames: string[];
}

export function PredictionForm({ apiUrl, featureNames }: PredictionFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [prediction, setPrediction] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Convert string values to appropriate types
    const data: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(values)) {
      const num = parseFloat(value);
      data[key] = isNaN(num) ? value : num;
    }

    try {
      const response = await fetch(`${apiUrl}/ml/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: [data] }),
      });

      const result = await response.json();
      setPrediction(result.predictions[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
          gap: "1rem",
        }}
      >
        {featureNames.map((feature) => (
          <label key={feature} style={{ display: "block" }}>
            {feature}:
            <input
              type="text"
              value={values[feature] || ""}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, [feature]: e.target.value }))
              }
              style={{
                width: "100%",
                padding: "0.5rem",
                marginTop: "0.25rem",
              }}
            />
          </label>
        ))}
      </div>

      <button type="submit" disabled={loading} style={{ marginTop: "1rem" }}>
        {loading ? "Predicting..." : "Predict"}
      </button>

      {prediction !== null && (
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            backgroundColor: "var(--color-surface)",
            borderRadius: "8px",
          }}
        >
          <strong>Prediction:</strong> {String(prediction)}
        </div>
      )}
    </form>
  );
}
```

### 4. Usage in App

```tsx
import { useState } from "react";
import { DatasetUpload } from "./components/DatasetUpload";
import { ModelTrainer } from "./components/ModelTrainer";
import { PredictionForm } from "./components/PredictionForm";

function App() {
  const apiUrl = "http://localhost:8000";

  const [analysis, setAnalysis] = useState<{
    rows: number;
    columns: { name: string }[];
    suggested_targets: string[];
  } | null>(null);

  const [modelReady, setModelReady] = useState(false);
  const [featureNames, setFeatureNames] = useState<string[]>([]);

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "2rem" }}>
      <h1>ML Prediction</h1>

      <section style={{ marginBottom: "2rem" }}>
        <h2>1. Upload Dataset</h2>
        <DatasetUpload apiUrl={apiUrl} onAnalysis={setAnalysis} />

        {analysis && (
          <p style={{ marginTop: "1rem" }}>
            Loaded {analysis.rows} rows, {analysis.columns.length} columns
          </p>
        )}
      </section>

      {analysis && (
        <section style={{ marginBottom: "2rem" }}>
          <h2>2. Train Model</h2>
          <ModelTrainer
            apiUrl={apiUrl}
            suggestedTargets={analysis.suggested_targets}
            onTrained={(result) => {
              setModelReady(true);
              setFeatureNames(result.feature_importance.map((f) => f.feature));
            }}
          />
        </section>
      )}

      {modelReady && featureNames.length > 0 && (
        <section>
          <h2>3. Make Predictions</h2>
          <PredictionForm apiUrl={apiUrl} featureNames={featureNames} />
        </section>
      )}
    </div>
  );
}
```

## Example: House Price Prediction

### Sample Dataset

Create a `houses.csv`:

```csv
bedrooms,bathrooms,sqft,age,garage,price
3,2,1500,10,1,250000
4,3,2200,5,2,380000
2,1,900,30,0,150000
5,4,3500,2,3,550000
3,2,1800,15,2,290000
```

### Workflow

1. Upload `houses.csv`
2. Select `price` as target (regression detected automatically)
3. Train model
4. Enter new house features to predict price

## Configuration Tips

### Different Algorithms

Swap out the model in `ml.py`:

```python
# Random Forest (faster, good baseline)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# XGBoost (requires: pip install xgboost)
from xgboost import XGBRegressor, XGBClassifier

# LightGBM (requires: pip install lightgbm)
from lightgbm import LGBMRegressor, LGBMClassifier
```

### Hyperparameter Tuning

Add cross-validation:

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "model__n_estimators": [50, 100, 200],
    "model__max_depth": [3, 5, 10],
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5)
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_
```

### Handling Large Datasets

For datasets > 100k rows, consider:

```python
# Sample for training
df_sample = df.sample(n=50000, random_state=42)

# Or use incremental learning
from sklearn.linear_model import SGDRegressor, SGDClassifier
```

## Next Steps

- Add data visualization (histograms, scatter plots)
- Support for multiple file formats (Excel, Parquet)
- Model comparison (train multiple algorithms)
- Export predictions to CSV
- Add SHAP explanations for model interpretability
