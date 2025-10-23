# SVG Pan-Zoom Error Fix

## 🔴 Error

```
pan-zoom initialization failed: ReferenceError: svgPanZoom is not defined
at _diagram.html:408:25
at _diagram.html:390:25
```

## 🔍 Root Cause

The `svg-pan-zoom` library is not loading before the code tries to use it. This can happen due to:

1. **CDN blocked** - Network/firewall blocking CDN access
2. **Timing issue** - Code runs before library loads
3. **CDN unavailable** - External CDN temporarily down
4. **Corporate proxy** - Proxy blocking external JavaScript

## ✅ Solutions

### Solution 1: Check CDN Access (Quick Test)

Open the HTML file and check browser console (F12):

```javascript
// In browser console, check if library loaded:
console.log(typeof svgPanZoom);
// Should print: "function"
// If prints: "undefined" → CDN is blocked or not loading
```

### Solution 2: Use Local Copy of svg-pan-zoom Library

Download and bundle the library locally:

#### Step 1: Download Library
```bash
# Create lib directory
mkdir -p static/lib

# Download svg-pan-zoom library
curl -o static/lib/svg-pan-zoom.min.js https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js
```

#### Step 2: Update HTML Template

Edit `src/diagrams.py` around line 781:

**Before:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js"></script>
```

**After:**
```html
<!-- Try local copy first, fallback to CDN -->
<script src="static/lib/svg-pan-zoom.min.js"
        onerror="this.onerror=null; this.src='https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js';"></script>
```

### Solution 3: Add Loading Check and Retry

Add safety check before using `svgPanZoom`:

```javascript
function initializePanZoom() {
    setTimeout(() => {
        const svg = document.querySelector('#diagram-container svg');

        if (svg) {
            // Check if library is loaded
            if (typeof svgPanZoom === 'undefined') {
                console.warn('svg-pan-zoom library not loaded. Retrying in 2 seconds...');
                setTimeout(initializePanZoom, 2000); // Retry after 2 seconds
                return;
            }

            // Initialize svg-pan-zoom (existing code)
            try {
                panZoom = svgPanZoom(svg, {
                    // ... options ...
                });
                console.log('Pan-zoom initialized successfully');
            } catch(err) {
                console.error('Pan-zoom initialization failed:', err);
            }
        }
    }, 1000);
}
```

### Solution 4: Embed Library Inline (No External Dependencies)

For **completely offline** environments, embed the library directly in HTML:

```html
<script>
// Inline svg-pan-zoom library (full content)
// Download from: https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js
// Paste entire minified library here
!function(t,e){"function"==typeof define&&define.amd?define(function(){return t.svgPanZoom=e()}):"object"==typeof module&&module.exports?module.exports=e():t.svgPanZoom=e()}(this,function(){...});
</script>
```

### Solution 5: Use Alternative Library

Replace `svg-pan-zoom` with modern browser-native approach:

```javascript
function initializePanZoom() {
    const svg = document.querySelector('#diagram-container svg');
    if (!svg) return;

    let isPanning = false;
    let startPoint = {x: 0, y: 0};
    let endPoint = {x: 0, y: 0};
    let scale = 1;

    // Mouse wheel zoom
    svg.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        scale *= delta;
        svg.style.transform = `scale(${scale})`;
    });

    // Pan with mouse drag
    svg.addEventListener('mousedown', (e) => {
        isPanning = true;
        startPoint = {x: e.clientX, y: e.clientY};
    });

    svg.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        endPoint = {x: e.clientX, y: e.clientY};
        const dx = endPoint.x - startPoint.x;
        const dy = endPoint.y - startPoint.y;
        svg.style.transform = `translate(${dx}px, ${dy}px) scale(${scale})`;
    });

    svg.addEventListener('mouseup', () => {
        isPanning = false;
    });
}
```

## 🛠️ Quick Fix for Existing Deployments

If you don't want to modify code, add this to the HTML file manually:

```html
<!-- Add before closing </head> tag -->
<script>
// Fallback: retry initialization if library not loaded
window.addEventListener('load', function() {
    let retries = 0;
    const maxRetries = 5;

    function checkAndInit() {
        if (typeof svgPanZoom !== 'undefined') {
            // Library loaded, proceed with initialization
            if (typeof initializePanZoom === 'function') {
                initializePanZoom();
            }
        } else if (retries < maxRetries) {
            // Library not loaded yet, retry
            retries++;
            console.log(`Waiting for svg-pan-zoom library... (attempt ${retries}/${maxRetries})`);
            setTimeout(checkAndInit, 1000);
        } else {
            // Give up after max retries
            console.error('svg-pan-zoom library failed to load after ' + maxRetries + ' attempts');
            console.log('Pan/zoom features disabled. Diagram will still display.');
        }
    }

    checkAndInit();
});
</script>
```

## 📋 Verification Steps

### 1. Check Library Loading

Open HTML file in browser, press **F12** for Developer Tools:

**Console tab:**
```javascript
console.log(typeof svgPanZoom);
```

**Expected:** `function`
**If you see:** `undefined` → Library not loading

### 2. Check Network Tab

**F12 → Network tab → Reload page**

Look for:
- `svg-pan-zoom.min.js`
- **Status:** Should be `200 OK`
- **If status is:** `Failed` or `CORS error` → CDN blocked

### 3. Test Offline

Disconnect internet and reload HTML file:
- **With CDN:** Won't work
- **With local copy:** Should work

## 🔧 Recommended Fix for Production

Create a local fallback system:

### File: `src/diagrams.py` (update HTML template)

```python
# Around line 775-785
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <!-- Mermaid library -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>

    <!-- SVG Pan-Zoom with local fallback -->
    <script>
    // Check if CDN loads, else use fallback
    window.svgPanZoomLoaded = false;
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/svg-pan-zoom/3.6.1/svg-pan-zoom.min.js"
            onload="window.svgPanZoomLoaded = true;"
            onerror="console.warn('CDN failed, using native pan/zoom');">
    </script>

    <style>
    /* ... existing styles ... */
    </style>
</head>
'''
```

### Add Native Fallback Function

```python
# In the JavaScript section of the HTML template:
def initializePanZoom() {
    setTimeout(() => {
        const svg = document.querySelector('#diagram-container svg');

        if (!svg) {
            console.error('SVG element not found');
            return;
        }

        // Remove fixed dimensions
        svg.removeAttribute('width');
        svg.removeAttribute('height');
        svg.style.width = '100%';
        svg.style.height = 'auto';

        // Try svg-pan-zoom library first
        if (typeof svgPanZoom !== 'undefined' && window.svgPanZoomLoaded) {
            try {
                panZoom = svgPanZoom(svg, {
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: false,
                    center: false,
                    minZoom: 0.1,
                    maxZoom: 20,
                    zoomScaleSensitivity: 0.3
                });
                console.log('✓ Pan-zoom initialized successfully (library)');
                return;
            } catch(err) {
                console.error('svg-pan-zoom failed:', err);
            }
        }

        // Fallback to native implementation
        console.log('Using native pan/zoom (library unavailable)');
        initializeNativePanZoom(svg);

    }, 1000);
}

function initializeNativePanZoom(svg) {
    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX, startY;

    // Zoom on wheel
    svg.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        scale *= delta;
        scale = Math.max(0.1, Math.min(scale, 20)); // Clamp between 0.1 and 20
        updateTransform();
    });

    // Pan on drag
    svg.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
        svg.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        updateTransform();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        svg.style.cursor = 'grab';
    });

    function updateTransform() {
        svg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }

    svg.style.cursor = 'grab';
    console.log('✓ Native pan/zoom initialized');
}
```

## 📖 Summary

**Problem:** `svgPanZoom is not defined` error in HTML diagrams

**Causes:**
1. CDN blocked by firewall/proxy
2. Library loading too slowly
3. Network connectivity issues

**Solutions:**
1. **Quick:** Add retry logic with `setTimeout`
2. **Reliable:** Download library locally with CDN fallback
3. **Production:** Implement native pan/zoom as fallback
4. **Offline:** Embed library inline in HTML

**Recommended:** Option 3 (native fallback) - works with or without CDN

---

**Created:** 2025-10-22
**Issue:** SVG pan-zoom library not loading
**Impact:** Pan/zoom features don't work (diagram still displays)
**Fix:** Add native browser-based pan/zoom fallback
