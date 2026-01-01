"""
Server-Sent Events (SSE) utilities for real-time streaming.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from starlette.responses import StreamingResponse


logger = logging.getLogger(__name__)


def format_sse_event(
    data: dict[str, Any],
    event: str | None = None,
    id: str | None = None,
) -> str:
    """
    Format data as an SSE event.
    
    Args:
        data: JSON-serializable data payload
        event: Optional event type name
        id: Optional event ID
        
    Returns:
        Formatted SSE string
    """
    lines = []
    
    if id:
        lines.append(f"id: {id}")
    if event:
        lines.append(f"event: {event}")
    
    # Convert data to JSON string
    json_data = json.dumps(data, ensure_ascii=False)
    lines.append(f"data: {json_data}")
    
    # SSE events end with double newline
    return "\n".join(lines) + "\n\n"


def format_sse_comment(comment: str) -> str:
    """Format a comment line (for keep-alive)."""
    return f": {comment}\n\n"


class SSEResponse(StreamingResponse):
    """
    StreamingResponse configured for Server-Sent Events.
    """
    
    def __init__(
        self,
        content: AsyncGenerator[str, None],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        sse_headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
        if headers:
            sse_headers.update(headers)
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=sse_headers,
            media_type="text/event-stream",
        )


async def sse_generator(
    poll_func,
    poll_interval: float = 0.5,
    timeout: float = 300,
    terminal_states: set[str] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Generic SSE generator that polls a function and streams updates.
    
    Args:
        poll_func: Async function that returns (data_dict, is_done)
        poll_interval: Seconds between polls
        timeout: Maximum stream duration in seconds
        terminal_states: Set of states that end the stream
        
    Yields:
        SSE formatted event strings
    """
    if terminal_states is None:
        terminal_states = {"ready", "failed", "error"}
    
    start_time = asyncio.get_event_loop().time()
    last_state = None
    event_id = 0
    
    try:
        # Send initial keep-alive
        yield format_sse_comment("stream connected")
        
        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                yield format_sse_event(
                    {"state": "timeout", "pct": 0, "msg": "Stream timed out"},
                    event="error",
                    id=str(event_id)
                )
                break
            
            # Poll for update
            try:
                data = await poll_func()
            except Exception as e:
                logger.error(f"Poll error: {e}")
                yield format_sse_event(
                    {"state": "error", "pct": 0, "msg": str(e)},
                    event="error",
                    id=str(event_id)
                )
                break
            
            # Only send if state changed or progress updated
            current_state = (data.get("state"), data.get("pct"))
            if current_state != last_state:
                event_id += 1
                last_state = current_state
                
                # Determine event type
                state = data.get("state", "unknown")
                if state in terminal_states:
                    event_type = "complete" if state == "ready" else "error"
                else:
                    event_type = "progress"
                
                yield format_sse_event(data, event=event_type, id=str(event_id))
                
                # End stream on terminal state
                if state in terminal_states:
                    break
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
            
            # Send keep-alive comment every 15 seconds
            if int(elapsed) % 15 == 0 and int(elapsed) > 0:
                yield format_sse_comment("keep-alive")
                
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled (client disconnected)")
        raise
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield format_sse_event(
            {"state": "error", "pct": 0, "msg": f"Stream error: {e}"},
            event="error"
        )
