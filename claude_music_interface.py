"""
Simple interface for Claude Code to handle music requests using the intelligent agent.

This module provides a clean, easy-to-use interface that Claude Code can invoke
to handle natural language music requests without needing to understand the
internal workings of the agent.
"""

from music_agent import MusicAgent
from typing import Optional, Dict, Any


def play_music(request: str, verbose: bool = False) -> str:
    """
    Handle a natural language music request and play the track.
    
    This is the main function Claude Code should use for music requests.
    
    Args:
        request: Natural language music request (e.g., "ani difranco's fixing her hair")
        verbose: Whether to return detailed information about the process
        
    Returns:
        Human-readable message about the result
    """
    agent = MusicAgent()
    result = agent.handle_music_request(request)
    
    if result['success']:
        if verbose:
            details = result.get('details', {})
            message = result['message']
            if 'search_query_used' in details:
                message += f"\n(Used search query: '{details['search_query_used']}')"
            if 'total_results' in details:
                message += f"\n(Found {details['total_results']} total results)"
            return message
        else:
            return result['message']
    else:
        if verbose:
            error_details = result.get('details', {})
            message = result['message']
            if 'queries_tried' in error_details:
                message += f"\n(Tried {len(error_details['queries_tried'])} different search queries)"
            return message
        else:
            return f"❌ {result['message']}"


def search_music(request: str) -> Dict[str, Any]:
    """
    Search for music without playing it, returning detailed results.
    
    Args:
        request: Natural language music request
        
    Returns:
        Dictionary with search results and analysis
    """
    agent = MusicAgent()
    
    # Parse the request to understand what they want
    try:
        parsed = agent._parse_music_request(request)
        title = parsed['title']
        artist = parsed['artist']
        preferences = parsed['preferences']
        
        # Generate search queries
        queries = agent._generate_smart_search_queries(title, artist, preferences)
        
        # Try searches and collect results
        all_results = []
        successful_queries = []
        
        for query in queries[:3]:  # Try first 3 queries
            try:
                search_result = agent.execute_sonos_command(['sonos', 'searchtrack'] + query.split())
                if search_result['success'] and search_result['output'].strip():
                    results = agent.parse_search_results(search_result['output'])
                    if results:
                        all_results.extend(results)
                        successful_queries.append(query)
                        break  # Stop after first successful search
            except:
                continue
        
        return {
            'parsed_title': title,
            'parsed_artist': artist,
            'preferences': preferences,
            'queries_generated': queries,
            'successful_queries': successful_queries,
            'results': all_results[:10],  # Top 10 results
            'total_results': len(all_results)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'request': request
        }


def get_current_track() -> str:
    """Get information about the currently playing track."""
    agent = MusicAgent()
    result = agent.get_current_track_info()
    
    if result['success']:
        return result['output']
    else:
        return f"❌ Could not get current track info: {result.get('error', 'Unknown error')}"


# Convenience functions for common operations
def pause_music() -> str:
    """Pause music playback."""
    agent = MusicAgent()
    result = agent.execute_sonos_command(['sonos', 'pause'])
    return "⏸️ Paused" if result['success'] else f"❌ Failed to pause: {result.get('error')}"


def resume_music() -> str:
    """Resume music playback."""
    agent = MusicAgent()
    result = agent.execute_sonos_command(['sonos', 'resume'])
    return "▶️ Resumed" if result['success'] else f"❌ Failed to resume: {result.get('error')}"


# Example usage demonstrations
if __name__ == "__main__":
    print("Testing Claude Code Music Interface")
    print("=" * 50)
    
    # Test the main play_music function
    test_requests = [
        "ani difranco's fixing her hair",
        "play harvest by neil young", 
        "I want to hear a live version of harvest"
    ]
    
    for request in test_requests:
        print(f"\n🎵 Testing: '{request}'")
        result = play_music(request, verbose=True)
        print(f"Result: {result}")
    
    print("\n📍 Current track:")
    print(get_current_track())