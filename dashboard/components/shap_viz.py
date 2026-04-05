"""
==============================================================================
SHAP EXPLAINABILITY VISUALIZATION DASHBOARD
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Interactive Streamlit dashboard for SHAP explainability visualization,
enabling users to understand model predictions through feature importance
and contribution analysis.

FEATURES:
---------
- Global feature importance plots
- Local explanation plots (force, waterfall)
- Feature dependency plots
- Interactive sample selection
- Export explanations to PDF/HTML

USAGE:
------
    # In Streamlit app
    from dashboard.components.shap_viz import SHAPDashboard

    dashboard = SHAPDashboard(model, X_train)
    dashboard.render()
"""

from __future__ import annotations

import io
import base64
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import json


# Lazy imports for optional dependencies
def _get_streamlit():
    try:
        import streamlit as st

        return st
    except ImportError:
        return None


def _get_shap():
    try:
        import shap

        return shap
    except ImportError:
        return None


def _get_matplotlib():
    try:
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def _get_numpy():
    try:
        import numpy as np

        return np
    except ImportError:
        return None


def _get_pandas():
    try:
        import pandas as pd

        return pd
    except ImportError:
        return None


@dataclass
class ExplanationResult:
    """Result of SHAP explanation."""

    sample_id: int
    prediction: float
    base_value: float
    feature_contributions: Dict[str, float]
    top_positive: List[Tuple[str, float]]
    top_negative: List[Tuple[str, float]]

    def to_dict(self) -> Dict:
        return {
            "sample_id": self.sample_id,
            "prediction": round(self.prediction, 4),
            "base_value": round(self.base_value, 4),
            "feature_contributions": {
                k: round(v, 4) for k, v in self.feature_contributions.items()
            },
            "top_positive": [(k, round(v, 4)) for k, v in self.top_positive],
            "top_negative": [(k, round(v, 4)) for k, v in self.top_negative],
        }


class SHAPExplainer:
    """
    Wrapper for SHAP explainability computations.

    Supports multiple model types and provides consistent interface
    for computing and caching explanations.
    """

    SUPPORTED_MODELS = [
        "xgboost",
        "lightgbm",
        "catboost",
        "random_forest",
        "gradient_boosting",
        "logistic_regression",
        "neural_network",
    ]

    def __init__(
        self,
        model: Any,
        background_data: Any,
        model_type: Optional[str] = None,
        feature_names: Optional[List[str]] = None,
        max_background_samples: int = 100,
    ):
        """
        Initialize SHAP explainer.

        Args:
            model: Trained ML model
            background_data: Background dataset for SHAP
            model_type: Type of model (auto-detected if None)
            feature_names: Names of features
            max_background_samples: Max samples for background
        """
        self.model = model
        self.model_type = model_type or self._detect_model_type()
        self.feature_names = feature_names

        np = _get_numpy()
        shap = _get_shap()

        if np is None or shap is None:
            self.explainer = None
            self.background = None
            return

        # Sample background data if too large
        if hasattr(background_data, "shape"):
            if background_data.shape[0] > max_background_samples:
                indices = np.random.choice(
                    background_data.shape[0], max_background_samples, replace=False
                )
                background_data = background_data[indices]

        self.background = background_data

        # Create appropriate explainer
        self.explainer = self._create_explainer()

        # Cache for explanations
        self._cache: Dict[str, Any] = {}

    def _detect_model_type(self) -> str:
        """Detect model type from class name."""
        class_name = type(self.model).__name__.lower()

        if "xgb" in class_name:
            return "xgboost"
        elif "lgbm" in class_name or "lightgbm" in class_name:
            return "lightgbm"
        elif "catboost" in class_name:
            return "catboost"
        elif "randomforest" in class_name:
            return "random_forest"
        elif "gradientboosting" in class_name:
            return "gradient_boosting"
        elif "logistic" in class_name:
            return "logistic_regression"
        else:
            return "generic"

    def _create_explainer(self) -> Any:
        """Create appropriate SHAP explainer for model type."""
        shap = _get_shap()
        if shap is None:
            return None

        try:
            if self.model_type in ["xgboost", "lightgbm", "catboost"]:
                return shap.TreeExplainer(self.model)
            elif self.model_type in ["random_forest", "gradient_boosting"]:
                return shap.TreeExplainer(self.model)
            elif self.model_type == "logistic_regression":
                return shap.LinearExplainer(self.model, self.background)
            else:
                # Use KernelExplainer as fallback
                return shap.KernelExplainer(
                    (
                        self.model.predict_proba
                        if hasattr(self.model, "predict_proba")
                        else self.model.predict
                    ),
                    self.background,
                )
        except Exception:
            # Fallback to KernelExplainer
            return shap.KernelExplainer(
                self.model.predict if hasattr(self.model, "predict") else lambda x: x,
                self.background,
            )

    def explain(self, X: Any, check_additivity: bool = False) -> Any:
        """
        Compute SHAP values for given samples.

        Args:
            X: Samples to explain
            check_additivity: Whether to check SHAP additivity

        Returns:
            SHAP values array
        """
        shap = _get_shap()
        if shap is None or self.explainer is None:
            return None

        # Cache key
        np = _get_numpy()
        if np is not None and hasattr(X, "tobytes"):
            cache_key = hash(X.tobytes())
            if cache_key in self._cache:
                return self._cache[cache_key]

        shap_values = self.explainer.shap_values(X, check_additivity=check_additivity)

        # Cache result
        if np is not None and hasattr(X, "tobytes"):
            self._cache[cache_key] = shap_values

        return shap_values

    def explain_single(self, sample: Any, sample_id: int = 0) -> ExplanationResult:
        """
        Get detailed explanation for a single sample.

        Args:
            sample: Single sample to explain
            sample_id: ID for the sample

        Returns:
            ExplanationResult with detailed breakdown
        """
        np = _get_numpy()
        if np is None:
            return ExplanationResult(
                sample_id=sample_id,
                prediction=0.5,
                base_value=0.5,
                feature_contributions={},
                top_positive=[],
                top_negative=[],
            )

        # Reshape if needed
        if len(sample.shape) == 1:
            sample = sample.reshape(1, -1)

        shap_values = self.explain(sample)

        if shap_values is None:
            return ExplanationResult(
                sample_id=sample_id,
                prediction=0.5,
                base_value=0.5,
                feature_contributions={},
                top_positive=[],
                top_negative=[],
            )

        # Handle multi-class case
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class

        values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

        # Get feature names
        feature_names = self.feature_names or [f"feature_{i}" for i in range(len(values))]

        # Create contributions dict
        contributions = dict(zip(feature_names, values.tolist()))

        # Sort by absolute contribution
        sorted_contrib = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

        # Top positive and negative
        top_positive = [(k, v) for k, v in sorted_contrib if v > 0][:5]
        top_negative = [(k, v) for k, v in sorted_contrib if v < 0][:5]

        # Get base value
        base_value = (
            self.explainer.expected_value[1]
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else self.explainer.expected_value
        )

        # Calculate prediction
        prediction = base_value + sum(values)

        return ExplanationResult(
            sample_id=sample_id,
            prediction=float(prediction),
            base_value=float(base_value),
            feature_contributions=contributions,
            top_positive=top_positive,
            top_negative=top_negative,
        )

    def get_global_importance(self, X: Any) -> Dict[str, float]:
        """
        Get global feature importance across all samples.

        Args:
            X: Dataset to compute importance over

        Returns:
            Dict mapping feature names to importance scores
        """
        np = _get_numpy()
        if np is None:
            return {}

        shap_values = self.explain(X)

        if shap_values is None:
            return {}

        # Handle multi-class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        # Mean absolute SHAP value per feature
        importance = np.abs(shap_values).mean(axis=0)

        feature_names = self.feature_names or [f"feature_{i}" for i in range(len(importance))]

        return dict(zip(feature_names, importance.tolist()))


class SHAPDashboard:
    """
    Streamlit dashboard for SHAP visualizations.

    Provides interactive exploration of model explanations with
    multiple visualization types.
    """

    def __init__(
        self,
        model: Any = None,
        X_train: Any = None,
        X_test: Any = None,
        y_test: Any = None,
        feature_names: Optional[List[str]] = None,
        class_names: Optional[List[str]] = None,
    ):
        """
        Initialize SHAP dashboard.

        Args:
            model: Trained model
            X_train: Training data for background
            X_test: Test data for explanations
            y_test: Test labels
            feature_names: Feature names
            class_names: Class names for classification
        """
        self.model = model
        self.X_train = X_train
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        self.class_names = class_names or ["Negative", "Positive"]

        # Initialize explainer if model provided
        self.explainer = None
        if model is not None and X_train is not None:
            self.explainer = SHAPExplainer(
                model=model, background_data=X_train, feature_names=feature_names
            )

    def render(self) -> None:
        """Render the complete SHAP dashboard."""
        st = _get_streamlit()
        if st is None:
            print("Streamlit not available. Cannot render dashboard.")
            return

        st.title("🔍 SHAP Explainability Dashboard")
        st.markdown("---")

        # Sidebar controls
        self._render_sidebar()

        # Main content
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📊 Global Importance",
                "🔬 Local Explanations",
                "📈 Feature Dependencies",
                "📋 Batch Analysis",
            ]
        )

        with tab1:
            self._render_global_importance()

        with tab2:
            self._render_local_explanations()

        with tab3:
            self._render_feature_dependencies()

        with tab4:
            self._render_batch_analysis()

    def _render_sidebar(self) -> None:
        """Render sidebar controls."""
        st = _get_streamlit()
        if st is None:
            return

        st.sidebar.header("⚙️ Settings")

        # Sample selection
        if self.X_test is not None:
            st.sidebar.subheader("Sample Selection")
            max_samples = len(self.X_test) if hasattr(self.X_test, "__len__") else 100
            st.session_state.sample_idx = st.sidebar.slider("Sample Index", 0, max_samples - 1, 0)

        # Visualization settings
        st.sidebar.subheader("Visualization")
        st.session_state.max_features = st.sidebar.slider("Max Features to Show", 5, 30, 15)

        st.session_state.plot_type = st.sidebar.selectbox(
            "Plot Type", ["bar", "dot", "violin", "layered_violin"]
        )

        # Export options
        st.sidebar.subheader("Export")
        if st.sidebar.button("📥 Export Report"):
            self._export_report()

    def _render_global_importance(self) -> None:
        """Render global feature importance section."""
        st = _get_streamlit()
        plt = _get_matplotlib()
        shap = _get_shap()
        np = _get_numpy()

        if st is None:
            return

        st.header("Global Feature Importance")
        st.markdown("""
        Global importance shows which features have the largest impact on model 
        predictions across all samples. Higher values indicate more influential features.
        """)

        if self.explainer is None or self.X_test is None:
            st.warning("⚠️ Model and data required for SHAP analysis.")
            self._render_demo_global()
            return

        # Calculate SHAP values
        with st.spinner("Computing SHAP values..."):
            shap_values = self.explainer.explain(self.X_test)

        if shap_values is None:
            self._render_demo_global()
            return

        # Summary plot
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Feature Importance (Bar)")
            fig, ax = plt.subplots(figsize=(10, 8))
            if isinstance(shap_values, list):
                shap.summary_plot(
                    shap_values[1],
                    self.X_test,
                    feature_names=self.feature_names,
                    plot_type="bar",
                    max_display=st.session_state.get("max_features", 15),
                    show=False,
                )
            else:
                shap.summary_plot(
                    shap_values,
                    self.X_test,
                    feature_names=self.feature_names,
                    plot_type="bar",
                    max_display=st.session_state.get("max_features", 15),
                    show=False,
                )
            st.pyplot(fig)
            plt.close()

        with col2:
            st.subheader("SHAP Summary Plot")
            fig, ax = plt.subplots(figsize=(10, 8))
            if isinstance(shap_values, list):
                shap.summary_plot(
                    shap_values[1],
                    self.X_test,
                    feature_names=self.feature_names,
                    max_display=st.session_state.get("max_features", 15),
                    show=False,
                )
            else:
                shap.summary_plot(
                    shap_values,
                    self.X_test,
                    feature_names=self.feature_names,
                    max_display=st.session_state.get("max_features", 15),
                    show=False,
                )
            st.pyplot(fig)
            plt.close()

        # Top features table
        st.subheader("📋 Top Features")
        importance = self.explainer.get_global_importance(self.X_test)
        sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)

        pd = _get_pandas()
        if pd is not None:
            df = pd.DataFrame(sorted_imp[:15], columns=["Feature", "Mean |SHAP|"])
            df["Rank"] = range(1, len(df) + 1)
            df = df[["Rank", "Feature", "Mean |SHAP|"]]
            st.dataframe(df, use_container_width=True)

    def _render_demo_global(self) -> None:
        """Render demo global importance when no model available."""
        st = _get_streamlit()
        pd = _get_pandas()

        if st is None:
            return

        st.info("📊 Demo Mode: Showing sample feature importance")

        # Sample data
        demo_features = [
            ("transaction_amount", 0.234),
            ("time_since_last", 0.189),
            ("merchant_category", 0.156),
            ("distance_from_home", 0.134),
            ("transaction_frequency", 0.112),
            ("device_type", 0.089),
            ("card_present", 0.078),
            ("day_of_week", 0.056),
            ("hour_of_day", 0.045),
            ("account_age", 0.034),
        ]

        if pd is not None:
            df = pd.DataFrame(demo_features, columns=["Feature", "Importance"])

            # Bar chart
            st.bar_chart(df.set_index("Feature"))

            # Table
            df["Rank"] = range(1, len(df) + 1)
            df = df[["Rank", "Feature", "Importance"]]
            st.dataframe(df, use_container_width=True)

    def _render_local_explanations(self) -> None:
        """Render local explanation section for individual predictions."""
        st = _get_streamlit()
        plt = _get_matplotlib()
        shap = _get_shap()

        if st is None:
            return

        st.header("Local Explanations")
        st.markdown("""
        Local explanations show how each feature contributed to a specific prediction.
        Red features push the prediction higher, blue features push it lower.
        """)

        sample_idx = st.session_state.get("sample_idx", 0)

        if self.explainer is None or self.X_test is None:
            st.warning("⚠️ Model and data required for local explanations.")
            self._render_demo_local()
            return

        np = _get_numpy()
        if np is None:
            return

        # Get sample
        sample = self.X_test[sample_idx : sample_idx + 1]

        # Get explanation
        with st.spinner("Computing explanation..."):
            result = self.explainer.explain_single(sample[0], sample_idx)

        # Display prediction info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sample ID", sample_idx)
        with col2:
            st.metric("Prediction", f"{result.prediction:.4f}")
        with col3:
            st.metric("Base Value", f"{result.base_value:.4f}")

        # Force plot
        st.subheader("Force Plot")
        shap_values = self.explainer.explain(sample)
        if shap_values is not None:
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            # Create force plot
            fig, ax = plt.subplots(figsize=(12, 3))
            shap.force_plot(
                (
                    self.explainer.explainer.expected_value[1]
                    if isinstance(self.explainer.explainer.expected_value, (list, np.ndarray))
                    else self.explainer.explainer.expected_value
                ),
                shap_values[0],
                sample[0],
                feature_names=self.feature_names,
                matplotlib=True,
                show=False,
            )
            st.pyplot(fig)
            plt.close()

        # Top contributors
        st.subheader("Top Contributing Features")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🔴 Pushing Higher**")
            for feature, value in result.top_positive:
                st.write(f"• {feature}: +{value:.4f}")

        with col2:
            st.markdown("**🔵 Pushing Lower**")
            for feature, value in result.top_negative:
                st.write(f"• {feature}: {value:.4f}")

    def _render_demo_local(self) -> None:
        """Render demo local explanation."""
        st = _get_streamlit()

        if st is None:
            return

        st.info("🔬 Demo Mode: Showing sample local explanation")

        # Demo metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sample ID", 42)
        with col2:
            st.metric("Prediction", "0.8734")
        with col3:
            st.metric("Base Value", "0.5000")

        # Demo contributors
        st.subheader("Top Contributing Features")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🔴 Pushing Higher (Fraud)**")
            st.write("• transaction_amount: +0.1823")
            st.write("• time_since_last: +0.0945")
            st.write("• distance_from_home: +0.0512")

        with col2:
            st.markdown("**🔵 Pushing Lower (Legitimate)**")
            st.write("• account_age: -0.0234")
            st.write("• card_present: -0.0156")
            st.write("• merchant_trust: -0.0089")

    def _render_feature_dependencies(self) -> None:
        """Render feature dependency plots."""
        st = _get_streamlit()
        plt = _get_matplotlib()
        shap = _get_shap()

        if st is None:
            return

        st.header("Feature Dependencies")
        st.markdown("""
        Dependency plots show how a feature's value affects the model output.
        The color shows interaction with another feature.
        """)

        if self.explainer is None or self.X_test is None:
            st.warning("⚠️ Model and data required for dependency plots.")
            self._render_demo_dependencies()
            return

        # Get feature names
        feature_names = self.feature_names or [f"feature_{i}" for i in range(self.X_test.shape[1])]

        # Feature selection
        selected_feature = st.selectbox("Select Feature", feature_names)

        # Compute SHAP values
        with st.spinner("Computing dependency plot..."):
            shap_values = self.explainer.explain(self.X_test)

        if shap_values is None:
            return

        # Handle multi-class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        # Dependency plot
        fig, ax = plt.subplots(figsize=(10, 6))
        feature_idx = feature_names.index(selected_feature)
        shap.dependence_plot(
            feature_idx, shap_values, self.X_test, feature_names=feature_names, show=False
        )
        st.pyplot(fig)
        plt.close()

    def _render_demo_dependencies(self) -> None:
        """Render demo dependency plot."""
        st = _get_streamlit()

        if st is None:
            return

        st.info("📈 Demo Mode: Dependency analysis unavailable without model")
        st.markdown("""
        With actual data, this section shows:
        - How feature values correlate with SHAP values
        - Feature interactions (color-coded)
        - Non-linear relationships
        """)

    def _render_batch_analysis(self) -> None:
        """Render batch analysis for multiple samples."""
        st = _get_streamlit()
        pd = _get_pandas()

        if st is None:
            return

        st.header("Batch Analysis")
        st.markdown("Analyze multiple samples at once.")

        if self.explainer is None or self.X_test is None:
            st.warning("⚠️ Model and data required for batch analysis.")
            return

        # Sample range
        col1, col2 = st.columns(2)
        with col1:
            start_idx = st.number_input("Start Index", 0, len(self.X_test) - 1, 0)
        with col2:
            end_idx = st.number_input(
                "End Index", start_idx + 1, len(self.X_test), min(start_idx + 10, len(self.X_test))
            )

        if st.button("🔍 Analyze Batch"):
            results = []

            progress = st.progress(0)
            for i, idx in enumerate(range(int(start_idx), int(end_idx))):
                sample = self.X_test[idx]
                result = self.explainer.explain_single(sample, idx)

                results.append(
                    {
                        "Sample": idx,
                        "Prediction": result.prediction,
                        "Top Feature": result.top_positive[0][0] if result.top_positive else "N/A",
                        "Top Impact": result.top_positive[0][1] if result.top_positive else 0,
                    }
                )

                progress.progress((i + 1) / (end_idx - start_idx))

            if pd is not None:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                # Summary stats
                st.subheader("Summary Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Mean Prediction", f"{df['Prediction'].mean():.4f}")
                with col2:
                    st.metric("Std Prediction", f"{df['Prediction'].std():.4f}")

    def _export_report(self) -> None:
        """Export SHAP report."""
        st = _get_streamlit()

        if st is None:
            return

        if self.explainer is None:
            st.error("No model loaded for export.")
            return

        report = {
            "title": "SHAP Explainability Report",
            "model_type": self.explainer.model_type,
            "num_features": len(self.feature_names) if self.feature_names else "Unknown",
            "global_importance": (
                self.explainer.get_global_importance(self.X_test) if self.X_test is not None else {}
            ),
        }

        # Download as JSON
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="📥 Download JSON Report",
            data=report_json,
            file_name="shap_report.json",
            mime="application/json",
        )


def create_shap_component(
    model: Any = None,
    X_train: Any = None,
    X_test: Any = None,
    feature_names: Optional[List[str]] = None,
) -> SHAPDashboard:
    """
    Factory function to create SHAP dashboard component.

    Args:
        model: Trained model
        X_train: Training data
        X_test: Test data
        feature_names: Feature names

    Returns:
        Configured SHAPDashboard instance
    """
    return SHAPDashboard(model=model, X_train=X_train, X_test=X_test, feature_names=feature_names)


# Standalone demo
if __name__ == "__main__":
    st = _get_streamlit()
    if st is not None:
        dashboard = SHAPDashboard()
        dashboard.render()
