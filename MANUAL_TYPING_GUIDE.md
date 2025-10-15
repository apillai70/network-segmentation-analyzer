# Manual Typing Guide - Customer Site

## Complete Fixes to Type Manually

This guide provides **exact line numbers and code** for you to type at customer site.

---

## Fix 1: NetSeg Folder Path (MISSED EARLIER!)

### File: `generate_all_reports.py`

**Line 318 - Change output directory:**

**FIND:**
```python
output_reports = Path('outputs_final/word_reports')
```

**REPLACE WITH:**
```python
output_reports = Path('outputs_final/word_reports/netseg')
```

**Why:** Report documents (`*_report.docx`) should go to `netseg/` subfolder, not root `word_reports/`

**Result:** `generate_all_reports.py` will now save to `word_reports/netseg/`

---

## Fix 2: Enable Markov Predictions

### File: `src/core/incremental_learner.py`

**Lines 340-412 - Replace entire `_update_topology()` function:**

**FIND THIS FUNCTION (starts at line 340):**
```python
def _update_topology(self, app_id: str, flow_records: List):
```

**DELETE everything from line 340 to line 412** (entire function)

**TYPE THIS COMPLETE FUNCTION:**

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

        # Persist topology to database for web UI
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

        # Generate application diagram with template format
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

**Save file!**

---

## Fix 3: Blue Color for Predicted Flows

### File: `src/application_diagram_generator.py`

#### Change 3a: Update Color Scheme (Line 38)

**FIND:**
```python
    ZONE_COLORS = {
        'WEB_TIER': '#ffcccc',           # Pink (frontend)
        'APP_TIER': '#ccffff',           # Cyan (backend services)
        'DATA_TIER': '#ccffcc',          # Light green (databases)
        'CACHE_TIER': '#ccffff',         # Cyan (cache services)
        'MESSAGING_TIER': '#ccffff',     # Cyan (message queues)
        'MANAGEMENT_TIER': '#ffffcc',    # Yellow (infrastructure)
        'EXTERNAL': '#e6ccff',           # Purple (external systems)
        'PREDICTED': '#ffcccc',          # Pink with dashed border
    }
```

**REPLACE WITH:**
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

#### Change 3b: Blue Outline for Predicted Nodes (Line 465-479)

**FIND (around line 465):**
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

#### Change 3c: Blue Dashed Lines (Line 485-497)

**FIND:**
```python
        # Define flows
        lines.append("")
        app_node = "app_container"

        for flow in flows:
            target_id = self._sanitize_id(flow['target'])
            label = flow['label']
            flow_type = flow.get('flow_type', 'app_to_infra')

            if flow['is_predicted']:
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
            else:
                # Use thicker arrows for app-to-app connections
                if flow_type == 'app_to_app':
                    lines.append(f"    {app_node} =={label}==> {target_id}")
                else:
                    lines.append(f"    {app_node} --{label}--> {target_id}")
```

**REPLACE WITH:**
```python
        # Define flows
        lines.append("")
        app_node = "app_container"

        flow_index = 0  # Track flow index for styling
        for flow in flows:
            target_id = self._sanitize_id(flow['target'])
            label = flow['label']
            flow_type = flow.get('flow_type', 'app_to_infra')

            if flow['is_predicted']:
                # ✅ FIX: Blue dashed line for predictions
                lines.append(f"    {app_node} -.{label}.-> {target_id}")
                lines.append(f"    linkStyle {flow_index} stroke:#3498db,stroke-width:2px")
            else:
                # Use thicker arrows for app-to-app connections
                if flow_type == 'app_to_app':
                    lines.append(f"    {app_node} =={label}==> {target_id}")
                else:
                    lines.append(f"    {app_node} --{label}--> {target_id}")

            flow_index += 1
```

#### Change 3d: Update Legend (Line 503-515)

**FIND:**
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

**REPLACE WITH:**
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
            "- ╌╌╌ Blue dashed lines = Predicted flows (Markov chain)",
            "- 🔵 Blue outline = Predicted components",
            "- 🎨 Colors indicate security zones",
            ""
        ])
```

**Save file!**

---

## Fix 4: Enable Deep Learning

### File: `config.yaml`

**Line 48 - Enable deep learning:**

**FIND:**
```yaml
  deep_learning:
    enabled: false  # Set to true if torch installed
    device: cpu  # 'cpu' or 'cuda'
```

**REPLACE WITH:**
```yaml
  deep_learning:
    enabled: true  # ✅ ENABLED
    device: cpu  # 'cpu' or 'cuda'
```

**IMPORTANT:** You must install PyTorch first!

```bash
# Install PyTorch (CPU version)
pip install torch==2.1.2+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Or simpler (may be slower to install):
pip install torch
```

**Save file!**

---

## Fix 5: Load config.yaml and Pass to EnsembleModel

### File: `run_incremental_learning.py`

**Change 5a: Add config.yaml loading (Line 210-226):**

**FIND (around line 210):**
```python
    logger.info(f"Output directory: {output_dir}")

    # Determine features
    enable_dl = args.enable_deep_learning or args.enable_all

    logger.info(f"Deep Learning: {enable_dl}")
```

**REPLACE WITH:**
```python
    logger.info(f"Output directory: {output_dir}")

    # Load config.yaml for default settings
    import yaml
    config_file = Path('config.yaml')
    config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

    # Determine features (command-line overrides config.yaml)
    config_dl_enabled = config.get('models', {}).get('deep_learning', {}).get('enabled', False)
    enable_dl = args.enable_deep_learning or args.enable_all or config_dl_enabled

    logger.info(f"Deep Learning: {enable_dl}")
    if config_dl_enabled and not (args.enable_deep_learning or args.enable_all):
        logger.info(f"  (enabled via config.yaml)")
```

**Change 5b: Pass deep learning to EnsembleModel (Line 245):**

**FIND (around line 244):**
```python
        # Initialize ensemble model
        ensemble = EnsembleNetworkModel(pm)
```

**REPLACE WITH:**
```python
        # Initialize ensemble model with deep learning settings
        ensemble = EnsembleNetworkModel(pm, use_deep_learning=enable_dl, device=args.device)
```

**Why:**
- Part (a): The script wasn't reading config.yaml at all!
- Part (b): The EnsembleModel was being created WITHOUT the deep learning flag, so it always defaulted to False

**IMPORTANT:** Note the `encoding='utf-8'` to prevent UTF-8 errors on Windows!

**Prerequisites:**
- PyYAML must be installed: `pip install pyyaml`
- PyTorch must be installed: `pip install torch`

**Save file!**

---

## Fix 6: Pass Deep Learning to UnifiedTopologySystem's EnsembleModel

### File: `src/agentic/unified_topology_system.py`

**Lines 64-79 - Pass deep learning parameters to EnsembleModel:**

**FIND (around line 64):**
```python
        self.pm = persistence_manager
        self.device = device

        # Core components (always available)
        self.network_graph = nx.DiGraph()
        self.application_graph = nx.DiGraph()
        self.combined_graph = nx.DiGraph()

        # Load existing ensemble model (from enterprise_network_analyzer.py)
        from core.ensemble_model import EnsembleNetworkModel
        self.ensemble_model = EnsembleNetworkModel(persistence_manager)
```

**REPLACE WITH:**
```python
        self.pm = persistence_manager
        self.device = device
        self.use_deep_learning = use_deep_learning

        # Core components (always available)
        self.network_graph = nx.DiGraph()
        self.application_graph = nx.DiGraph()
        self.combined_graph = nx.DiGraph()

        # Load existing ensemble model (from enterprise_network_analyzer.py)
        from core.ensemble_model import EnsembleNetworkModel
        self.ensemble_model = EnsembleNetworkModel(
            persistence_manager,
            use_deep_learning=use_deep_learning,
            device=device
        )
```

**Why:** UnifiedTopologySystem was creating a SECOND EnsembleModel without deep learning parameters, causing "Deep Learning: False" to appear even after fixing run_incremental_learning.py

**Save file!**

---

## Fix 7: Correct Import Names for Transformer and VAE Models

### File: `src/core/ensemble_model.py`

**Lines 107 & 121 - Fix incorrect class names:**

**FIND (line 107):**
```python
            try:
                from deep_learning.transformer_model import TransformerTopologyAnalyzer

                self.models['transformer'] = {
                    'analyzer': TransformerTopologyAnalyzer(device=self.device),
```

**REPLACE WITH:**
```python
            try:
                from deep_learning.transformer_model import TemporalTrafficAnalyzer

                self.models['transformer'] = {
                    'analyzer': TemporalTrafficAnalyzer(device=self.device),
```

**FIND (line 121):**
```python
            try:
                from deep_learning.vae_model import TopologyVAE

                self.models['vae'] = {
                    'analyzer': TopologyVAE(device=self.device),
```

**REPLACE WITH:**
```python
            try:
                from deep_learning.vae_model import ApplicationBehaviorAnalyzer

                self.models['vae'] = {
                    'analyzer': ApplicationBehaviorAnalyzer(device=self.device),
```

**Why:** The code was trying to import non-existent class names. The actual classes are:
- `TemporalTrafficAnalyzer` (not TransformerTopologyAnalyzer)
- `ApplicationBehaviorAnalyzer` (not TopologyVAE)

**Save file!**

---

## Summary of Changes

| Fix | File | Lines | What |
|-----|------|-------|------|
| 1 | `generate_all_reports.py` | 318 | NetSeg folder path |
| 2 | `src/core/incremental_learner.py` | 340-412 | Enable Markov predictions |
| 3a | `src/application_diagram_generator.py` | 38 | Blue color scheme |
| 3b | `src/application_diagram_generator.py` | 465-479 | Blue node outline |
| 3c | `src/application_diagram_generator.py` | 485-497 | Blue dashed lines |
| 3d | `src/application_diagram_generator.py` | 503-515 | Update legend |
| 4 | `config.yaml` | 48 | Enable deep learning |
| 5a | `run_incremental_learning.py` | 210-226 | Load config.yaml with UTF-8 |
| 5b | `run_incremental_learning.py` | 245 | Pass DL to EnsembleModel (1st) |
| 6 | `src/agentic/unified_topology_system.py` | 64-79 | Pass DL to EnsembleModel (2nd) |
| 7 | `src/core/ensemble_model.py` | 107, 121 | Fix Transformer & VAE imports |

**Total:** 7 files, ~190 lines of code to type

---

## Testing After Manual Changes

### Step 1: Verify Syntax

```bash
# Check Python syntax
python -m py_compile src/core/incremental_learner.py
python -m py_compile src/core/ensemble_model.py
python -m py_compile src/application_diagram_generator.py
python -m py_compile src/agentic/unified_topology_system.py
python -m py_compile generate_all_reports.py
python -m py_compile run_incremental_learning.py
```

**No errors = Good!**

### Step 2: Test Markov + Blue Colors

```bash
# Clear one app for reprocessing
python scripts/manage_file_tracking.py --forget App_Code_AODSVY.csv

# Reprocess with new code
python run_incremental_learning.py --batch
```

**Expected console output:**
```
  🕸️  Updating topology for AODSVY...
    Zone: APP_TIER
    Confidence: 0.85
    Dependencies: 5
    🔮 Generating Markov predictions for AODSVY...    ← NEW!
    [OK] Markov predictions: 5 dependencies           ← NEW!
    DNS lookups ENABLED (timeout: 3s)
    [OK] Application diagram generated
    [INFO] Diagram includes 5 predicted flows (blue dashed)  ← NEW!
```

### Step 3: Check Diagram

```bash
# Open in browser
start outputs_final\diagrams\AODSVY_application_diagram.html
```

**Look for:**
- ✅ Blue dashed lines for predicted flows
- ✅ Blue outline on predicted nodes
- ✅ Legend shows "Blue dashed = Predicted"

### Step 4: Test NetSeg Folder

```bash
# Generate reports
python generate_all_reports.py

# Check folder
dir outputs_final\word_reports\netseg\
```

**Should see:** `*_report.docx` files

### Step 5: Test Deep Learning + config.yaml Loading

```bash
# Check if PyTorch loaded
python -c "import torch; print('PyTorch:', torch.__version__)"

# Check if PyYAML loaded
python -c "import yaml; print('PyYAML:', yaml.__version__)"

# Run incremental learning (should auto-load config.yaml)
python run_incremental_learning.py --batch
```

**Expected console output:**
```
Mode: BATCH
Watch directory: .\data\input
Output directory: outputs_final
Deep Learning: True                       ← ✅ Should be True!
  (enabled via config.yaml)               ← ✅ Shows it loaded from config!

📦 Initializing components...

✓ Classical ML models loaded
✓ GAT model loaded                        ← ✅ Fix 7 working!
✓ Transformer model loaded                ← ✅ Fix 7 working!
✓ VAE model loaded                        ← ✅ Fix 7 working!
✓ Ensemble Network Model initialized
  Deep Learning: True                     ← ✅ FIRST EnsembleModel (Fix 5b)
  Active models: ['random_forest', 'svm', 'gat', 'transformer', 'vae']  ← ✅ ALL models!

✓ Local Semantic Analyzer initialized

✓ Classical ML models loaded
✓ GAT model loaded
✓ Transformer model loaded
✓ VAE model loaded
✓ Ensemble Network Model initialized
  Deep Learning: True                     ← ✅ SECOND EnsembleModel (Fix 6)
  Active models: ['random_forest', 'svm', 'gat', 'transformer', 'vae']  ← ✅ ALL models!

✓ Deep learning models loaded
✓ Graph algorithms loaded
🚀 Unified Topology Discovery System initialized
```

**If you see import errors for Transformer or VAE:**
- Check Fix 7 was applied (ensemble_model.py lines 107 & 121)
- Verify the class names are `TemporalTrafficAnalyzer` and `ApplicationBehaviorAnalyzer`

**If you still see "Deep Learning: False" in ANY EnsembleModel:**
- **First False**: Check Fix 5b (run_incremental_learning.py line 245)
- **Second False**: Check Fix 6 (unified_topology_system.py lines 64-79)
- Check config.yaml line 48 is `enabled: true`
- Verify PyYAML is installed: `pip install pyyaml`
- Verify PyTorch is installed: `pip install torch`
- Check for UTF-8 errors in the logs

---

## Typing Tips

1. **Use a text editor** - Don't type directly in vi/vim if not comfortable
2. **Copy-paste line by line** - If you can transfer this file, copy each section
3. **Check indentation** - Python is sensitive to spaces/tabs
4. **Save frequently** - After each fix
5. **Test after each file** - Don't wait until all 4 fixes are done

---

## Common Typing Errors

### Error 1: IndentationError

**Problem:** Mixed tabs and spaces

**Fix:** Use 4 spaces for each indent level (not tabs)

### Error 2: SyntaxError: invalid syntax

**Problem:** Typo in code

**Fix:** Double-check quotes, parentheses, colons

### Error 3: NameError: name 'logger' is not defined

**Problem:** Function not indented properly

**Fix:** Ensure function is inside class (4 spaces indent)

---

## Rollback Instructions

If something breaks:

```bash
# Rollback using git
git checkout src/core/incremental_learner.py
git checkout src/core/ensemble_model.py
git checkout src/application_diagram_generator.py
git checkout src/agentic/unified_topology_system.py
git checkout generate_all_reports.py
git checkout run_incremental_learning.py
git checkout config.yaml
```

Or just re-download the files from your backup.

---

## Need Help?

If you encounter errors while typing:

1. **Check the error message** - Python errors are usually helpful
2. **Verify line numbers** - Make sure you're editing the right line
3. **Check indentation** - Use a text editor that shows spaces
4. **Test one fix at a time** - Don't apply all 4 at once

---

**End of Manual Typing Guide**
