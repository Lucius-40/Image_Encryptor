import plotly.graph_objects as go


GREEN = "#39FF14"
TEXT = "#B7FFB0"
GRID = "rgba(57, 255, 20, 0.18)"
BACKGROUND = "rgba(0, 0, 0, 0)"


def _apply_theme(fig, title, x_title, y_title):
    fig.update_layout(
        title=dict(text=title, font=dict(family="Courier New", color=GREEN)),
        font=dict(family="Courier New", color=TEXT),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        margin=dict(l=65, r=25, t=65, b=60),
        hovermode="x unified",
        xaxis=dict(
            title=x_title,
            color=TEXT,
            gridcolor=GRID,
            zerolinecolor=GRID,
        ),
        yaxis=dict(
            title=y_title,
            color=TEXT,
            gridcolor=GRID,
            zerolinecolor=GRID,
        ),
        legend=dict(font=dict(color=TEXT)),
    )
    return fig


def plot_sensitivity_curve(magnitudes, psnr_values):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=magnitudes,
        y=psnr_values,
        mode="lines+markers",
        name="PSNR",
        line=dict(color=GREEN, width=2),
        marker=dict(color=GREEN, size=6),
    ))
    fig.add_hline(
        y=10,
        line_dash="dash",
        line_color="#FF5555",
        annotation_text="Total Data Loss Threshold",
        annotation_font_color="#FF7777",
    )
    return _apply_theme(
        fig,
        "DRPE Key Sensitivity Curve",
        "Error Magnitude",
        "Decryption Quality (PSNR in dB)",
    )


def plot_robustness_curve(severity, psnr_values, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=severity,
        y=psnr_values,
        mode="lines+markers",
        name="PSNR",
        line=dict(color="#FF9D2E", width=2),
        marker=dict(color="#FF9D2E", size=7),
    ))
    return _apply_theme(fig, title, "Corruption Severity", "PSNR (dB)")


def plot_audio_sensitivity_curve(magnitudes, snr_values):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=magnitudes,
        y=snr_values,
        mode="lines+markers",
        name="SNR",
        line=dict(color="#63A8FF", width=2),
        marker=dict(color="#63A8FF", size=7),
    ))
    return _apply_theme(
        fig,
        "Audio Key Sensitivity Curve",
        "Perturbation Magnitude",
        "Decryption Quality (SNR in dB)",
    )