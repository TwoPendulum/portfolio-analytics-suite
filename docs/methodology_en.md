## Why Does Correlation Change Over Time?
*Why Does Correlation Change Over Time?*

Describing the relationship between two assets with a single static number is like describing a city's climate using only the annual average temperature—it misses most of the story. During market stress (e.g., March 2020), correlations between assets spike suddenly; during calm periods, they naturally decline. A static correlation coefficient cannot capture these dynamics. The goal of this tool is to **track these changes in real time**, so that when you construct a portfolio, you see "what is happening now" rather than "what happened on average."

Computing a static correlation using 5 years of historical data implicitly assumes that the relationship between assets remains unchanged over that period. This assumption is wrong most of the time. Market structure evolves, macro conditions shift, and investor behavior adapts—correlations naturally follow.

---

## Removing Volatility Noise: The GARCH Filter
*Removing Volatility Noise: The GARCH Filter*

Intuition: Two athletes' coordination should not be judged based on the intensity of a single match. When the pace is frantic (high volatility), every movement is amplified—the observed co-movement may simply be because "the game is intense," not because the two athletes are genuinely better coordinated.

GARCH (Generalized Autoregressive Conditional Heteroskedasticity) standardizes away this "game intensity." We fit a GARCH(1,1) model to each asset's return series, extract time-varying conditional volatility, and compute standardized returns:

$$\tilde{r}_t = \frac{r_t}{\sigma_t}$$

The standardized series now reflects **pure asset performance**, free from volatility-driven distortion. The observation fed into the Kalman filter is simply the product of two standardized returns:

$$\text{Obs}_t = \tilde{r}^X_t \times \tilde{r}^Y_t$$

If GARCH fails to converge for a given asset (common for low-volatility fixed-income instruments), we automatically fall back to an **EWMA (exponentially weighted moving average) rolling standard deviation**, with a yellow warning banner indicating which assets used the fallback.

**Why does GARCH fail on ultra-low-volatility assets?** GARCH(1,1) estimates parameters by maximizing log-likelihood, which requires meaningful "volatility clustering" in the series (large moves followed by large moves, calm periods followed by calm periods). For assets with daily volatility in the 0.1% range (e.g., short-term Treasury ETFs), returns are near-constant and the likelihood surface is extremely flat — the optimizer cannot find reliable parameter estimates.

**The EWMA fallback**: When GARCH does not converge, we estimate time-varying volatility using an exponentially weighted moving average:

$$\sigma_t^2 = (1 - \alpha) \cdot \sigma_{t-1}^2 + \alpha \cdot r_t^2$$

where the smoothing factor α = 2/(span+1), with span defaulting to 20 trading days. This is equivalent to assuming volatility has a "memory" of roughly one month — recent fluctuations carry more weight, while older ones decay exponentially. Unlike GARCH, EWMA has only one fixed parameter requiring no optimization, so it produces stable output for any return series.

**Practical impact**: In the current default asset list, STIP (short-term TIPS ETF, ~0.15% daily vol) and SHY (short-term Treasury ETF, ~0.11% daily vol) typically trigger this fallback. For these assets, the statistical quality of the standardized returns is indistinguishable from GARCH — both instruments lack meaningful volatility clustering to begin with, and EWMA adequately captures their weak time-varying characteristics. If an asset triggers the fallback for other reasons (e.g., fewer than 30 observations), the page will display a specific warning.

---

## The Kalman Filter: A Self-Updating Belief
*The Kalman Filter: A Self-Updating Belief*

Intuition: You observe the weather each day and gradually form an understanding of a city's climate patterns. Each new observation doesn't completely overturn your prior belief, nor do you ignore the new data entirely—you weight old and new information according to your confidence in the observation's reliability. This is exactly what a Kalman filter does.

In this tool, the Kalman filter tracks a **hidden state**: the true correlation ρ. We cannot observe it directly—all we see each period is a noisy observation (the product of two standardized returns). The Kalman filter operates in two steps:

- **Predict**: Without assuming mean reversion (φ=1), today's best guess is simply yesterday's estimate. We deliberately avoid assuming that "correlation should regress to some mean"—we let the data speak for itself.
- **Update**: When a new observation arrives, we use the Kalman gain K to weight old and new information. K depends on how confident we are in the current estimate (P) and how reliable the observation is (R).

Standard 1D Kalman recursion:

$$\hat{\rho}_{t|t-1} = \hat{\rho}_{t-1|t-1}$$

$$P_{t|t-1} = P_{t-1|t-1} + Q$$

$$K_t = \frac{P_{t|t-1}}{P_{t|t-1} + R}$$

$$\hat{\rho}_{t|t} = \hat{\rho}_{t|t-1} + K_t(\text{Obs}_t - \hat{\rho}_{t|t-1})$$

The final output is clipped to the [-1, +1] interval to preserve the physical meaning of a correlation coefficient.

**Initial value**: A Kalman filter needs a starting point $$\hat{\rho}_{0|0}$$. Instead of starting from zero (which would assume the two assets are completely unrelated), we initialize with the **historical Pearson correlation coefficient** computed from the two standardized return series. This gives the filter a sensible prior before the first observation arrives; subsequent observations then incrementally refine this estimate. The initial uncertainty is set to $$P_{0|0}=0.1$$ (rather than the classical 1.0), reflecting higher confidence in this data-driven prior — preventing the first noisy observation from pulling the estimate far from a reasonable starting point.

**The φ=1 design choice**: Many applications introduce mean reversion in the Kalman filter (φ<1), assuming the state naturally returns to some long-term average. We deliberately refrain from this—we have no prior reason to believe that the "natural correlation" between two assets should be fixed at any specific level. The model stays open; where correlation goes is entirely data-driven.

Two adjustable parameters:
- **Q (process noise)**: How much you expect correlation to naturally vary over time. Higher Q makes the filter more responsive to recent observations.
- **R (observation noise)**: How reliable you think each period's observation is. Higher R makes the filter trust historical estimates more, producing smoother output.

---

## Efficient Frontier: The Best Possible Trade-off
*Efficient Frontier: The Best Possible Trade-off*

Intuition: With a fixed budget for ingredients, you want both nutrition and flavor. The efficient frontier is the set of all combinations where "you cannot do better." Any portfolio off the frontier means you're either sacrificing returns for the same risk, or bearing extra risk for the same returns.

**Mean-variance optimization** follows the classic Markowitz framework. We solve two core objectives:

1. **Maximize Sharpe Ratio**: Find the portfolio with the highest excess return per unit of risk.
2. **Minimize Volatility**: Find the portfolio with the lowest possible volatility.

Between these two endpoints, we generate the full efficient frontier via parameterized scanning (100 target return points). Each point represents: **the lowest-volatility portfolio achievable at a given target return**.

**The key innovation: dynamic correlation**

Traditional efficient frontiers use a static historical covariance matrix. We use the **latest-period dynamic correlation matrix** from Tab 1's Kalman filter output (monthly by default), combined with your forward volatility estimates to construct the covariance matrix:

$$\Sigma_{ij} = \rho_{ij}^{\text{KF}} \cdot \sigma_i^{\text{fwd}} \cdot \sigma_j^{\text{fwd}}$$

This means the frontier reflects optimal allocation under the **current market structure**, not stale data averaged over the past 5 years.

**Two critical inputs—Forward μ and Forward σ**

- **Forward μ**: Your estimate of future expected returns. The tool provides historical averages as a starting point, but you are encouraged to override them with your own research.
- **Forward σ**: Your estimate of future volatility. Similarly seeded from history, with manual override capability.

---

## Model Limitations
*Model Limitations*

- **The Kalman filter lags on sudden structural breaks**: The filter assumes correlation changes are linear and gradual. It will react with a delay to the first day of a market crash. This is an inherent limitation of all linear state-space models.
- **Forward μ and σ determine EF quality**: The efficient frontier is only as good as the forward estimates you input. Historical averages serve merely as a reference starting point and do not constitute any prediction or investment advice.
- **Short-allowed EF is more sensitive to parameters**: The -50% per-asset short cap is an engineering constraint, not a theoretical optimum. Small parameter changes can produce large weight swings in short-selling scenarios.
- **GARCH may not converge for ultra-low-volatility assets**: Certain fixed-income instruments with near-zero volatility may cause GARCH to fail; in such cases, the tool falls back to EWMA rolling standard deviation with a visible warning.
- **This tool does not constitute investment advice**: All outputs are for analytical reference only. Actual investment decisions should account for personal risk tolerance, investment objectives, and professional judgment.
