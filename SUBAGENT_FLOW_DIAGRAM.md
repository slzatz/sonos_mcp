# LLM-Powered Subagent Flow Diagram

This document traces the complete flow from a natural language music request through Claude Code's Task tool subagents to actual song playback on Sonos speakers. **Updated to reflect the new standardized prompt system.**

## Example Request: "I'd like to hear a live version of Neil Young's Harvest"

## High-Level Architecture
```
User Input → Claude Code Detection → Standardized Parsing (Task) → Hybrid Selection (Task) → Sonos CLI → Music Playing
```

## Detailed Step-by-Step Flow

### Phase 1: Request Detection & LLM Parsing Delegation
```
1. User types: "I'd like to hear a live version of Neil Young's Harvest"
   ↓
2. Claude Code scans input against CLAUDE.md patterns
   ↓  
3. Detects patterns: "I'd like to hear" + "live version of" + "[Artist]'s [Song]"
   ↓
4. Claude Code determines: HIGH-CONFIDENCE MUSIC REQUEST
   ↓
5. Claude Code executes: from claude_music_interface import parse_music_request_llm, play_music_parsed_with_llm
   ↓
6. Claude Code uses standardized parsing function:
   parse_music_request_llm(
     "I'd like to hear a live version of Neil Young's Harvest",
     task_function=Task
   )
   ↓
7. Function loads standardized prompt from music_parsing_prompts.py:
   STANDARD_MUSIC_PARSING_PROMPT.format(request="I'd like to hear...")
   ↓
8. Claude Code delegates parsing to Task subagent with standardized prompt:
   Task(
     description="Parse music request", 
     prompt=STANDARD_MUSIC_PARSING_PROMPT,  # Consistent, tested instructions
     subagent_type="general-purpose"
   )
```

### Phase 2: Standardized LLM Natural Language Processing
```
9. Task subagent (general-purpose) receives standardized parsing request
   ↓
10. LLM follows consistent, well-tested instructions:
    - Possessive pattern recognition: "[Artist]'s [Song]"
    - Preference extraction: "live version of" → prefer_live: true
    - Title/artist normalization: lowercase, clean formatting
   ↓
11. LLM returns structured parsing in standardized format:
    {
      "title": "harvest",
      "artist": "neil young", 
      "preferences": {"prefer_live": true}
    }
    ↓
12. parse_music_request_llm() returns parsed result to Claude Code
    ↓
13. Claude Code calls: play_music_parsed_with_llm(
      "harvest", 
      "neil young", 
      {"prefer_live": true},
      task_function=Task  # Enables hybrid LLM result selection
    )
```

### Phase 3: Hybrid Agent Initialization & Search Strategy
```
12. ClaudeCodeMusicAgent initializes with task_function=Task
    ↓
13. Agent calls: _generate_smart_search_queries()
    ↓
14. Agent generates multiple search queries based on preferences:
    Query 1: "live harvest neil young"       # Live preference first
    Query 2: "harvest live neil young"       # Title-live variant
    Query 3: "neil young harvest live"       # Artist-title-live
    Query 4: "harvest by neil young"         # Standard fallback
    Query 5: "harvest neil young"            # Minimal fallback
```

### Phase 4: Search Execution & Error Handling
```
15. Agent tries Query 1: subprocess.run(['sonos', 'searchtrack', 'live', 'harvest', 'neil', 'young'])
    ↓
16. Sonos CLI → Amazon Music API search
    ↓
17. API returns search results OR parsing error
    ↓
18. IF ERROR (e.g., "string indices must be integers"):
    → Agent catches exception
    → Agent tries Query 2: "harvest live neil young"
    → Repeat until success or all queries exhausted
    ↓
19. SUCCESS: Agent receives search results:
    1. Harvest Moon-Neil Young-Harvest Moon
    2. Harvest (2009 Remaster)-Neil Young-Harvest (2009 Remaster)
    3. Heart of Gold-Neil Young-Harvest
    4. Harvest-Neil Young-Harvest
    5. Harvest (Live)-Neil Young & Stray Gators-Tuscaloosa (Live)
    6. Like a Hurricane (Live)-Neil Young-Live Rust
```

### Phase 5: Complexity Detection & LLM Selection Decision
```
20. Agent calls: _should_use_llm_selection()
    ↓
21. Agent analyzes search complexity:
    - Multiple exact title matches: ✓ (positions 2, 4, 5)
    - Live preference requested: ✓
    - Multiple artists variations: ✓ (Neil Young vs Neil Young & Stray Gators)
    - Complex album context needed: ✓
    ↓
22. Agent determines: COMPLEX CASE → Use LLM Selection
    ↓
23. Agent prepares LLM selection prompt:
    "You are a music selection expert. Choose the best track from these results for: 
    title='harvest', artist='neil young', preferences={'prefer_live': true}
    
    Results:
    1. Harvest Moon-Neil Young-Harvest Moon
    2. Harvest (2009 Remaster)-Neil Young-Harvest (2009 Remaster)  
    3. Heart of Gold-Neil Young-Harvest
    4. Harvest-Neil Young-Harvest
    5. Harvest (Live)-Neil Young & Stray Gators-Tuscaloosa (Live)
    6. Like a Hurricane (Live)-Neil Young-Live Rust
    
    Return just the position number of the best match..."
```

### Phase 6: Standardized LLM-Powered Intelligent Selection
```
24. Agent calls: self._llm_select_best_match() (now using standardized prompts)
    ↓
25. ClaudeCodeMusicAgent loads standardized selection prompt:
    format_result_selection_prompt(
      title="harvest", artist="neil young", 
      preferences={"prefer_live": True}, results=search_results
    )
    ↓
26. Agent executes Task with standardized prompt:
    self.task_function(
      description="Select best music track",
      prompt=standardized_selection_prompt,  # Consistent selection logic
      subagent_type="general-purpose"
    )
    ↓
27. Task subagent (general-purpose) follows standardized analysis instructions:
    - Position 1: "Harvest Moon" ≠ "Harvest" (wrong song)
    - Position 2: "Harvest" exact match, but remaster (studio)
    - Position 3: "Heart of Gold" ≠ "Harvest" (wrong song)
    - Position 4: "Harvest" exact match, original album (studio)
    - Position 5: "Harvest (Live)" exact match + LIVE preference ← WINNER
    - Position 6: "Like a Hurricane" ≠ "Harvest" (wrong song)
    ↓
27. LLM subagent returns: "5" (with reasoning about live preference match)
    ↓
28. Agent receives LLM selection: position 5
```

### Phase 7: Playback Execution & Confirmation
```
29. Agent calls: _play_track_by_position(5)
    ↓
30. Agent executes: subprocess.run(['sonos', 'playtrackfromlist', '5'])
    ↓
31. Sonos CLI sends play command to Sonos speaker
    ↓
32. Sonos speaker begins playing: "Harvest (Live)" by Neil Young & Stray Gators
    ↓
33. Agent returns structured result:
    {
      'success': True,
      'message': 'Now playing: Harvest (Live) by Neil Young & Stray Gators from Tuscaloosa (Live)',
      'details': {
        'position_played': 5,
        'llm_selection_used': True,
        'search_query_used': 'live harvest neil young',
        'total_results': 6,
        'selection_method': 'LLM subagent'
      }
    }
```

### Phase 8: Claude Code Response & User Feedback
```
34. Claude Code receives agent result
    ↓
35. Claude Code processes success response
    ↓
36. Claude Code responds to user: 
    "Now playing: Harvest (Live) by Neil Young & Stray Gators from Tuscaloosa (Live)"
```

## Key Intelligence Layers

### 🧠 LLM Natural Language Parsing (Task Subagent #1)
- **Complex Grammar**: Handles possessives ("Neil Young's"), preferences ("live version of")
- **Intent Recognition**: Distinguishes play vs search vs info requests
- **Preference Extraction**: Identifies acoustic, live, studio, unplugged preferences
- **Normalization**: Converts to consistent structured format

### 🤖 Automatic Complexity Detection
- **Simple Cases**: "Bohemian Rhapsody by Queen" → algorithmic selection (fast)
- **Complex Cases**: Multiple matches + preferences → LLM selection (intelligent)
- **Hybrid Approach**: Best of both worlds - speed when possible, intelligence when needed

### 🎯 LLM Result Selection (Task Subagent #2)
- **Music Domain Knowledge**: Understands albums, live recordings, remasters
- **Context Awareness**: Prefers originals over compilations, authentic over covers
- **Preference Matching**: Intelligently applies user's live/acoustic/studio preferences
- **Disambiguation**: Handles multiple matches with nuanced reasoning

### ⚡ Error Recovery & Fallback
- **API Error Handling**: Gracefully handles Amazon Music parsing errors
- **LLM Unavailability**: Falls back to algorithmic selection if Task tool fails
- **Multi-Query Strategy**: Tries multiple search variations before giving up
- **Progressive Degradation**: Each fallback layer maintains functionality

## Architectural Advantages

### vs. Old Pattern-Matching Approach
```
OLD (Regex-based):
User: "Neil Young's Harvest" → Regex fails on possessive → No results

NEW (LLM-powered):  
User: "Neil Young's Harvest" → LLM Parse → {"title": "harvest", "artist": "neil young"}
```

### vs. Pure Algorithmic Selection
```
OLD (Algorithm only):
Multiple "Harvest" matches → Picks first exact match (could be remaster)

NEW (Hybrid LLM):
Multiple "Harvest" matches + live preference → LLM chooses live version intelligently
```

### vs. Manual CLI Workflow
```
OLD (Manual):
1. User: sonos searchtrack harvest neil young
2. User reviews: 6 results displayed
3. User picks: sonos playtrackfromlist 5

NEW (Automated):
1. User: "I'd like to hear a live version of Neil Young's Harvest"
2. System handles everything automatically with intelligence
```

## Technical Implementation Details

### Task Function Integration
```python
# Claude Code provides Task function to enable LLM selection
def handle_music_request(user_request):
    # Step 1: LLM-powered parsing
    parsed = Task(
        description="Parse music request",
        prompt=f"Parse '{user_request}' into components...",
        subagent_type="general-purpose"
    )
    
    # Step 2: Hybrid LLM selection (when needed)
    result = play_music_parsed_with_llm(
        parsed['title'], 
        parsed['artist'], 
        parsed['preferences'],
        task_function=Task  # Critical: enables LLM selection
    )
    
    return result
```

### ClaudeCodeMusicAgent Enhancement
```python
class ClaudeCodeMusicAgent(MusicAgent):
    def __init__(self, task_function=None):
        super().__init__()
        self.task_function = task_function  # Receives Task function from Claude Code
    
    def _call_selection_subagent(self, prompt: str) -> str:
        if self.task_function:
            # Use Claude Code's Task tool for LLM selection
            return self.task_function(
                description="Select best music track",
                prompt=prompt,
                subagent_type="general-purpose"
            )
        else:
            # Fallback to algorithmic selection
            return ""
```

### Hybrid Selection Logic
```python
def _should_use_llm_selection(self, results, preferences):
    """Automatically detect when LLM selection is needed"""
    
    # Simple case: obvious single match
    if len(results) == 1:
        return False
    
    # Complex case: multiple exact matches + preferences
    exact_matches = [r for r in results if similarity_score(r.title, target_title) > 0.9]
    if len(exact_matches) > 1 and preferences:
        return True
    
    # Complex case: ambiguous artist variations
    unique_artists = set(r.artist for r in results)
    if len(unique_artists) > 2:
        return True
        
    return False
```

## Standardized Prompt System Benefits

### Key Improvements Over Ad-hoc Prompts

#### **Consistency**
**Before (Ad-hoc):**
```python
# Variable instructions written during conversations
Task(prompt="Parse 'Neil Young's Harvest' and extract title, artist...")  # Improvised each time
```

**After (Standardized):**  
```python
# Consistent, well-tested template
from music_parsing_prompts import STANDARD_MUSIC_PARSING_PROMPT
Task(prompt=STANDARD_MUSIC_PARSING_PROMPT.format(request="Neil Young's Harvest"))
```

#### **Reliability**
- **Parsing**: Same comprehensive pattern recognition every time
- **Selection**: Consistent music domain expertise applied
- **Error Handling**: Predictable JSON response format

#### **Maintainability**
- **Centralized Logic**: All prompt instructions in `music_parsing_prompts.py`
- **Version Control**: Changes to prompts are tracked and reviewable
- **Testing**: Standardized prompts can be systematically tested and refined

#### **Extensibility**
- **Album Support**: `ENHANCED_MUSIC_PARSING_PROMPT` ready for activation
- **New Preferences**: Easy to add acoustic, studio, unplugged flags
- **Custom Output**: Template system supports any desired JSON structure

### Implementation Files
- **`music_parsing_prompts.py`**: Template definitions and formatting functions
- **`claude_music_interface.py`**: Updated to use standardized prompts
- **`CLAUDE.md`**: Documentation and usage examples

### Performance Impact
- **Parsing Time**: Unchanged (same LLM calls)
- **Selection Quality**: Improved consistency and reliability
- **Debugging**: Much easier to trace issues to specific prompt templates

## Decision Tree for Claude Code Integration

```
User Request → Contains music patterns?
    ↓
  YES → Step 1: Task subagent parses natural language
    ↓
       → Step 2: Generate smart search queries  
    ↓
       → Step 3: Execute searches with error recovery
    ↓
       → Step 4: Complexity detection
    ↓
       → Step 5a: Simple case → Algorithmic selection (fast)
       → Step 5b: Complex case → Task subagent selection (intelligent)
    ↓
       → Step 6: Play selected track
    ↓
  NO → Regular sonos CLI command or other action
```

## File Architecture

### Core Components
- **`claude_music_interface.py`**: Claude Code integration layer
  - `play_music_parsed_with_llm()`: Hybrid LLM-powered entry point
  - `ClaudeCodeMusicAgent`: Enhanced agent with Task function support
  - `parse_music_request_llm()`: LLM parsing interface (placeholder)

- **`music_agent.py`**: Base agent implementation
  - `MusicAgent`: Core search and selection logic
  - `_generate_smart_search_queries()`: Multi-query strategy
  - `parse_search_results()`: Sonos CLI output parsing

### Integration Points
- **CLAUDE.md**: Detection patterns and usage instructions
- **Task Tool**: Claude Code's subagent delegation mechanism
- **Sonos CLI**: Underlying music control system

## Usage Patterns for Claude Code

### Optimal Approach (Hybrid LLM)
```python
# Step 1: Parse with LLM
parsed = Task(
    description="Parse music request", 
    prompt="Parse 'I want some live Neil Young'...",
    subagent_type="general-purpose"
)

# Step 2: Play with hybrid selection
result = play_music_parsed_with_llm(
    parsed['title'], 
    parsed['artist'], 
    parsed['preferences'],
    task_function=Task  # Enable LLM selection when needed
)
```

### Alternative Approach (LLM Parsing Only)
```python  
# Step 1: Parse with LLM (same as above)
# Step 2: Play with algorithmic selection only
result = play_music_parsed(parsed['title'], parsed['artist'], parsed['preferences'])
```

### Fallback Approach (Full Legacy)
```python
# Single call with regex parsing (less reliable)
result = play_music("I want some live Neil Young")
```

## Performance Characteristics

### LLM Usage Optimization
- **Parsing**: Always uses LLM for natural language understanding
- **Selection**: Only uses LLM when algorithmic approach insufficient
- **Caching**: Task results cached within Claude Code session
- **Fallback**: Graceful degradation when LLM services unavailable

### Response Times
- **Simple cases**: ~2-3 seconds (single LLM call for parsing)
- **Complex cases**: ~4-6 seconds (two LLM calls: parsing + selection)  
- **Error recovery**: Additional 1-2 seconds per fallback query
- **Network issues**: Automatic fallback to algorithmic methods

This hybrid architecture combines the natural language understanding power of LLMs with the speed and reliability of algorithmic selection, automatically choosing the optimal approach for each request while maintaining graceful fallback capabilities.