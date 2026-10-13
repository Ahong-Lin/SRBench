"""Truth/prediction overlays with a pale-pink held-out region."""
import numpy as np


def plot_metadata(split, spec):
    """Recover coordinate scales for provided CSVs without inventing a split."""
    result = dict(split)
    transforms = dict(split.get("coordinate_transform", {}))
    for variable in spec.get("independent_variables", []):
        transforms.setdefault(variable["symbol"], variable.get("scale", "linear"))
    result["coordinate_transform"] = transforms
    return result


def make_figure(frame, contract, split, *, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    truth = frame["ground_truth"].to_numpy()
    prediction = frame["prediction"].to_numpy()
    partition = frame["partition"].to_numpy()
    train = np.flatnonzero(partition == "train")
    test = np.flatnonzero(partition == "test")
    xname = contract["features"][0]
    coordinates = frame[xname].to_numpy()
    # A genuine right-hand interval is needed to mark a physical test region.
    # Arbitrary provided/interleaved splits instead use explicit sample ranks.
    physical_axis = (len(contract["features"]) == 1 or contract["family"] == "ode")
    physical_axis = physical_axis and len(np.unique(coordinates)) == len(coordinates)
    if len(train) and len(test):
        physical_axis = physical_axis and coordinates[train].max() < coordinates[test].min()

    fig, ax = plt.subplots(figsize=(11, 4.8))
    if physical_axis:
        order = np.argsort(coordinates, kind="stable")
        x = coordinates[order]
        log_axis = split.get("coordinate_transform", {}).get(xname) == "log"
        if log_axis:
            ax.set_xscale("log")
        if len(train) and len(test):
            left, right = coordinates[train].max(), coordinates[test].min()
            cut = np.sqrt(left * right) if log_axis else (left + right) / 2
            boundary = split.get("normalized_boundary")
            ranges = split.get("sampling_ranges", {})
            if boundary is not None and xname in ranges:
                low, high = ranges[xname]
                candidate = (10 ** (np.log10(low) + boundary * (np.log10(high) - np.log10(low)))
                             if log_axis else low + boundary * (high - low))
                if left <= candidate <= right:
                    cut = candidate
        else:
            cut = x[0] if len(test) else None
        ax.plot(x, truth[order], color="#2563a6", lw=2.2, label="ground truth")
        ax.plot(x, prediction[order], color="#d05d27", lw=1.6, ls="--", label="LLM solution")
        ax.set_xlabel(xname)
        xmin, xmax = x[0], x[-1]
    else:
        # Sort separately within each partition for a legible paired-sample view.
        # This rank is not a coordinate in the multivariate input space.
        order = np.concatenate([indices[np.argsort(truth[indices], kind="stable")]
                                for indices in (train, test)])
        x = np.arange(1, len(order) + 1)
        ax.scatter(x, truth[order], color="#2563a6", s=10, alpha=.8, label="ground truth")
        ax.scatter(x, prediction[order], color="#d05d27", s=9, alpha=.65, label="LLM solution")
        xmin, xmax = .5, len(order) + .5
        cut = len(train) + .5 if len(test) else None
        ax.set_xlabel("Sample rank (train then test; sorted by truth within each partition)")

    if xmax > xmin:
        ax.set_xlim(xmin, xmax)
    if cut is not None:
        ax.axvspan(cut, xmax, color="#fce4ec", zorder=0)
        if len(train):
            ax.axvline(cut, color="#ce94a7", ls="--", lw=1)
    # Position labels in axes coordinates, accounting for logarithmic axes.
    if len(train) and len(test):
        if physical_axis and log_axis:
            fraction = (np.log(cut) - np.log(xmin)) / (np.log(xmax) - np.log(xmin))
        else:
            fraction = (cut - xmin) / (xmax - xmin)
        regions = [(fraction / 2, f"Train (n={len(train)})"),
                   ((fraction + 1) / 2, f"Test (n={len(test)})")]
    else:
        regions = [(.5, f"{'Test' if len(test) else 'Train'} (n={len(frame)})")]
    for position, label in regions:
        ax.text(position, 1.025, label, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=10, color="#6b5260")
    ax.set_ylabel(contract["target"])
    ax.legend(frameon=False, loc="best")
    ax.grid(alpha=.12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .94))
    return fig


def make_spatial_figure(frame, contract, split, *, title):
    """Show a two-input response in its input space, using cached predictions."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    from matplotlib.colors import Normalize
    from matplotlib.lines import Line2D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import ConvexHull, QhullError

    if contract["family"] != "static" or len(contract["features"]) != 2:
        raise ValueError("Spatial surfaces require exactly two independent static inputs")
    names = contract["features"]
    coordinates = frame[names].to_numpy(dtype=float).copy()
    labels = list(names)
    for i, name in enumerate(names):
        if split.get("coordinate_transform", {}).get(name) == "log":
            coordinates[:, i] = np.log10(coordinates[:, i])
            labels[i] = f"log10({name})"
    truth = frame["ground_truth"].to_numpy()
    prediction = frame["prediction"].to_numpy()
    lower = min(truth.min(), prediction.min())
    upper = max(truth.max(), prediction.max())
    span = max(upper - lower, 1e-12)
    norm = Normalize(lower, upper if upper > lower else lower + 1)
    floor = lower - .08 * span
    test = frame["partition"].to_numpy() == "test"
    hull = None
    if test.sum() >= 3:
        try:
            points = coordinates[test]
            hull = points[ConvexHull(points).vertices]
        except QhullError:
            pass
    triangulation = mtri.Triangulation(*coordinates.T)
    # Do not interpolate surfaces across the train/test interface.
    mixed = np.ptp(test[triangulation.triangles].astype(int), axis=1) != 0
    triangulation.set_mask(mixed)
    fig = plt.figure(figsize=(12, 10), layout="constrained")
    heat_axes = []
    for i, (values, name, color) in enumerate([
            (truth, "Ground truth", "#2563a6"),
            (prediction, "LLM solution", "#d05d27")]):
        ax = fig.add_subplot(2, 2, i + 1)
        heat_axes.append(ax)
        scatter = ax.scatter(*coordinates.T, c=values, norm=norm, cmap="viridis",
                             s=9, linewidths=0, rasterized=True)
        if hull is not None:
            closed = np.vstack([hull, hull[0]])
            ax.plot(*closed.T, color="#f098b4", lw=2, ls="--")
        ax.set(xlabel=labels[0], ylabel=labels[1], title=f"{name} — sampled values")
        ax3 = fig.add_subplot(2, 2, i + 3, projection="3d")
        ax3.plot_trisurf(triangulation, values, color=color, alpha=.85,
                        linewidth=0, antialiased=True)
        if hull is not None:
            polygon = np.column_stack([hull, np.full(len(hull), floor)])
            ax3.add_collection3d(Poly3DCollection([polygon], facecolor="#fce4ec",
                                                 edgecolor="#df8faa", alpha=.85))
        ax3.set(xlabel=labels[0], ylabel=labels[1], zlabel=contract["target"],
                zlim=(floor, upper + .05 * span), title=f"{name} — surface from samples")
        ax3.view_init(elev=28, azim=-125)
    fig.colorbar(scatter, ax=heat_axes, label=contract["target"], shrink=.85)
    fig.suptitle(title + "\nSame input coordinates and shared value scales", fontsize=12)
    if hull is not None:
        heat_axes[0].legend(handles=[Line2D([0], [0], color="#f098b4", ls="--", lw=2,
                                          label="Test sample hull (pink floor below)")],
                            loc="best", fontsize=8)
    return fig
