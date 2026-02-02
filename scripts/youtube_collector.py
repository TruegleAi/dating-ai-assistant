#!/usr/bin/env python3
"""
YouTube Data Collector - Quick Start Version
"""
import yaml
import json
from datetime import datetime
import os

print("=" * 60)
print("Initializing Dating AI Knowledge Base")
print("=" * 60)

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Create sample knowledge structure
knowledge = {
    "metadata": {
        "collected": datetime.now().isoformat(),
        "channels": [c["name"] for c in config["curated_channels"]],
        "note": "Sample data - add YouTube API calls later"
    },
    "core_principles": [
        "Push-Pull Dynamics: Creating attraction through attention variability",
        "Qualification: Having her prove value rather than seeking validation",
        "Social Proof: Demonstrating value indirectly through lifestyle",
        "Cold Reading: Making personalized, seemingly insightful observations",
        "Fractionation: Rapid emotional pacing to build connection"
    ]
}

# Ensure directory exists
os.makedirs('data/processed', exist_ok=True)

# Save knowledge base
output_file = 'data/processed/initial_knowledge.json'
with open(output_file, 'w') as f:
    json.dump(knowledge, f, indent=2)

print(f"✅ Knowledge base created: {output_file}")
print(f"📺 Sources: {len(config['curated_channels'])} channels configured")
print("💡 Next: Add real YouTube API calls for full data collection")
print("=" * 60)
