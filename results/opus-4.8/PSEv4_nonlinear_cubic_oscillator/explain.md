# Discovered Law for `dv_dt`

## Formula

$$\frac{dv}{dt} = -\beta\, x^3 \;-\; \frac{g_0}{1 + a\,x^2}\, v$$

with fitted parameters

| parameter | value | meaning |
|-----------|-------|---------|
| $\beta$   | **2.25** | strength of the cubic restoring force |
| $g_0$     | **0.67237** | damping coefficient at $x=0$ |
| $a$       | **0.44406** | rate at which damping weakens with amplitude |

The output does **not** depend on `t` explicitly — the system is autonomous.

## Interpretation

This is a **damped nonlinear (Duffing-type) oscillator**:

- **Restoring force** $-\beta x^3$: a purely cubic spring. There is no linear
  ($\propto x$) term — position curvature grows with the cube of the
  displacement, so large excursions are pulled back hard while small ones are
  nearly free. This is why the trajectory in the data starts at $x=1.2$ and
  relaxes toward $x\approx 0$.

- **Damping** $-\gamma(x)\,v$ with a **position-dependent coefficient**
  $\gamma(x)=g_0/(1+a x^2)$: friction is strongest near the origin
  ($\gamma(0)=g_0\approx0.672$) and falls off smoothly as the amplitude grows
  (e.g. $\gamma(1.2)\approx0.42$). The damping is always positive, so energy is
  monotonically removed and the oscillation decays — consistent with the data,
  where the velocity amplitude shrinks over time.

## How it was found

1. **Anchor point.** At $t=0$, $v=0$ and $x=1.2$, giving
   $dv/dt=-3.888=-2.25\times1.2^3$ exactly ⇒ the restoring term is $-2.25\,x^3$
   with $\beta = 2.25 = 9/4$.

2. **Isolate the damping.** The residual $r = dv/dt + 2.25\,x^3$ is almost
   perfectly proportional to $v$ (correlation $-0.99$), confirming a linear-in-$v$
   damping term. The effective coefficient $\gamma(x) = -r/v$ was then found to be
   an even function of $x$, peaking at $x=0$ and decreasing symmetrically with
   $|x|$.

3. **Functional form.** Binning $\gamma$ against $x$ and testing candidate shapes
   (polynomial, exponential, Lorentzian), the **Lorentzian** $g_0/(1+a x^2)$ gave
   the best parsimonious fit. Its Taylor expansion
   $g_0(1 - a x^2 + a^2 x^4 - \dots)$ also matches the polynomial-in-$x^2$ damping
   fits, confirming it is the underlying form.

4. **Final fit.** With $\beta$ fixed at $2.25$, a nonlinear least-squares fit of
   $g_0,a$ over all 4500 rows gave $g_0=0.67237$, $a=0.44406$.

## Fit quality (training data)

- $R^2 = 0.99997$
- RMSE $= 0.0021$ (signal ranges over $\approx[-3.9,\,0.8]$)
- max absolute error $= 0.025$ (occurs at the highest speeds, $|v|\approx0.9$)
