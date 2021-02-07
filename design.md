# Overview
A remote system is rate-limiting us and adding additional penalties when
rate-limiting is triggered. We wish to throttle our clients as little as
possible so that the remote never sees rate-limitable throughput.

# Problem Definition
In particular, we are attempting to throttle local requests in such a way that
no remote measurement could detect more than `n` events in any window of `w`
seconds. We are additionally assuming:
- Some "true" time exists -- we don't care about relativity.
- The remote clock is measured in pulses with a given resolution `rr` -- i.e.,
  any time measurement will resemble a step function with step widths of `rr`.
- The local clock is measured in pulses with a given resolution `lr`.
- There exists a remote clock error ppm `re` with the property that when an
  interval of width `t` elapses between the start of one remote clock pulse
  and the start of some other remote clock pulse then the measured width `mw`
  of that interval will satisfy `(1 - 1e-6*re) * t <= mw <= (1 + 1e-6*re)`.
- There exists a similar local clock error ppm `le`.
- There exists some minimum latency `ltr` from the local time measurement immediately
  before an event is dispatched to the remote time measurement immediately
  after an event is received.
- There exists some minimum latency `rtl` from the remote time measurement
  immediately after an event is received to the local time measurement
  immediately after we locally receive acknowledgement from the remote that our
  event has been received.

# Assumptions
Our key operating assumption is that at no point have we dispatched an event
which could potentially incurred remote rate limiting. This implies that in any
window of width `w` there are at most `n` events which could possibly be
recorded, and it further implies that in order to send just one more event we
simply have to wait enough time that the oldest of those events could not
possibly be recorded in the last `w` seconds according to the remote clock (or
if there were fewer than `n` such events then we can dispatch another
immediately).

# Rough Derivation
1. In particular, let `now` denote the current moment in true time. If we
   dispatched an event immediately it could arrive as soon as `now+ltr`. The
   remote clock would record that event some portion of the way through a clock
   tick, and in the worst case it would be at the beginning of such a tick.
2. Suppose the remote system recorded that event at time `R_new`. Then any
   event happening as early as `R_new-w` in remote time would be recorded as
   arriving in the same window. Due to the discrete nature of the clock, any
   event arriving strictly after `R_new-w-rr` would likewise be recorded in the
   same window. This represents a remote gap of less than `(R_new) - (R_new-w-rr) ==
   w+rr`. In true time that could be no greater than `(w+rr)/(1-1e-6*re)`.
   Hence, any event received at some time `ts <= now+ltr-(w+rr)/(1-1e-6*re)`
   would not be recorded in the same window by the remote system.
3. Let us consider an acknowledged event -- one where at some true timestamp
   `ts` we recorded that the event had round-tripped. The actual time the event
   was recorded was no later than `ts-rtl`. As such, if `ts-rtl <=
   now+ltr-(w+rr)/(1-1e-6*re)` then that event would definitely not be recorded
   in the same window as any newly dispatched event.
4. The challenge then is to translate true times to locally measured clock
   signals. Re-writing the above equation, we have `now >= ts
   + (w+rr)/(1-1e-6*re) - rtl - ltr`. This is simply saying that a true-time
   gap of `(w+rr)/(1-1e-6*re)-rtl-ltr` must occur, and given that we have
   available to use an error rate for local clock measurements we can bound
   that gap in local time to `[(w+rr)/(1-1e-6*re)-rtl-ltr]*(1+1e-6*le)`, so
   long as measurements are confined to the same position in a local clock
   tick. However, due to the discrete nature of the local clock, waiting till
   such a gap has elapsed as measured by the local clock could potentially
   leave us high and dry by any duration less than a full tick. Consequently we
   instead need a gap of at least `[(w+rr)/(1-1e-6*re)-rtl-ltr]*(1+1e-6*le)+lr`.
5. Note that the above expression is constant, given our assumptions. For
   convenience, let `gap=[(w+rr)/(1-1e-6*re)-rtl-ltr]*(1+1e-6*le)+lr`. Then for
   any event which we have locally recorded at time `ts` as having completed
   then at local time `ts+gap` no event we dispatched immediately could be
   recorded in the same window as that completed event.
6. This lends itself to a simple plan. At any given point in time `now` there
   are `j` events outstanding and `k` events which have locally been recorded
   as having completed no later than `now-gap`. If `j+k<n` then we can
   immediately dispatch another event. Otherwise, if `j+k==n` (since if `j+k>n`
   then we might feasibly have violated the core operating assumption) then let
   `t0` denote the completed time for the oldest completed event (if none
   exists yet, let it denote the completed time for the first outstanding event
   which does complete -- assuming n>0). In that case, at time `t0+gap` that
   event will no longer be included in the same window as any newly dispatched
   event, so at most `n-1` events might conflict with a new dispatch, and we're
   free to send out another.
7. Reflecting further on point (6), you're effectively claiming the oldest
   record which might cause a conflict, waiting until no such conflict can
   exist, and then dispatching a new event. The acts of claiming and
   dispatching can be completely divorced however -- any event which won't
   conflict with the 2nd oldest won't conflict with the oldest either (and so
   on), and with a little more effort you can show that "checking out" the
   oldest event as a token/currency of sorts can safely give you a credit to
   dispatch an event at any point in the future so long as you only use it once
   and so long as everyone else dispatching events has also checked out such a
   token. This is readily implemented as a queue of completion times.
