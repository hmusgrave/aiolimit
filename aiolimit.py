import asyncio, time

class Limiter:
    def __init__(self, w, n, rr=.016,
            lr=time.get_clock_info('monotonic').resolution, re=250, le=250,
            rtl=0, ltr=0):
        """
        Locally rate-limits so that remote limits cannot be exceeded

        Parameters
        ----------
        w : float (seconds). Range (0, infinity)
            remote time window which should never read more than `n` events
        n : int. Range [1, infinity)
            remote API should never read more than `n` events in a window `w`
        rr : float (seconds). Default 0.16. Range [0, infinity)
            remote clock resolution (in remote time) -- typically 15.6ms for
            Windows and <=1ns for Linux; if unsure, err on the side of larger
            values
        lr : float (seconds). Default time.get_clock_info('monotonic').resolution. Range [0, infinity)
            local clock resolution (in local time) -- typically 15.6ms for
            Windows and <=1ns for Linux; if unsure, err on the side of larger
            values
        re : float (ppm). Default 250. Range [0, 1_000_000)
            remote clock error -- typically 100ppm on consumer-grade machines,
            below 250ppm on all but the cheapest/worst microcontrollers; 100ppm
            is an error of 8.64 seconds per day; if unsure, err on the side of
            larger values
        le : float (ppm). Default 250. Range [0, 1_000_000)
            local clock error -- typically 100ppm on consumer-grade machines,
            below 250ppm on all but the cheapest/worst microcontrollers; 100ppm
            is an error of 8.64 seconds per day; if unsure, err on the side of
            larger values
        rtl : float (seconds). Default 0. Range [0, infinity)
            minimum true-time latency from the remote event time measurement
            to the local event acknowledgement time measurement; if unsure, err
            on the side of smaller values
        ltr : float (seconds). Default 0. Range [0, infinity)
            minimum true-time latency from the local time measurement before
            event dispatch to the remote event time measurement; if unsure, err
            on the side of smaller values

        Examples
        --------
        >>> import aiolimit, asyncio
        >>> limiter = aiolimit.Limiter(1, 10)  # max 10 calls in 1 second
        >>> async def main():
        ...     loop = asyncio.get_running_loop()
        ...     start = loop.time()
        ...     for _ in range(50):
        ...         await limiter.run(asyncio.sleep(0)) 
        ...     return 50 / (loop.time() - start)
        ...
        >>> # note that average requests per second can be greater than 10 even
        >>> # though every 1s window had at most 10 requests
        >>> print(asyncio.run(main()))
        12.479
        """

        # Magic -- read design doc
        # 
        # In short, if the local monotonic clock reads `ts+gap` for some
        # event who had its local time recorded as `ts` then that event
        # cannot cohabitate any w-width time window with a newly dispatched
        # event as far as the remote monotonic clock is concerned
        self.gap = ((w+rr)/(1-1e-6*re)-rtl-ltr)*(1+1e-6*le)+lr

        self.waiting = asyncio.Queue()
        t = self.time() - self.gap
        for _ in range(n):
            self.waiting.put_nowait(t)

    def time(self):
        return asyncio.get_running_loop().time()

    async def run(self, coro):
        # Assumed that self.time(), await q.get(), and q.put_nowait() never
        # fail
        try:
            # wait till `(await self.waiting.get()) + self.gap`
            await asyncio.sleep((await self.waiting.get()) + self.gap - self.time())
            return await coro
        finally:
            self.waiting.put_nowait(self.time())
