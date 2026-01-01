# Services Directory

This directory contains the business logic services for The Arbiter.

## Planned Services

| Service | Description |
|---------|-------------|
| `embedding.py` | OpenAI embedding generation |
| `retrieval.py` | RAG retrieval with pgvector |
| `qa.py` | Question answering with citation |
| `pdf.py` | PDF parsing with PyMuPDF |
| `cache.py` | Query caching with semantic matching |
| `verification.py` | Citation verification |

## Service Pattern

Each service follows this pattern:

```python
# services/example.py

from app.config import get_settings

class ExampleService:
    def __init__(self):
        self.settings = get_settings()
    
    async def do_something(self, input: str) -> str:
        # Implementation
        pass

# Singleton instance
_service: ExampleService | None = None

def get_example_service() -> ExampleService:
    global _service
    if _service is None:
        _service = ExampleService()
    return _service
```

## Usage in Routes

```python
from fastapi import Depends
from app.services.example import ExampleService, get_example_service

@router.post("/example")
async def example_endpoint(
    service: ExampleService = Depends(get_example_service)
):
    result = await service.do_something("input")
    return {"result": result}
```
