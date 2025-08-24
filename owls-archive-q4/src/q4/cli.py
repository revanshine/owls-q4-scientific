
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
from .operator import learn_projectors_linear, four_quadrants, energy_split

def run_file(path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(path) if path.suffix.lower()==".csv" else pd.read_parquet(path)
    X = df.to_numpy(dtype=float)
    Ps, Pv = learn_projectors_linear(X, labels=None, r=1)
    q = four_quadrants(X, Ps, Pv)
    np.savetxt(out_dir/"Q_keep.csv", q.Q_keep, delimiter=",")
    np.savetxt(out_dir/"Q_discard.csv", q.Q_discard, delimiter=",")
    (out_dir/"Q_study.json").write_text(json.dumps(q.Q_study, indent=2))
    (out_dir/"er.json").write_text(json.dumps({"energy_split": energy_split(X, Ps, Pv), "rows": int(X.shape[0])}, indent=2))
    (out_dir/"MANIFEST.json").write_text(json.dumps({"inputs":{"path":str(path)},"outputs":{"Q_keep":"Q_keep.csv","Q_discard":"Q_discard.csv","Q_study":"Q_study.json","er":"er.json"}}, indent=2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run_file(args.input, args.out)
