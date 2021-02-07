# aiolimit

A client-side rate limiter to avoid remote penalties

## Installation

```bash
python -m pip install -e git+https://github.com/hmusgrave/aiolimit.git#egg=aiolimit
```

## Examples
```python
import asyncio, aiolimit

async def some_remote_call():
    return 1

rps = 1500
buffer = 100

async def main():
    limiter = aiolimit.Limiter(buffer/rps, buffer)
    for _ in range(1000):
        result = await limiter.run(some_remote_call())

print(asyncio.run(main()))
```

## Design Choices
- Issuing a sequence of calls causing the remote system to invoke rate limiting
  is unacceptable. In practice, we are at the mercy of machine designers, so we
  provide extremely conservative estimates for hardware capabilities rather
  than requiring an excessive amount of specialized knowledge at the outset.
- The authors' envisioned use case is calling a remote http API, where a few
  dozen thousand requests per second per core is more than acceptable. Higher
  throughput applications should seek other solutions.
- Relativity is completely ignored
