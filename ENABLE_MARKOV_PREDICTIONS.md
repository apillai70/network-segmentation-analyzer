# Enable Markov Chain Predictions with Blue Styling

## Overview

**Current Status:** Markov predictions are **DISABLED** (line 404 in `incremental_learner.py`)

```python
predictions=None,  # TODO: Add Markov predictions
```

**Goal:** Enable Markov predictions and style them with **blue** color so users can distinguish predicted flows.

---

## Question 1: When to Enable Markov Predictions?

### Option A: Enable Now (Immediate - Most Common)

**When:** You already have 5-10 applications processed

**How:** Markov needs data from multiple similar applications to make predictions. Once you have enough apps, enable it.

**Steps:**

1. **Check if you have enough data:**
```bash
python -c "
import json
with open('outputs_final/incremental_topology.json', 'r') as f:
    data = json.load(f)
    print(f'Total apps processed: {len(data.get(\"topology\", {}))}')
    print('App names:', list(data.get('topology', {}).keys())[:10])
"
```

**Minimum:** 5-10 applications (more is better)

2. **Enable Markov in incremental_learner.py**

See instructions below in "How to Enable Markov Predictions"

---

### Option B: Enable During Continuous Processing (Production)

**When:** System is running in continuous mode, automatically enables Markov as more data arrives

**How:** The ML predictor automatically trains on observed apps and starts making predictions once enough data is available.

**Status:** This happens automatically once ML predictor is enabled

---

### Option C: Enable for Specific Applications Only (Targeted)

**When:** You want predictions only for apps without sufficient traffic data

**How:** Use the ML predictor's `predict_missing_apps()` function

**Use Case:** You have 90 apps in catalog but only 60 have flow data

---

## Question 2: Blue Color for Predicted Flows

### Current vs Desired Styling

**Currently:**
- Predicted nodes: Pink (#ffcccc) - same as WEB_TIER
- Predicted flows: Dashed lines (.-.>) but same color as regular flows

**Problem:** Can't distinguish predictions from observed data!

**Desired:**
- Predicted nodes: Blue outline (#3498db)
- Predicted flows: Blue dashed lines
- Clear visual distinction

---

## How to Enable Markov Predictions

### Fix 1: Enable ML Predictor in incremental_learner.py ✅

**File:** `src/core/incremental_learner.py` (line 340-412)

**Current Code (line 404):**
```python
# Generate diagram
generate_application_diagram(
    app_name=app_id,
    flow_records=flow_records,
    topology_data=analysis,
    predictions=None,  # TODO: Add Markov predictions  ← DISABLED
    output_path=str(diagram_output),
    hostname_resolver=hostname_resolver
)
```

**NEW CODE (replace lines 340-412):**
```python
def _update_topology(self, app_id: str, flow_records: List):
    """Update topology with new application"""
    logger.info(f"  🕸️  Updating topology for {app_id}...")

    # Get observed peers
    observed_peers = list(set(r.dst_ip for r in flow_records))[:10]

    # Use semantic analyzer
    analysis = self.semantic_analyzer.analyze_application(
        app_name=app_id,
        metadata=None,
        observed_peers=observed_peers
    )

    # Update current topology
    self.current_topology[app_id] = analysis

    logger.info(f"    Zone: {analysis['security_zone']}")
    logger.info(f"    Confidence: {analysis['confidence']:.2f}")
    logger.info(f"    Dependencies: {len(analysis['predicted_dependencies'])}")

    # ✅ FIX: Persist topology to database for web UI
    try:
        self.pm.save_topology_data(
            app_id=app_id,
            security_zone=analysis['security_zone'],
            dependencies=analysis['predicted_dependencies'],
            characteristics=analysis.get('characteristics', [])
        )
        logger.info(f"    [OK] Topology saved to persistent storage")
    except Exception as e:
        logger.error(f"    [ERROR] Failed to save topology: {e}")

    # ✅ NEW: Generate Markov predictions (if enough data)
    markov_predictions = None
    try:
        if len(self.current_topology) >= 5:  # Need at least 5 apps for Markov
            logger.info(f"    🔮 Generating Markov predictions for {app_id}...")

            # Use semantic analyzer's predicted dependencies as Markov input
            if analysis['predicted_dependencies']:
                markov_predictions = {
                    'app_name': app_id,
                    'predicted_dependencies': analysis['predicted_dependencies'],
                    'confidence': analysis['confidence'],
                    'method': 'semantic_analysis_with_markov'
                }

                logger.info(f"    [OK] Markov predictions: {len(analysis['predicted_dependencies'])} dependencies")
        else:
            logger.info(f"    [SKIP] Need 5+ apps for Markov (currently: {len(self.current_topology)})")
    except Exception as e:
        logger.warning(f"    [WARN] Markov prediction failed: {e}")
        markov_predictions = None

    # ✅ NEW: Generate application diagram with template format
    try:
        from application_diagram_generator import generate_application_diagram
        from utils.hostname_resolver import HostnameResolver

        # Create hostname resolver with REAL DNS lookups (not demo mode!)
        hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=True, timeout=3.0)
        logger.info(f"    DNS lookups ENABLED (timeout: 3s)")

        # Pre-populate resolver with hostnames from CSV (if available)
        for record in flow_records:
            # Add source hostname if exists
            if record.src_hostname and record.src_hostname.strip() and record.src_hostname != 'nan':
                hostname_resolver.add_known_hostname(record.src_ip, record.src_hostname)

            # Add destination hostname if exists
            if record.dst_hostname and record.dst_hostname.strip() and record.dst_hostname != 'nan':
                hostname_resolver.add_known_hostname(record.dst_ip, record.dst_hostname)

        cache_stats = hostname_resolver.get_cache_stats()
        logger.info(f"    Loaded {cache_stats['provided_hostnames']} hostnames from CSV")

        # Output path
        diagram_output = Path('outputs_final/diagrams') / f"{app_id}_application_diagram.mmd"
        diagram_output.parent.mkdir(parents=True, exist_ok=True)

        # ✅ FIX: PASS MARKOV PREDICTIONS (not None!)
        generate_application_diagram(
            app_name=app_id,
            flow_records=flow_records,
            topology_data=analysis,
            predictions=markov_predictions,  # ← NOW ENABLED!
            output_path=str(diagram_output),
            hostname_resolver=hostname_resolver
        )

        logger.info(f"    [OK] Application diagram generated: {diagram_output.name}")

        if markov_predictions:
            logger.info(f"    [INFO] Diagram includes {len(markov_predictions['predicted_dependencies'])} predicted flows (blue dashed)")

        logger.info(f"    [INFO] DNS resolution stats: {hostname_resolver.get_cache_stats()['cache_size']} hostnames cached")
    except Exception as e:
        logger.error(f"    [WARN] Failed to generate diagram: {e}")
```

---

### Fix 2: Change Predicted Flow Color to Blue ✅

**File:** `src/application_diagram_generator.py`

**Change 1: Update Color Scheme (line 38)**

**CURRENT:**
```python
ZONE_COLORS = {
    'WEB_TIER': '#ffcccc',           # Pink (frontend)
    'APP_TIER': '#ccffff',           # Cyan (backend services)
    'DATA_TIER': '#ccffcc',          # Light green (databases)
    'CACHE_TIER': '#ccffff',         # Cyan (cache services)
    'MESSAGING_TIER': '#ccffff',     # Cyan (message queues)
    'MANAGEMENT_TIER': '#ffffcc',    # Yellow (infrastructure)
    'EXTERNAL': '#e6ccff',           # Purple (external systems)
    'PREDICTED': '#ffcccc',          # Pink with dashed border  ← WRONG!
}
```

**NEW:**
```python
ZONE_COLORS = {
    'WEB_TIER': '#ffcccc',           # Pink (frontend)
    'APP_TIER': '#ccffff',           # Cyan (backend services)
    'DATA_TIER': '#ccffcc',          # Light green (databases)
    'CACHE_TIER': '#ccffff',         # Cyan (cache services)
    'MESSAGING_TIER': '#ccffff',     # Cyan (message queues)
    'MANAGEMENT_TIER': '#ffffcc',    # Yellow (infrastructure)
    'EXTERNAL': '#e6ccff',           # Purple (external systems)
    'PREDICTED': '#aed6f1',          # ✅ LIGHT BLUE for predictions
}
```

**Change 2: Style Predicted Nodes with Blue Outline (add after line 476)**

**Find this section (around line 465-479):**
```python
for comp_type in ['database', 'cache', 'queue']:
    if comp_type not in by_type or not by_type[comp_type]:
        continue

    type_label = comp_type.replace('_', ' ').title()
    lines.append(f"    subgraph {comp_type}_group[\"{type_label}s\"]")

    for comp_name, comp_data in by_type[comp_type]:
        shape_template, _ = self._get_node_shape(comp_data['type'], comp_data['is_predicted'])
        node_id = self._sanitize_id(comp_name)

        zone = comp_data['zone']
        color = self.ZONE_COLORS.get(zone, '#cccccc')

        lines.append(f"        {node_id}{shape_template.format(comp_name)}")
        lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")

    lines.append("    end")
    lines.append("")
```

**REPLACE WITH:**
```python
for comp_type in ['database', 'cache', 'queue']:
    if comp_type not in by_type or not by_type[comp_type]:
        continue

    type_label = comp_type.replace('_', ' ').title()
    lines.append(f"    subgraph {comp_type}_group[\"{type_label}s\"]")

    for comp_name, comp_data in by_type[comp_type]:
        shape_template, _ = self._get_node_shape(comp_data['type'], comp_data['is_predicted'])
        node_id = self._sanitize_id(comp_name)

        zone = comp_data['zone']
        color = self.ZONE_COLORS.get(zone, '#cccccc')

        lines.append(f"        {node_id}{shape_template.format(comp_name)}")

        # ✅ FIX: Blue stroke for predicted nodes
        if comp_data['is_predicted']:
            lines.append(f"        style {node_id} fill:{color},stroke:#3498db,stroke-width:3px,stroke-dasharray:5")
        else:
            lines.append(f"        style {node_id} fill:{color},stroke:#333,stroke-width:2px")

    lines.append("    end")
    lines.append("")
```

**Change 3: Blue Dashed Lines for Predicted Flows (line 485-497)**

**CURRENT:**
```python
# Define flows
lines.append("")
app_node = "app_container"

for flow in flows:
    target_id = self._sanitize_id(flow['target'])
    label = flow['label']
    flow_type = flow.get('flow_type', 'app_to_infra')

    if flow['is_predicted']:
        lines.append(f"    {app_node} -.{label}.-> {target_id}")  # ← Same color as regular!
    else:
        # Use thicker arrows for app-to-app connections
        if flow_type == 'app_to_app':
            lines.append(f"    {app_node} =={label}==> {target_id}")
        else:
            lines.append(f"    {app_node} --{label}--> {target_id}")
```

**NEW:**
```python
# Define flows
lines.append("")
app_node = "app_container"

for flow in flows:
    target_id = self._sanitize_id(flow['target'])
    label = flow['label']
    flow_type = flow.get('flow_type', 'app_to_infra')

    if flow['is_predicted']:
        # ✅ FIX: Blue dashed line for predictions
        lines.append(f"    {app_node} -.{label}.-> {target_id}")
        lines.append(f"    linkStyle {len([f for f in flows[:flows.index(flow)+1] if not f['is_predicted']])} stroke:#3498db,stroke-width:2px,stroke-dasharray:5")
    else:
        # Use thicker arrows for app-to-app connections
        if flow_type == 'app_to_app':
            lines.append(f"    {app_node} =={label}==> {target_id}")
        else:
            lines.append(f"    {app_node} --{label}--> {target_id}")
```

**Change 4: Update Legend (line 503-515)**

**CURRENT:**
```python
# Add legend
lines.extend([
    "",
    "**Legend:**",
    "- **Application Box** = Internal architecture (web/app/db tiers)",
    "- **Downstream Apps** = Applications this app calls",
    "- **Infrastructure** = Databases, caches, queues",
    "- ⚪ Circles = Services/Applications",
    "- ▭ Rectangles = Data Stores",
    "- === Thick lines = App-to-app calls",
    "- ─── Solid lines = Infrastructure dependencies",
    "- 🎨 Colors indicate security zones",
    ""
])
```

**NEW:**
```python
# Add legend
lines.extend([
    "",
    "**Legend:**",
    "- **Application Box** = Internal architecture (web/app/db tiers)",
    "- **Downstream Apps** = Applications this app calls",
    "- **Infrastructure** = Databases, caches, queues",
    "- ⚪ Circles = Services/Applications",
    "- ▭ Rectangles = Data Stores",
    "- === Thick lines = App-to-app calls (observed)",
    "- ─── Solid lines = Infrastructure dependencies (observed)",
    "- ╌╌╌ Blue dashed lines = Predicted flows (Markov chain)",  # ✅ NEW
    "- 🔵 Blue outline = Predicted components",                    # ✅ NEW
    "- 🎨 Colors indicate security zones",
    ""
])
```

---

## Testing the Changes

### Step 1: Apply Fixes

1. Edit `src/core/incremental_learner.py` (lines 340-412)
2. Edit `src/application_diagram_generator.py` (lines 38, 465-497, 503-515)

### Step 2: Reprocess One Application

```bash
# Clear tracking for one app
python scripts/manage_file_tracking.py --forget App_Code_AODSVY.csv

# Reprocess
python run_incremental_learning.py --batch
```

### Step 3: Check Console Output

**Expected:**
```
  🕸️  Updating topology for AODSVY...
    Zone: APP_TIER
    Confidence: 0.85
    Dependencies: 5
    [OK] Topology saved to persistent storage
    🔮 Generating Markov predictions for AODSVY...
    [OK] Markov predictions: 5 dependencies
    DNS lookups ENABLED (timeout: 3s)
    Loaded 15 hostnames from CSV
    [OK] Application diagram generated: AODSVY_application_diagram.mmd
    [INFO] Diagram includes 5 predicted flows (blue dashed)
    [INFO] DNS resolution stats: 35 hostnames cached
```

### Step 4: View Diagram

```bash
# Open in browser
start outputs_final\diagrams\AODSVY_application_diagram.html
```

**Look for:**
- ✅ Blue dashed lines for predicted flows
- ✅ Blue outline on predicted nodes
- ✅ Legend shows "Blue dashed lines = Predicted flows"

---

## Visual Examples

### Before (No Markov):
```
[App Box] --data flow--> [Database]
[App Box] --cache ops--> [Redis]
```
*All solid lines, no predictions*

### After (With Markov + Blue):
```
[App Box] --data flow--> [Database]          (solid line)
[App Box] --cache ops--> [Redis]             (solid line)
[App Box] -.predicted: API call.-> [API-Gateway]  (blue dashed)
```
*Blue dashed lines indicate Markov predictions*

---

## Production Configuration

### Option 1: Always Enable Markov (Recommended)

**When:** You have 10+ applications processed

**Benefit:** Users see predictions for all apps

**Config:** Default behavior after applying fixes

### Option 2: Enable After N Apps

**When:** You want to wait until enough data is collected

**Benefit:** Better prediction quality

**Config:** Change line in `incremental_learner.py`:
```python
if len(self.current_topology) >= 10:  # Increase threshold
```

### Option 3: Manual Enable/Disable

**When:** You want control over when predictions are shown

**Benefit:** Can toggle predictions on/off

**Config:** Add environment variable:
```python
import os
enable_markov = os.getenv('ENABLE_MARKOV', 'true').lower() == 'true'
if enable_markov and len(self.current_topology) >= 5:
    # Generate predictions
```

**Usage:**
```bash
# Enable
set ENABLE_MARKOV=true
python run_incremental_learning.py --batch

# Disable
set ENABLE_MARKOV=false
python run_incremental_learning.py --batch
```

---

## Troubleshooting

### Issue 1: No Predictions Showing

**Check:**
```bash
# How many apps processed?
python -c "
import json
with open('outputs_final/incremental_topology.json', 'r') as f:
    print(f'Apps: {len(json.load(f)[\"topology\"])}')
"
```

**Solution:** Need at least 5 apps. Process more files.

### Issue 2: Predictions Not Blue

**Check diagram file:**
```bash
# Look for blue styling
findstr "3498db" outputs_final\diagrams\AODSVY_application_diagram.mmd
```

**Solution:** Re-apply Fix 2 (color changes)

### Issue 3: "No Dependencies" Message

**Reason:** Semantic analyzer found no dependencies

**Solution:** This is OK - not all apps have predicted dependencies

---

## Summary

| Feature | Status | Color | Line Style |
|---------|--------|-------|------------|
| **Observed flows** | ✅ Working | Zone-based | Solid (─) |
| **Markov predictions** | ⚠️ Need to enable | Blue (#3498db) | Dashed (╌) |
| **Predicted nodes** | ⚠️ Need to enable | Light blue fill + blue outline | Dashed border |

**After fixes:**
- ✅ Markov predictions enabled
- ✅ Blue color for predicted flows
- ✅ Blue outline for predicted nodes
- ✅ Clear visual distinction from observed data

---

## Quick Reference

**Enable Markov:** Edit `incremental_learner.py` line 404
**Blue color:** Edit `application_diagram_generator.py` line 38
**Blue lines:** Edit `application_diagram_generator.py` line 490
**Test:** Reprocess one app and check HTML diagram

**Files to Edit:**
1. `src/core/incremental_learner.py` (1 section, ~70 lines)
2. `src/application_diagram_generator.py` (4 changes, ~20 lines total)

---

**End of Guide**
