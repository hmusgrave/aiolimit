# aiolimit

An outbound request rate limiter

## Purpose

When limiting outbound requests so as to not trigger penalties in a remote system, the _remote_ clock's opinion is the only one which matters. This library allows you to dispatch your requests so that from the perspective of the remote system, regardless of implementation, you cannot have exceeded the remote rate quota.

## Status
Contributions welcome (from 22 Feb 2021 through roughly 31 March 2021 no changes will be made, feel free to fork).

Test suite catches:
- [x] Some obvious misimplementations
- [ ] Bugs related to anything fine-grained like clock resolution

Overhead suitable for:
- [x] Typical http requests
- [x] Typical rpc requests
- [ ] High-performance networking
- [ ] Low-level socket handling (depends)

Limiter types:
- [x] Sliding window (at most `n` requests in any window of `w` seconds)
- [ ] Leaky bucket (using the sliding window limiter against a remote leaky bucket algorithm results in marginally lower average throughput than could otherwise be achieved)
- [ ] Dynamic parameter discovery (for any kind of limiter)

Model incorporates:
- [x] Clock drift
- [x] Clock resolution
- [x] Local vs Remote clocks
- [x] Request latency
- [ ] Relativity

Safe for:
- [x] Single Thread
- [ ] Multiple Processes

Works on:
- [x] Asyncio
- [ ] Multiple event loops

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
max_items_in_window = 100
window_width_seconds = max_items_in_window / rps

async def main():
    limiter = aiolimit.Limiter(window_width_seconds, max_items_in_window)
    for _ in range(1000):
        result = await limiter.run(some_remote_call())

print(asyncio.run(main()))
```
