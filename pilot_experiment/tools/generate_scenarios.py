#!/usr/bin/env python3
"""
合成场景生成工具：基于 domain + topic_seed + difficulty 生成 S031-S100。

用法:
    python tools/generate_scenarios.py --start 31 --end 100 --budget 25
    python tools/generate_scenarios.py --domains astronomy,protein_structure --dry-run
"""
import sys
import os
import json
import argparse
import yaml
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from config import API_KEY, BASE_URL, MODELS, log_cost, total_cost, SCENARIOS_DIR

import anthropic

# 领域 × topic seed 矩阵（70 个合成场景）
DOMAIN_TOPICS = {
    "astronomy": [
        ("galaxy_morphology", "medium", "Classify galaxy morphology from photometric catalog data"),
        ("stellar_spectra", "hard", "Normalize and classify stellar spectra by spectral type"),
        ("exoplanet_transit", "medium", "Detect and fit exoplanet transit signals in photometry"),
        ("quasar_variability", "medium", "Analyze quasar optical variability from survey data"),
        ("pulsar_timing", "hard", "Process pulsar timing residuals and compute dispersion measure"),
        ("cmb_power_spectrum", "medium", "Compute angular power spectrum from CMB temperature maps"),
        ("asteroid_orbit", "easy", "Compute orbital elements from asteroid position observations"),
        ("solar_flare", "easy", "Detect and classify solar flare events from X-ray light curves"),
    ],
    "protein_structure": [
        ("pdb_parser", "easy", "Parse PDB structure files and compute residue-level statistics"),
        ("contact_map", "medium", "Compute residue contact maps from atomic coordinates"),
        ("secondary_structure", "medium", "Assign secondary structure from backbone dihedral angles"),
        ("binding_site", "hard", "Identify ligand binding sites from protein surface analysis"),
        ("rmsd_alignment", "medium", "Align protein structures and compute RMSD"),
        ("bfactor_analysis", "easy", "Analyze B-factor distribution and identify flexible regions"),
        ("ramachandran", "medium", "Generate Ramachandran plot data and detect outliers"),
        ("disulfide_bonds", "hard", "Detect and validate disulfide bonds from cysteine distances"),
    ],
    "genomics": [
        ("vcf_filter", "medium", "Filter and annotate VCF variant calls by quality metrics"),
        ("gene_ontology", "easy", "Map gene lists to GO terms and compute enrichment"),
        ("rna_seq_counts", "medium", "Normalize RNA-seq count matrices using TPM and DESeq2-style"),
        ("snp_ld", "hard", "Compute linkage disequilibrium between SNP pairs"),
        ("primer_design", "easy", "Design PCR primers with Tm and GC content constraints"),
        ("phylogenetic_distance", "medium", "Compute pairwise phylogenetic distances from alignment"),
        ("methylation_beta", "hard", "Process DNA methylation beta-value arrays and find DMRs"),
    ],
    "ecology": [
        ("species_accumulation", "easy", "Compute species accumulation curves from sampling data"),
        ("population_dynamics", "medium", "Fit Lotka-Volterra population dynamics to time series"),
        ("habitat_suitability", "medium", "Build habitat suitability index from environmental layers"),
        ("beta_diversity", "medium", "Compute beta diversity metrics between sampling sites"),
        ("mark_recapture", "easy", "Estimate population size from mark-recapture data"),
        ("trophic_network", "medium", "Analyze food web structure and compute trophic levels"),
        ("phenology_shifts", "hard", "Detect phenological shifts from long-term observation data"),
    ],
    "oceanography": [
        ("argo_profiles", "medium", "Process Argo float profiles and compute mixed layer depth"),
        ("wave_spectrum", "medium", "Compute ocean wave frequency spectrum from buoy data"),
        ("tidal_analysis", "easy", "Perform harmonic analysis on tidal height records"),
        ("sea_surface_temp", "easy", "Compute SST anomalies from satellite-derived temperature grids"),
        ("chlorophyll_bloom", "medium", "Detect phytoplankton bloom events from chlorophyll time series"),
        ("acoustic_doppler", "hard", "Process ADCP velocity profiles and remove bad data"),
        ("salinity_gradient", "hard", "Analyze estuarine salinity gradient from CTD transects"),
    ],
    "atmospheric": [
        ("weather_fronts", "medium", "Detect weather fronts from temperature gradient analysis"),
        ("rainfall_extreme", "easy", "Compute rainfall return periods from daily precipitation"),
        ("wind_rose", "easy", "Generate wind rose statistics from meteorological observations"),
        ("visibility_analysis", "medium", "Analyze visibility data and compute fog frequency"),
        ("ozone_profile", "medium", "Process vertical ozone profiles from ozonesonde data"),
        ("lightning_density", "medium", "Compute lightning flash density maps from stroke data"),
        ("heat_index", "hard", "Calculate heat index time series and identify heat waves"),
    ],
    "materials": [
        ("tensile_curves", "easy", "Process tensile test stress-strain curves and extract properties"),
        ("thermal_analysis", "medium", "Analyze DSC thermal curves: baseline correction and peak detection"),
        ("grain_size", "easy", "Compute grain size distribution from image analysis measurements"),
        ("fatigue_life", "medium", "Fit S-N fatigue curves and predict cycles to failure"),
        ("crystal_symmetry", "medium", "Determine crystal system from unit cell parameters"),
        ("impedance_spectroscopy", "hard", "Fit equivalent circuit to electrochemical impedance data"),
        ("hardness_mapping", "hard", "Interpolate hardness indentation data into 2D maps"),
    ],
    "medical": [
        ("ecg_qrs_detect", "medium", "Detect QRS complexes in ECG signals and compute HR variability"),
        ("survival_analysis", "medium", "Perform Kaplan-Meier survival analysis from patient data"),
        ("dose_response", "easy", "Fit dose-response curves and compute IC50/EC50 values"),
        ("spirometry_flow", "easy", "Process spirometry flow-volume loops and compute FEV1/FVC"),
        ("blood_cell_count", "medium", "Normalize and flag complete blood count results"),
        ("drug_interaction", "medium", "Check drug interaction pairs from prescription data"),
        ("dicom_metadata", "hard", "Extract and validate DICOM metadata from medical images"),
    ],
    "signal_processing": [
        ("vibration_analysis", "medium", "Analyze machine vibration spectra for fault detection"),
        ("noise_reduction", "medium", "Apply adaptive noise cancellation to recorded signals"),
        ("modulation_classify", "hard", "Classify digital modulation schemes from IQ samples"),
        ("chirp_detection", "easy", "Detect chirp signals in noisy time-frequency spectrograms"),
        ("echo_removal", "medium", "Remove echo artifacts from audio recordings"),
        ("spectral_leakage", "hard", "Analyze and correct spectral leakage with windowing functions"),
    ],
    "social_science": [
        ("sentiment_score", "easy", "Compute sentiment scores for survey open-ended responses"),
        ("network_influence", "medium", "Identify influencers in a social network from interaction data"),
        ("topic_frequency", "easy", "Compute topic frequency trends from timestamped document corpus"),
        ("gini_coefficient", "medium", "Calculate Gini coefficient and Lorenz curve from income data"),
        ("mobility_patterns", "medium", "Analyze urban mobility patterns from anonymized trip data"),
        ("election_forecast", "hard", "Aggregate poll data and compute weighted election forecasts"),
    ],
}

# 生成场景的 system prompt
SCENARIO_GEN_PROMPT = """You are an expert at creating scientific data processing coding tasks for benchmarking AI code generation.

Given a domain, topic, and difficulty level, generate a complete scenario consisting of:

1. **task.md**: A realistic CLI script task description (200-400 words). Requirements:
   - Use argparse with clear input/output arguments
   - Process synthetic data (no external files needed)
   - Produce specific, verifiable outputs (files, JSON, etc.)
   - Include 4-6 numbered requirements
   - Difficulty: {difficulty} (easy=straightforward, medium=some domain knowledge, hard=complex algorithm)

2. **test_script.py**: A complete Python test script that:
   - Generates synthetic test data internally (create_data function)
   - Runs `generated.py` with appropriate arguments
   - Tests 10-15 PASS/FAIL conditions covering all requirements
   - Includes 2 SCORE: metrics (continuous 0-1)
   - Uses ONLY: numpy, pandas, scipy, h5py, PIL, matplotlib, standard library
   - Is self-contained and runs in a temporary directory
   - Tolerates common argument naming variations

Output format — respond with exactly two blocks:
```task
<task.md content>
```
```python
<test_script.py content>
```

Domain: {domain}
Topic: {topic}
Difficulty: {difficulty}
Topic description: {description}
"""


def generate_scenario(domain: str, topic: str, difficulty: str, description: str,
                      scenario_num: int, budget: float, model: str = "sonnet") -> dict | None:
    """调用 LLM 生成单个场景"""
    if total_cost() >= budget:
        print(f"  预算已用完: ${total_cost():.2f} >= ${budget:.2f}")
        return None

    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    prompt = SCENARIO_GEN_PROMPT.format(
        domain=domain, topic=topic, difficulty=difficulty, description=description
    )

    try:
        resp = client.messages.create(
            model=MODELS[model],
            max_tokens=8192,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text
        cost = log_cost(model, resp.usage.input_tokens, resp.usage.output_tokens,
                        f"S{scenario_num:03d}_{topic}", "scenario_gen")

        # 解析输出
        task_match = re.search(r"```task\s*\n(.*?)```", text, re.DOTALL)
        code_match = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)

        if not task_match or not code_match:
            print(f"  ✗ 解析失败: 无法提取 task 或 test")
            return None

        return {
            "task": task_match.group(1).strip(),
            "test": code_match.group(1).strip(),
            "cost": cost,
        }
    except Exception as e:
        print(f"  ✗ API 错误: {e}")
        return None


def save_scenario(scenario_num: int, topic: str, domain: str, difficulty: str,
                  task_text: str, test_text: str):
    """保存场景到目录"""
    scenario_id = f"S{scenario_num:03d}_{topic}"
    scenario_dir = SCENARIOS_DIR / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": scenario_id,
        "name": topic,
        "domain": domain,
        "difficulty": difficulty,
        "source": "synthetic",
        "tags": [domain, difficulty, "generated"],
        "required_packages": [],
    }

    (scenario_dir / "scenario.yaml").write_text(
        yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False))
    (scenario_dir / "task.md").write_text(task_text + "\n")
    (scenario_dir / "test_script.py").write_text(test_text + "\n")

    return scenario_id


def main():
    parser = argparse.ArgumentParser(description="批量生成合成场景")
    parser.add_argument("--start", type=int, default=31, help="起始编号")
    parser.add_argument("--end", type=int, default=100, help="结束编号")
    parser.add_argument("--budget", type=float, default=25.0, help="预算（美元）")
    parser.add_argument("--model", default="sonnet", help="用于生成的模型")
    parser.add_argument("--domains", default="all", help="逗号分隔的领域或 'all'")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划，不执行")
    args = parser.parse_args()

    # 构建生成计划
    if args.domains == "all":
        domains = list(DOMAIN_TOPICS.keys())
    else:
        domains = [d.strip() for d in args.domains.split(",")]

    plan = []
    num = args.start
    for domain in domains:
        topics = DOMAIN_TOPICS.get(domain, [])
        for topic, difficulty, description in topics:
            if num > args.end:
                break
            plan.append((num, domain, topic, difficulty, description))
            num += 1

    print(f"生成计划: {len(plan)} 个场景 (S{args.start:03d} - S{min(num-1, args.end):03d})")
    print(f"模型: {args.model}, 预算: ${args.budget}")

    if args.dry_run:
        for num, domain, topic, difficulty, desc in plan:
            print(f"  S{num:03d}_{topic} ({domain}, {difficulty}): {desc[:60]}...")
        return

    generated = 0
    for num, domain, topic, difficulty, desc in plan:
        print(f"\n[{num}/{args.end}] S{num:03d}_{topic} ({domain}, {difficulty})")
        result = generate_scenario(domain, topic, difficulty, desc, num, args.budget, args.model)
        if result:
            sid = save_scenario(num, topic, domain, difficulty, result["task"], result["test"])
            print(f"  ✓ {sid} (${result['cost']:.4f})")
            generated += 1
        else:
            print(f"  ✗ 跳过")

    print(f"\n{'='*50}")
    print(f"生成完成: {generated}/{len(plan)} 场景")
    print(f"总花费: ${total_cost():.4f}")


if __name__ == "__main__":
    main()
