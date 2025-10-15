# DNS Lookup Enabled - Real Hostname Resolution

## Change Summary

**Previously:** Hostname resolver was in **demo mode** → Generated fake names like "web-srv-35"

**Now:** Hostname resolver uses **REAL DNS lookups** via nslookup → Shows actual hostnames

---

## What Changed

### File: `src/core/incremental_learner.py` (Line 379)

**Before:**
```python
hostname_resolver = HostnameResolver(demo_mode=True)
```

**After:**
```python
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=True, timeout=3.0)
```

---

## How It Works Now

### Resolution Order:

1. **Check CSV columns first** (Source Hostname, Dest Hostname)
   - If CSV has hostnames, use those (no DNS lookup needed)
   - Cached for subsequent uses

2. **Perform reverse DNS lookup** (nslookup)
   - Uses `socket.gethostbyaddr()` (Python's built-in nslookup)
   - Timeout: 3 seconds per IP
   - Caches result to avoid repeat lookups

3. **Fallback to IP address**
   - If DNS lookup fails or times out, shows IP address

---

## Expected Behavior

### During Processing:

```
python run_incremental_learning.py --batch
```

**Console Output:**
```
  DNS lookups ENABLED (timeout: 3s)
  Loaded 0 hostnames from CSV  (if CSV columns are empty)
  [OK] Application diagram generated: AODSVY_application_diagram.mmd
  [INFO] DNS resolution stats: 152 hostnames cached  (after DNS lookups)
```

### In the Diagram:

**Instead of:**
- web-srv-35
- app-srv-67
- db-srv-102

**You'll see:**
- web-prod-01.company.local
- app-backend-03.company.local
- db-primary-01.company.local

(Actual hostnames from your DNS server)

---

## Performance Considerations

### ⚠️ WARNING: DNS Lookups Can Be SLOW

**Your AODSVY file has 924 flows.**

If each unique IP needs DNS lookup:
- 100 unique IPs × 3 sec timeout = **5 minutes** (worst case)
- With successful lookups (faster): **30-60 seconds**

### Progress Indicators:

The system will show:
```
  Processing: App_Code_AODSVY.csv
  Loaded 924 flows for AODSVY
  🕸️ Updating topology for AODSVY...
  DNS lookups ENABLED (timeout: 3s)
  Loaded 0 hostnames from CSV
  [SLOW - DNS lookups in progress...]
```

---

## How to Speed Up (Options)

### Option 1: Pre-populate CSV with Hostnames

If you already have a hostname mapping, add them to the CSV:

```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
AODSVY,10.100.246.18,app-server-01,10.164.116.35,db-server-05,1521,TCP,0,0
```

**Benefit:** No DNS lookup needed, instant processing

### Option 2: Reduce DNS Timeout

Edit `incremental_learner.py` line 379:

```python
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=True, timeout=1.0)
# Reduce from 3s to 1s
```

**Benefit:** Faster, but may miss some slow DNS responses

### Option 3: Disable DNS Lookups (Use IPs Only)

Edit `incremental_learner.py` line 379:

```python
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=False)
```

**Benefit:** Fast processing, but shows IP addresses instead of hostnames

### Option 4: Use Demo Mode for Quick Testing

Edit `incremental_learner.py` line 379:

```python
hostname_resolver = HostnameResolver(demo_mode=True)
```

**Benefit:** Fast, generates synthetic hostnames for testing

---

## Troubleshooting

### Issue: Processing takes forever

**Solution 1: Reduce timeout**
```python
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=True, timeout=1.0)
```

**Solution 2: Disable DNS temporarily**
```python
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=False)
```

### Issue: Still seeing fake names like "web-srv-35"

**Check:**
1. Did you re-run the processing? Old diagrams won't update automatically.
2. Clear old outputs first:
   ```cmd
   del outputs_final\diagrams\AODSVY*
   python run_incremental_learning.py --batch
   ```

### Issue: DNS lookups failing / showing IP addresses

**Possible causes:**
1. **DNS server not configured** on customer network
2. **Firewall blocking** DNS queries
3. **Reverse DNS not configured** for internal IPs
4. **Network timeout** issues

**Check DNS connectivity:**
```cmd
# Windows
nslookup 10.100.246.18

# Linux
host 10.100.246.18
dig -x 10.100.246.18
```

### Issue: "DNS lookup failed for 10.x.x.x"

This is **NORMAL** for internal IPs if:
- Reverse DNS is not configured
- IP is not registered in DNS
- DNS server is unreachable

**Result:** Diagram will show IP address (10.x.x.x) instead of hostname

---

## DNS Lookup Log Messages

### Success:
```
DEBUG: DNS lookup: 10.100.246.18 -> app-server-01.company.local
```

### Failure (Normal):
```
DEBUG: DNS lookup failed for 10.100.246.18: [Errno 11001] getaddrinfo failed
```

### Timeout:
```
DEBUG: DNS lookup failed for 10.100.246.18: timed out
```

---

## CSV Format for Pre-populated Hostnames

If you have a hostname mapping file, format it like this:

```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
AODSVY,10.100.246.18,app-prod-01,10.164.116.35,db-primary-01,1521,TCP,100,200
AODSVY,10.164.105.74,web-frontend-02,10.164.116.125,db-primary-02,8443,HTTPS,1000,2000
```

**Benefit:** No DNS lookups needed, instant processing

---

## Configuration Summary

| Mode | Setting | Speed | Accuracy | Use Case |
|------|---------|-------|----------|----------|
| **DNS Enabled** (Current) | `demo_mode=False, enable_dns_lookup=True` | Slow (1-5 min) | Real hostnames | Production |
| **DNS Disabled** | `demo_mode=False, enable_dns_lookup=False` | Fast (seconds) | IP addresses only | Quick analysis |
| **Demo Mode** | `demo_mode=True` | Fast (seconds) | Fake hostnames | Testing/Demo |
| **CSV Pre-populated** | (CSV has hostnames) | Fast (seconds) | Real hostnames | Best option |

---

## Recommendation for Customer Site

### Initial Processing (First Time):
```python
# Use DNS lookups to discover hostnames
hostname_resolver = HostnameResolver(demo_mode=False, enable_dns_lookup=True, timeout=2.0)
```

**Result:** Cache file with all resolved hostnames

### Subsequent Processing:
```python
# Reuse cached hostnames (faster)
# The cache persists across runs
```

### For Quick Testing:
```python
# Use demo mode
hostname_resolver = HostnameResolver(demo_mode=True)
```

---

## Files Modified

1. ✅ `src/core/incremental_learner.py` (Line 379)
   - Changed `demo_mode=True` to `demo_mode=False, enable_dns_lookup=True`
   - Added CSV hostname pre-population
   - Added cache statistics logging

---

## Next Steps

1. **Test the DNS lookups:**
   ```cmd
   python run_incremental_learning.py --batch
   ```

2. **Check the output:**
   - Look for "DNS lookups ENABLED"
   - Note how many hostnames were resolved
   - Check if processing is reasonably fast

3. **View the diagram:**
   ```cmd
   start outputs_final\diagrams\AODSVY_application_diagram.html
   ```

4. **If too slow:**
   - Reduce timeout to 1 second
   - Or disable DNS lookups
   - Or pre-populate CSV with hostnames

---

## Contact

If DNS lookups are too slow or not working:
1. Check network connectivity to DNS server
2. Verify reverse DNS is configured for internal IPs
3. Consider pre-populating CSV with hostnames
4. Or use IP addresses (disable DNS lookups)
