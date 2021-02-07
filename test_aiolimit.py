import pytest, aiolimit, asyncio, itertools, collections
from unittest.mock import patch

@pytest.mark.parametrize('w,n,rr,lr,re,le,rtl,ltr', itertools.product(*[
    [1.],
    [1, 2, 10],
    [1e-9, 1e-6, 1e-3],
    [1e-9, 1e-6, 1e-3],
    [10, 100, 250],
    [10, 100, 250],
    [0, 1e-3, 1],
    [0, 1e-3, 1]
]))
@pytest.mark.asyncio
async def test_basic(w, n, rr, lr, re, le, rtl, ltr):
    """
    Basic test ignoring most parameters for now -- checks that the implementation of
    Limiter() cannot dispatch events in such a way that a remote API (us) could
    record more than `n` events per sliding window of `w` seconds.
    """
    # Mock
    # ====
    _cur_time = 0
    def time():
        return _cur_time
    async def sleep(x):
        nonlocal _cur_time
        if x>0:
            _cur_time += x
    d = collections.deque()
    async def event():
        await sleep(ltr)
        while d and d[0] < time()-w:
            d.popleft()
        d.append(time())
        await sleep(rtl)
        if len(d) > n:
            raise Exception("Overloaded Window")

    # Impl
    # ====
    loop = asyncio.get_running_loop()
    with \
            patch.object(loop, 'time', wraps=time) as mock_time, \
            patch.object(asyncio, 'sleep', wraps=sleep) as mock_sleep:
        limiter = aiolimit.Limiter(w, n, rr, lr, re, le, rtl, ltr)
        for _ in range(20):
            await limiter.run(event())
