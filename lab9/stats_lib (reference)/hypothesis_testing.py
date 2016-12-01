import numpy as np
import matplotlib.pyplot as plt


class HypothesisTest():

    def __init__(self, test, H0, H1, one_tailed=True, alpha=0.05):
        """Constructor for the Hypothesis Test class"""
        pass

    # Define class methods as necessary


class TestStatistic():

    def __init__(self, point_estimate,
                 null_distribution=None, alt_distribution=None):
        """Constructor for the TestStatistic Test class"""
        pass

    def set_null_distribution(self, distribution):
        """Establish the distribution of the Test Statistic under H0"""
        pass

    def set_alt_distribution(self, distribution):
        """Establish the distribution of the Test Statistic under H1"""
        pass

    def plot_pdf(self, distribution='null'):
        """Plot the Probability Density function of the appropriate distribution"""
        pass
