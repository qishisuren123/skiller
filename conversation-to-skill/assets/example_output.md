# Example Output

This document shows examples of both conversation generation and skill package generation.

## Example 1: Generated Test Conversation

Running:
```bash
python scripts/generate_test_conversations.py \
    --scenario "Build a neural spike visualization pipeline from HDF5 electrophysiology data" \
    --domain neuroscience \
    --complexity advanced \
    --output conversations/neuro-spike.json
```

Produces a JSON file with 14-20 turns, including:

```json
[
  {
    "role": "user",
    "content": "I have HDF5 files from a neural recording experiment with about 150 neurons tracked across 200 trials. Each trial has spike times aligned to different behavioral events. I need to create a publication-quality figure with raster plots and PSTHs, but I'm not sure where to start with the visualization layout."
  },
  {
    "role": "assistant",
    "content": "I can help you build a multi-panel visualization. Let me first understand your data structure. Can you share the HDF5 hierarchy? You can check it with:\n\n```python\nimport h5py\n\nwith h5py.File('your_data.h5', 'r') as f:\n    f.visititems(lambda name, obj: print(name, type(obj)))\n```\n\nAlso, what alignment events do you have (e.g., stimulus onset, movement onset, go cue)?"
  },
  {
    "role": "user",
    "content": "Here's what I see:\n\n```\ntrials/go_cue float64 (200,)\ntrials/movement_onset float64 (200,)\nspikes/trial_000/neuron_000 float64 (var,)\n...\nbehavior/hand_velocity float64 (200, 500, 2)\n```\n\nI want to align to movement onset."
  },
  {
    "role": "assistant",
    "content": "Here's an initial implementation with 4 panels...\n\n```python\nimport numpy as np\nimport matplotlib.pyplot as plt\n...\n```"
  }
]
```

### Validation Report

```
Turns: 16
English ratio: 99.8%
Has traceback: Yes (2 found)
Has code blocks: Yes (12 found)
Quality: PASS
```

## Example 2: Generated Skill Package

Running:
```bash
python scripts/generate_skill.py conversations/neuro-spike.json \
    --output skills/neuro-spike-visualization \
    --name neuro-spike-visualization
```

Produces:
```
neuro-spike-visualization/
├── SKILL.md                    (3.2 KB, body under 5000 chars)
├── scripts/
│   ├── main.py                 (18 KB, complete with argparse CLI)
│   └── requirements.txt        (5 dependencies with version pins)
├── references/
│   ├── workflow.md             (8 KB, 6-step detailed workflow)
│   └── pitfalls.md             (6 KB, 8 documented pitfalls)
└── assets/
    └── example_output.md       (4 KB, figure description + data shapes)
```

### SKILL.md Preview (frontmatter)

```yaml
---
name: neuro-spike-visualization
description: >
  Generate publication-quality multi-panel neural spike visualizations from
  HDF5 electrophysiology data. Produces raster plots, population PSTH
  heatmaps, single-neuron PSTH curves, and behavioral kinematics overlays.
  Use this skill whenever you need to create publication-ready neural activity
  figures from spike-sorted recordings.
license: MIT
compatibility: >
  Python >=3.8; numpy >=1.20; matplotlib >=3.5; h5py >=3.0.
  Optional: scipy >=1.7 for advanced smoothing.
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---
```

## Example 3: End-to-End Self-Test

```bash
# Step 1: Generate conversations from scenarios CSV
python scripts/generate_test_conversations.py \
    --csv scenarios.csv \
    --output-dir conversations/ \
    --complexity advanced \
    --enhance

# Step 2: Generate skills from each conversation
for conv in conversations/*.json; do
    name=$(basename "$conv" .json)
    python scripts/generate_skill.py "$conv" \
        --output skills/"$name" \
        --name "$name"
done

# Step 3: Validate (manual or automated)
# Check each skill against references/quality-checklist.md
```
