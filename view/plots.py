import plotly.graph_objects as go


ACCENT = "#2563EB"
TEXT = "#1E293B"
GRID = "#E2E8F0"
BACKGROUND = "#FFFFFF"


def _apply_theme(fig, title, x_title, y_title):
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT)),
        font=dict(color=TEXT),
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
        line=dict(color=ACCENT, width=2),
        marker=dict(color=ACCENT, size=6),
    ))
    fig.add_hline(
        y=10,
        line_dash="dash",
        line_color="#64748B",
        annotation_text="Total Data Loss Threshold",
        annotation_font_color="#64748B",
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
        line=dict(color=ACCENT, width=2),
        marker=dict(color=ACCENT, size=7),
    ))
    return _apply_theme(fig, title, "Corruption Severity", "PSNR (dB)")


def plot_audio_sensitivity_curve(magnitudes, snr_values):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=magnitudes,
        y=snr_values,
        mode="lines+markers",
        name="SNR",
        line=dict(color=ACCENT, width=2),
        marker=dict(color=ACCENT, size=7),
    ))
    return _apply_theme(
        fig,
        "Audio Key Sensitivity Curve",
        "Perturbation Magnitude",
        "Decryption Quality (SNR in dB)",
    )