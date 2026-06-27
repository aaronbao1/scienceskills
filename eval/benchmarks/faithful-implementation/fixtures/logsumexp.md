# Fixture — numerically stable log-sum-exp

Reference definition: logsumexp(x) = m + log(Σ_i exp(x_i − m)), where m = max_i x_i.

Properties (oracles):
- logsumexp([0, 0]) = log(2) ≈ 0.6931471805599453.
- Shift invariance: logsumexp(x + c) = logsumexp(x) + c for any scalar c.
- Stability: logsumexp([1000, 1000]) must be finite (≈ 1000 + log 2), not inf.
