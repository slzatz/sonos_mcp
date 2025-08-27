"""
Simple interface for Claude Code to handle music requests using the intelligent agent.

This module provides a clean, easy-to-use interface that Claude Code can invoke
to handle natural language music requests without needing to understand the
internal workings of the agent.
"""

from music_agent import MusicAgent
from typing import Optional, Dict, Any
import json


class ClaudeCodeMusicAgent(MusicAgent):
    """
    Enhanced MusicAgent that integrates with Claude Code's Task subagent capabilities.
    
    This subclass overrides methods to use standardized prompts instead of ad-hoc prompts,
    and integrates with Claude Code's Task tool for LLM-powered result selection.
    """
    
    def __init__(self, task_function=None):
        super().__init__()
        self.task_function = task_function
    
    def _call_selection_subagent(self, prompt: str) -> str:
        """
        Call Claude Code Task subagent for intelligent music selection.
        
        This method uses the Task function when available (provided during initialization)
        or falls back to programmatic selection.
        """
        if self.task_function:
            try:
                print(f"🤖 Using LLM selection for complex music matching...")
                result = self.task_function(
                    description="Select best music track",
                    prompt=prompt,
                    subagent_type="general-purpose"
                )
                return result if result else ""
            except Exception as e:
                print(f"LLM selection failed ({e}), falling back to programmatic selection")
                return ""
        else:
            # Task function not available, use programmatic fallback
            return ""
    
    def _llm_select_best_match(self, results, target_title: str, 
                              target_artist: str = None, preferences = None):
        """
        Use standardized prompt template for LLM-powered result selection.
        
        This overrides the base class method to use consistent prompt templates
        instead of ad-hoc prompt generation.
        """
        try:
            from music_parsing_prompts import format_result_selection_prompt
            
            # Generate standardized prompt using template
            prompt = format_result_selection_prompt(
                title=target_title,
                artist=target_artist, 
                preferences=preferences or {},
                results=results
            )
            
            if not prompt:
                return None
                
            # Call Task subagent for selection
            result = self._call_selection_subagent(prompt)
            
            # Parse result to get position number
            if result and result.strip():
                try:
                    position = int(result.strip().split()[0])  # Get first number
                    # Validate position is in results
                    if any(r['position'] == position for r in results):
                        return position
                except (ValueError, IndexError):
                    pass
            
        except ImportError:
            print("music_parsing_prompts not found, falling back to base implementation")
            return super()._llm_select_best_match(results, target_title, target_artist, preferences)
        except Exception as e:
            print(f"Standardized LLM selection error: {e}")
        
        return None


def parse_music_request_llm(request: str, task_function=None) -> Dict[str, Any]:
    """
    Parse a natural language music request using LLM capabilities with standardized prompts.
    
    This function uses standardized prompt templates to ensure consistent parsing behavior
    instead of ad-hoc prompts written during Claude Code conversations.
    
    Args:
        request: Natural language music request
        task_function: Claude Code's Task function (required for LLM parsing)
        
    Returns:
        Dict with parsed components: {'title': str, 'artist': str|None, 'preferences': dict}
        
    Example:
        # Called from Claude Code with Task function:
        parsed = parse_music_request_llm("Neil Young's Harvest", task_function=Task)
        # Returns: {'title': 'harvest', 'artist': 'neil young', 'preferences': {}}
    """
    if not task_function:
        return {
            'error': 'Task function required - this must be called from Claude Code session',
            'original_request': request,
            'message': 'Pass task_function=Task when calling from Claude Code'
        }
    
    try:
        from music_parsing_prompts import STANDARD_MUSIC_PARSING_PROMPT
        
        # Format the standardized prompt with the actual request
        prompt = STANDARD_MUSIC_PARSING_PROMPT.format(request=request)
        
        # Call Claude Code's Task tool with standardized prompt
        result = task_function(
            description="Parse music request",
            prompt=prompt,
            subagent_type="general-purpose"
        )
        
        # The LLM should return JSON, but handle string responses too
        if isinstance(result, str):
            import json
            try:
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError:
                # If not valid JSON, return error with raw result
                return {
                    'error': 'LLM returned non-JSON response',
                    'raw_response': result,
                    'original_request': request
                }
        else:
            # Result is already a dict/object
            return result
            
    except ImportError:
        return {
            'error': 'music_parsing_prompts module not found',
            'original_request': request
        }
    except Exception as e:
        return {
            'error': f'Parsing failed: {str(e)}',
            'original_request': request
        }


def play_music_parsed_with_llm(title: str, artist: str = None, preferences: Dict[str, Any] = None, 
                              verbose: bool = False, task_function=None) -> str:
    """
    Play music using pre-parsed components with LLM-powered result selection.
    
    This version accepts a task_function parameter that allows Claude Code to pass
    the Task function for LLM-powered result selection when needed.
    
    Args:
        title: Song title (required)
        artist: Artist name (optional)
        preferences: Dict with preference keys (optional)
        verbose: Whether to return detailed information
        task_function: Function to call Task subagent (provided by Claude Code)
        
    Returns:
        Human-readable message about the result
    """
    # Use Claude Code-enhanced agent with LLM selection capability
    agent = ClaudeCodeMusicAgent(task_function=task_function)
    result = agent.handle_parsed_music_request(title, artist, preferences or {})
    
    if result['success']:
        if verbose:
            details = result.get('details', {})
            message = result['message']
            if 'search_query_used' in details:
                message += f"\n(Used search query: '{details['search_query_used']}')"
            if 'total_results' in details:
                message += f"\n(Found {details['total_results']} total results)"
            if preferences:
                prefs_str = ", ".join(f"{k.replace('prefer_', '')}" for k, v in preferences.items() if v)
                if prefs_str:
                    message += f"\n(Applied preferences: {prefs_str})"
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


def play_music_parsed(title: str, artist: str = None, preferences: Dict[str, Any] = None, verbose: bool = False) -> str:
    """
    Play music using pre-parsed components from LLM analysis.
    
    This is the recommended approach for Claude Code integration - use LLM capabilities
    to parse the natural language request, then call this function with structured data.
    
    Args:
        title: Song title (required)
        artist: Artist name (optional)
        preferences: Dict with keys like 'prefer_live', 'prefer_acoustic', 'prefer_studio' (optional)
        verbose: Whether to return detailed information
        
    Returns:
        Human-readable message about the result
        
    Example:
        # After LLM parsing of "play an acoustic version of Neil Young's Harvest":
        play_music_parsed("harvest", "neil young", {"prefer_acoustic": True})
    """
    # Use Claude Code-enhanced agent for better LLM integration
    agent = ClaudeCodeMusicAgent()
    result = agent.handle_parsed_music_request(title, artist, preferences or {})
    
    if result['success']:
        if verbose:
            details = result.get('details', {})
            message = result['message']
            if 'search_query_used' in details:
                message += f"\n(Used search query: '{details['search_query_used']}')"
            if 'total_results' in details:
                message += f"\n(Found {details['total_results']} total results)"
            if preferences:
                prefs_str = ", ".join(f"{k.replace('prefer_', '')}" for k, v in preferences.items() if v)
                if prefs_str:
                    message += f"\n(Applied preferences: {prefs_str})"
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


def play_music(request: str, verbose: bool = False) -> str:
    """
    Handle a natural language music request and play the track.
    
    LEGACY FUNCTION: This function uses basic regex parsing and is less reliable.
    For Claude Code integration, the recommended approach is:
    1. Use LLM capabilities to parse the request
    2. Call play_music_parsed() with the structured data
    
    This function is kept for backward compatibility and fallback scenarios.
    
    Args:
        request: Natural language music request (e.g., "ani difranco's fixing her hair")
        verbose: Whether to return detailed information about the process
        
    Returns:
        Human-readable message about the result
    """
    # Use legacy agent for backward compatibility (no LLM selection)
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


def search_music_parsed(title: str, artist: str = None, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Search for music using pre-parsed components from LLM analysis.
    
    Args:
        title: Song title (required)
        artist: Artist name (optional)  
        preferences: Dict with preference keys (optional)
        
    Returns:
        Dictionary with search results and analysis
    """
    # Use Claude Code-enhanced agent for better LLM integration
    agent = ClaudeCodeMusicAgent()
    
    try:
        # Generate search queries
        queries = agent._generate_smart_search_queries(title, artist, preferences or {})
        
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
            'preferences': preferences or {},
            'queries_generated': queries,
            'successful_queries': successful_queries,
            'results': all_results[:10],  # Top 10 results
            'total_results': len(all_results)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'title': title,
            'artist': artist
        }


def search_music(request: str) -> Dict[str, Any]:
    """
    Search for music without playing it, returning detailed results.
    
    LEGACY FUNCTION: Uses basic regex parsing. For Claude Code, use search_music_parsed() instead.
    
    Args:
        request: Natural language music request
        
    Returns:
        Dictionary with search results and analysis
    """
    # Use legacy agent for backward compatibility (no LLM selection)
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
    agent = ClaudeCodeMusicAgent()
    result = agent.get_current_track_info()
    
    if result['success']:
        return result['output']
    else:
        return f"❌ Could not get current track info: {result.get('error', 'Unknown error')}"


# Convenience functions for common operations
def pause_music() -> str:
    """Pause music playback."""
    agent = ClaudeCodeMusicAgent()
    result = agent.execute_sonos_command(['sonos', 'pause'])
    return "⏸️ Paused" if result['success'] else f"❌ Failed to pause: {result.get('error')}"


def resume_music() -> str:
    """Resume music playback."""
    agent = ClaudeCodeMusicAgent()
    result = agent.execute_sonos_command(['sonos', 'resume'])
    return "▶️ Resumed" if result['success'] else f"❌ Failed to resume: {result.get('error')}"


# Example usage demonstrations
if __name__ == "__main__":
    print("Testing Claude Code Music Interface")
    print("=" * 50)
    print("🚀 NEW LLM-POWERED APPROACH (Recommended for Claude Code):")
    print("=" * 50)
    
    # Example of the new LLM-powered approach
    # In Claude Code, you would first parse the natural language using Task subagent:
    # parsed = Task("Parse music request", prompt="...", subagent_type="general-purpose")
    # Then call: play_music_parsed(parsed['title'], parsed['artist'], parsed['preferences'])
    
    test_parsed_examples = [
        ("fixing her hair", "ani difranco", {}),
        ("harvest", "neil young", {}),
        ("harvest", "neil young", {"prefer_live": True}),
        ("harvest", "neil young", {"prefer_acoustic": True})
    ]
    
    for title, artist, prefs in test_parsed_examples:
        print(f"\n🎵 Testing parsed: title='{title}', artist='{artist}', prefs={prefs}")
        result = play_music_parsed(title, artist, prefs, verbose=True)
        print(f"Result: {result}")
    
    print("\n" + "=" * 50)
    print("📜 LEGACY APPROACH (Regex-based, less reliable):")
    print("=" * 50)
    
    # Test the legacy play_music function
    test_requests = [
        "ani difranco's fixing her hair",
        "play harvest by neil young", 
        "I want to hear a live version of harvest"
    ]
    
    for request in test_requests:
        print(f"\n🎵 Testing legacy: '{request}'")
        result = play_music(request, verbose=True)
        print(f"Result: {result}")
    
    print("\n📍 Current track:")
    print(get_current_track())