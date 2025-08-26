"""
Helper functions for Claude Code integration with Sonos CLI
"""

import re
import subprocess
from typing import List, Tuple, Optional, Dict, Any
from difflib import SequenceMatcher


def parse_search_results(search_output: str) -> List[Tuple[int, str, str, str]]:
    """
    Parse sonos searchtrack output into structured data.
    
    Args:
        search_output: Raw output from sonos searchtrack command
        
    Returns:
        List of tuples: (position, title, artist, album)
    """
    results = []
    lines = search_output.strip().split('\n')
    
    for line in lines:
        # Match new pattern: "number. Title-Artist-Album"
        match = re.match(r'^(\d+)\.\s+(.+?)-(.+?)-(.+)$', line.strip())
        if match:
            position = int(match.group(1))
            title = match.group(2).strip()
            artist = match.group(3).strip()
            album = match.group(4).strip()
            results.append((position, title, artist, album))
        else:
            # Fallback for old format without album
            old_match = re.match(r'^(\d+)\.\s+(.+?)-(.+)$', line.strip())
            if old_match:
                position = int(old_match.group(1))
                title = old_match.group(2).strip()
                artist = old_match.group(3).strip()
                results.append((position, title, artist, 'Unknown Album'))
    
    return results


def clean_title(title: str) -> str:
    """
    Clean track title by removing common variations and annotations.
    
    Args:
        title: Raw track title
        
    Returns:
        Cleaned title
    """
    # Remove remaster annotations
    title = re.sub(r'\s*\(\d{4}\s+Remaster\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(Remaster\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(Remastered\)', '', title, flags=re.IGNORECASE)
    
    # Remove live annotations
    title = re.sub(r'\s*\(Live.*?\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*- Live', '', title, flags=re.IGNORECASE)
    
    # Remove explicit tags
    title = re.sub(r'\s*\[Explicit\]', '', title, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title


def similarity_score(str1: str, str2: str) -> float:
    """
    Calculate similarity score between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def find_best_match(
    search_results: List[Tuple[int, str, str, str]], 
    target_title: str, 
    target_artist: str = None,
    preferences: Dict[str, Any] = None
) -> Optional[int]:
    """
    Find the best matching track from search results.
    
    Args:
        search_results: List of (position, title, artist) tuples
        target_title: Title to search for
        target_artist: Optional artist to help with disambiguation
        
    Returns:
        Position of best match, or None if no good match found
    """
    if not search_results:
        return None
    
    preferences = preferences or {}
    prefer_live = preferences.get('prefer_live', False)
    
    target_title_clean = clean_title(target_title).lower()
    
    # Score each result
    scored_results = []
    
    for position, title, artist, album in search_results:
        title_clean = clean_title(title).lower()
        artist_clean = artist.lower()
        album_clean = album.lower()
        
        # Calculate title similarity
        title_score = similarity_score(title_clean, target_title_clean)
        
        # Bonus for exact match
        if title_clean == target_title_clean:
            title_score = 1.0
        
        # Artist matching bonus
        artist_score = 0.0
        if target_artist:
            target_artist_clean = target_artist.lower()
            artist_score = similarity_score(artist_clean, target_artist_clean)
            
            # Bonus for artist name being contained in result
            if target_artist_clean in artist_clean or artist_clean in target_artist_clean:
                artist_score = max(artist_score, 0.8)
        
        # Handle version preferences - check both title and album
        version_modifier = 0.0
        is_live = bool(re.search(r'live', title, re.IGNORECASE)) or bool(re.search(r'live', album, re.IGNORECASE))
        is_remaster = bool(re.search(r'remaster', title, re.IGNORECASE))
        
        # Additional live detection patterns in album names
        live_album_patterns = [
            r'live from',
            r'live at',
            r'concert',
            r'acoustic',
            r'unplugged',
            r'artists den'
        ]
        if any(re.search(pattern, album_clean) for pattern in live_album_patterns):
            is_live = True
        
        if prefer_live:
            # Boost live versions when specifically requested
            if is_live:
                version_modifier = 0.3  # Significant boost for live versions
            elif is_remaster and title_score >= 0.9:
                version_modifier = -0.1  # Small penalty for remasters when we want live
        else:
            # Original behavior - prefer studio versions
            if title_score >= 0.9:  # High title similarity
                if is_remaster or is_live:
                    version_modifier = -0.1
        
        # Combined score
        if target_artist:
            combined_score = (title_score * 0.7) + (artist_score * 0.3) + version_modifier
        else:
            combined_score = title_score + version_modifier
        
        scored_results.append((position, combined_score, title, artist, album))
    
    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    # Return position of best match if score is good enough
    best_position, best_score, best_title, best_artist, best_album = scored_results[0]
    
    # Only return if we have a reasonable match
    if best_score >= 0.6:
        return best_position
    
    return None


def extract_music_request(user_input: str) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    Extract song title, artist, and preferences from natural language request.
    
    Args:
        user_input: Natural language music request
        
    Returns:
        Tuple of (title, artist, preferences) where artist may be None
    """
    user_input_lower = user_input.strip().lower()
    
    # Detect preferences
    preferences = {}
    
    # Detect live version requests
    live_patterns = [
        r'live version',
        r'live recording',
        r'live performance',
        r'concert version',
        r'\blive\b(?!.*studio)'
    ]
    
    prefer_live = any(re.search(pattern, user_input_lower) for pattern in live_patterns)
    if prefer_live:
        preferences['prefer_live'] = True
    
    # Clean the input for parsing (remove live-related modifiers)
    clean_input = user_input_lower
    clean_input = re.sub(r'\b(live version of|live recording of|live performance of|concert version of)\s*', '', clean_input)
    clean_input = re.sub(r'\ba live version of\s*', '', clean_input)
    clean_input = re.sub(r'\blive\b(?!.*studio)\s*', '', clean_input)
    clean_input = re.sub(r'\s+', ' ', clean_input).strip()
    
    # Common patterns
    patterns = [
        r'play\s+(.+?)\s+by\s+(.+)',  # "play harvest by neil young"
        r'(.+?)\s+by\s+(.+)',         # "harvest by neil young"  
        r'play\s+(.+)',               # "play harvest moon" (no artist)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, clean_input, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return match.group(1).strip(), match.group(2).strip(), preferences
            else:
                return match.group(1).strip(), None, preferences
    
    # Fallback: treat entire input as title
    return clean_input, None, preferences


def execute_smart_search(title: str, artist: str = None, preferences: Dict[str, Any] = None) -> Optional[int]:
    """
    Execute intelligent multi-search strategy to find the best track match.
    
    Args:
        title: Track title to search for
        artist: Optional artist name
        preferences: Search preferences (e.g., prefer_live)
        
    Returns:
        Position of best match, or None if no good match found
    """
    preferences = preferences or {}
    prefer_live = preferences.get('prefer_live', False)
    
    # Generate search queries in order of preference
    search_queries = []
    
    if artist:
        base_query = f"{title} by {artist}"
        search_queries.append(base_query)
        
        if prefer_live:
            # Try live-specific searches first when requesting live versions
            search_queries.insert(0, f"live {title} {artist}")
            search_queries.insert(1, f"{title} live {artist}")
            search_queries.insert(2, f"{artist} {title} live")
    else:
        base_query = title
        search_queries.append(base_query)
        
        if prefer_live:
            search_queries.insert(0, f"live {title}")
            search_queries.insert(1, f"{title} live")
    
    best_match = None
    best_score = 0
    best_results = None
    
    # Try each search query
    for query in search_queries:
        try:
            # Execute sonos search
            result = subprocess.run(
                ['sonos', 'searchtrack'] + query.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse results
                results = parse_search_results(result.stdout)
                
                if results:
                    # Find best match in these results
                    position = find_best_match(results, title, artist, preferences)
                    
                    if position:
                        # Calculate a rough score for this match
                        for pos, track_title, track_artist, track_album in results:
                            if pos == position:
                                # Score based on title similarity and preference matching
                                title_sim = similarity_score(clean_title(track_title), title)
                                is_live = (bool(re.search(r'live', track_title, re.IGNORECASE)) or 
                                          bool(re.search(r'live', track_album, re.IGNORECASE)))
                                
                                match_score = title_sim
                                if prefer_live and is_live:
                                    match_score += 0.3
                                elif not prefer_live and not is_live:
                                    match_score += 0.1
                                
                                if match_score > best_score:
                                    best_match = position
                                    best_score = match_score
                                    best_results = results
                                break
                    
                    # If we found a great match (especially for live requests), stop searching
                    if best_score > 0.9 or (prefer_live and best_score > 0.7):
                        break
                        
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            continue
    
    return best_match


def format_track_info(title: str, artist: str) -> str:
    """
    Format track information for display.
    
    Args:
        title: Track title
        artist: Track artist
        
    Returns:
        Formatted string
    """
    return f"{title} by {artist}"


def handle_music_request(user_input: str) -> Optional[int]:
    """
    Complete workflow to handle a music request from natural language input.
    
    Args:
        user_input: Natural language music request
        
    Returns:
        Position to play, or None if no good match found
    """
    # Extract request components
    title, artist, preferences = extract_music_request(user_input)
    
    # Execute smart search
    position = execute_smart_search(title, artist, preferences)
    
    return position