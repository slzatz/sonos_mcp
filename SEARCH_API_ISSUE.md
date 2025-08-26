# Amazon Music API Search Parsing Issue

## Summary
The SoCo library fails to parse certain Amazon Music API search responses, causing `TypeError: string indices must be integers, not 'str'` when specific search terms are used.

## Error Details
- **Location**: `soco/music_services/data_structures.py:146`
- **Code**: `class_key = result_type_proper + raw_item["itemType"].title()`
- **Issue**: `raw_item` is returned as a string instead of expected dictionary structure
- **Exception**: `TypeError: string indices must be integers, not 'str'`

## Reproduction Examples

### ❌ Failing Searches
```bash
sonos searchtrack "fixing her hair"
sonos searchtrack "fixing her hair by ani difranco" 
sonos searchtrack "mrs robinson counting crows"
```

### ✅ Working Alternatives
```bash
sonos searchtrack "fixing hair"          # Returns: Fixing Her Hair-Ani DiFranco-Imperfectly
sonos searchtrack "ani difranco"         # Works fine
sonos searchtrack "32 flavors by ani difranco"  # Works fine
```

## Pattern Analysis
- **Not related to result count**: Both single and multiple result queries can fail
- **Search term specific**: Certain combinations of words trigger malformed API responses
- **Inconsistent**: Similar searches work fine, suggesting API parsing edge cases
- **Song exists**: The content is available, but specific query formats break parsing

## Root Cause
Amazon Music API occasionally returns response data in an unexpected format that the SoCo library's `parse_response()` function cannot handle. The parsing code expects `raw_item` to be a dictionary with an "itemType" key, but receives a string instead.

## Impact
- Intermittent search failures for valid content
- Unpredictable behavior based on search term combinations  
- Users must guess alternative search terms when errors occur

## Potential Solutions
1. **SoCo Library Fix**: Add error handling in `parse_response()` to handle malformed API responses
2. **Retry Logic**: Implement automatic retry with modified search terms
3. **Search Sanitization**: Pre-process search terms to avoid known problematic patterns
4. **Graceful Fallback**: Return empty results instead of crashing on parsing errors

## Next Steps
- Examine SoCo library source code in `data_structures.py`
- Develop a robust parsing fix that handles both dictionary and string responses
- Submit pull request to SoCo project with fix
- Implement local workaround in our search functions

## Files for Reference
- `/home/slzatz/sonos_cli/.venv/lib/python3.13/site-packages/soco/music_services/data_structures.py:146`
- `/home/slzatz/sonos_cli/.venv/lib/python3.13/site-packages/soco/music_services/music_service.py:915`

## Test Cases for Validation
```python
# Test cases that should work after fix
test_searches = [
    "fixing her hair",
    "fixing her hair by ani difranco", 
    "mrs robinson counting crows",  # (should return empty results gracefully)
    "live harvest neil young",      # (should continue working)
]
```

*Documented: 2025-08-26*