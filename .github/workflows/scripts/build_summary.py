#!/usr/bin/env python3
"""Collect only reported build outputs and summarize every matrix entry."""
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile


def collect(result_file: Path, output_dir: Path):
    result = json.loads(result_file.read_text())
    if result.get("total") != 1 or result.get("success") != 1:
        raise ValueError("Expected one successful kernel build")
    artifacts = [Path(p) for p in result["results"][0]["artifacts"]]
    if not any(p.name.endswith("-AnyKernel3.zip") for p in artifacts):
        raise ValueError("Build did not produce an AnyKernel3 package")
    for source in artifacts:
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError(f"Missing or empty artifact: {source}")
        if source.suffix == ".zip":
            with zipfile.ZipFile(source) as archive:
                if "Image" not in archive.namelist() or archive.getinfo("Image").file_size == 0:
                    raise ValueError(f"AnyKernel3 package has no Image: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for source in artifacts:
        shutil.copy2(source, output_dir / source.name)
    config = result["results"][0]["config"]
    name = f"{config['android_version']}-{config['kernel_version']}-{config['sub_level']}"
    shutil.copy2(result_file, output_dir / f"build-info-{name}.json")


def summarize(results_dir: Path, output: Path, matrix: list, inputs: dict):
    counts = {"success": 0, "failure": 0, "cancelled": 0, "missing": 0}
    lines = ["# GKI full matrix build", "",
             f"SukiSU commit: `{inputs.get('kernelsu_commit') or 'builtin HEAD'}`",
             f"Manager version code: `{inputs.get('ksu_version_code') or 'automatic'}`", "",
             "KPM is disabled for 6.6; other versions follow the use_kpm input.",
             "Build success does not establish device boot compatibility.", "",
             "| Configuration | OS patch | SUSFS commit | Result |",
             "| --- | --- | --- | --- |"]
    for cfg in matrix:
        name = f"{cfg['android']}-{cfg['kernel']}-{cfg['sub_level']}"
        status_file = results_dir / f"{name}.status"
        status = "missing"
        if status_file.exists():
            record = status_file.read_text().strip()
            prefix = f"{name}:outcome="
            if record.startswith(prefix) and record[len(prefix):] in counts:
                status = record[len(prefix):]
        counts[status] += 1
        commit = inputs.get("susfs_commit") or cfg["susfs_commit"]
        lines.append(f"| {name} | {cfg['os_patch']} | `{commit}` | {status} |")
    failed = len(matrix) - counts["success"]
    lines.extend(["", f"Total: {len(matrix)}; success: {counts['success']}; "
                  f"failure: {counts['failure']}; cancelled: {counts['cancelled']}; "
                  f"missing: {counts['missing']}", "", "## Inputs", "",
                  "```json", json.dumps(inputs, indent=2, ensure_ascii=False), "```", ""])
    body = "\n".join(lines)
    output.write_text(body)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(body)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"success={counts['success']}\nfailed={failed}\n")
    print(body)
    return counts


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1] == "summarize":
        summarize(Path(sys.argv[2]), Path(sys.argv[3]),
                  json.loads(os.environ["BUILD_MATRIX"]),
                  json.loads(os.environ["BUILD_INPUTS"]))
    else:
        raise SystemExit("Expected collect or summarize")
