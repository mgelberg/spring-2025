import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional
import numpy as np

def plot_city_trends(df: pd.DataFrame, 
                    cities: List[str], 
                    metric: str = 'current_period',
                    title: str = 'City Trends Over Time',
                    figsize: tuple = (12, 6)) -> None:
    """
    Plot trends for selected cities over time.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the trend data
    cities : List[str]
        List of cities to plot
    metric : str
        Column name for the metric to plot
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    for city in cities:
        city_data = df[df['city'] == city]
        plt.plot(city_data['week'], city_data[metric], label=city, marker='o')
    
    plt.title(title)
    plt.xlabel('Week')
    plt.ylabel(metric.replace('_', ' ').title())
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def calculate_streams_per_listener(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate streams per listener ratio for each city and week.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing streams and listener data
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with streams per listener ratio
    """
    # Pivot the data to get streams and listeners in separate columns
    pivot_df = df.pivot_table(
        index=['city', 'week'],
        columns='measure',
        values='current_period',
        aggfunc='sum'
    ).reset_index()
    
    # Calculate streams per listener
    pivot_df['streams_per_listener'] = pivot_df['plays'] / pivot_df['listeners']
    
    return pivot_df

def complete_timeseries_data(df: pd.DataFrame, 
                           date_col: str = 'week',
                           group_cols: List[str] = ['city', 'song', 'measure']) -> pd.DataFrame:
    """
    Complete the time series data by filling in missing dates with zeros.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the time series data
    date_col : str
        Name of the date column
    group_cols : List[str]
        List of columns to group by
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with completed time series
    """
    # Convert date column to datetime if not already
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Get all unique dates
    all_dates = pd.date_range(df[date_col].min(), df[date_col].max(), freq='W')
    
    # Create a complete index
    complete_index = pd.MultiIndex.from_product(
        [df[col].unique() for col in group_cols] + [all_dates],
        names=group_cols + [date_col]
    )
    
    # Reindex the DataFrame
    df_complete = df.set_index(group_cols + [date_col]).reindex(complete_index)
    
    # Fill missing values with 0
    df_complete = df_complete.fillna(0)
    
    return df_complete.reset_index()

def plot_streams_per_listener_trends(df: pd.DataFrame,
                                   cities: List[str],
                                   figsize: tuple = (12, 6)) -> None:
    """
    Plot streams per listener trends for selected cities.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the trend data
    cities : List[str]
        List of cities to plot
    figsize : tuple
        Figure size (width, height)
    """
    # Calculate streams per listener
    ratio_df = calculate_streams_per_listener(df)
    
    plt.figure(figsize=figsize)
    
    for city in cities:
        city_data = ratio_df[ratio_df['city'] == city]
        plt.plot(city_data['week'], 
                city_data['streams_per_listener'], 
                label=city, 
                marker='o')
    
    plt.title('Streams per Listener Trends')
    plt.xlabel('Week')
    plt.ylabel('Streams per Listener')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_city_comparison(df: pd.DataFrame,
                        cities: List[str],
                        metric: str = 'current_period',
                        title: str = 'City Comparison',
                        figsize: tuple = (10, 6)) -> None:
    """
    Create a bar plot comparing cities for a specific metric.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the comparison data
    cities : List[str]
        List of cities to compare
    metric : str
        Column name for the metric to compare
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    # Filter data for selected cities
    city_data = df[df['city'].isin(cities)]
    
    # Create bar plot
    sns.barplot(data=city_data, x='city', y=metric)
    
    plt.title(title)
    plt.xlabel('City')
    plt.ylabel(metric.replace('_', ' ').title())
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_metric_distribution(df: pd.DataFrame,
                           metric: str = 'current_period',
                           title: str = 'Metric Distribution',
                           figsize: tuple = (10, 6)) -> None:
    """
    Create a distribution plot for a specific metric.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the metric data
    metric : str
        Column name for the metric to plot
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    sns.histplot(data=df, x=metric, bins=30)
    
    plt.title(title)
    plt.xlabel(metric.replace('_', ' ').title())
    plt.ylabel('Count')
    plt.tight_layout()
    plt.show()

def plot_correlation_matrix(df: pd.DataFrame,
                          metrics: List[str],
                          title: str = 'Metric Correlations',
                          figsize: tuple = (10, 8)) -> None:
    """
    Create a correlation matrix plot for selected metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the metrics
    metrics : List[str]
        List of metric columns to correlate
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    # Calculate correlation matrix
    corr_matrix = df[metrics].corr()
    
    # Create heatmap
    sns.heatmap(corr_matrix, 
                annot=True, 
                cmap='coolwarm', 
                center=0,
                fmt='.2f')
    
    plt.title(title)
    plt.tight_layout()
    plt.show()

def plot_rolling_average(df: pd.DataFrame,
                        cities: List[str],
                        metric: str = 'current_period',
                        window: int = 4,
                        title: str = 'Rolling Average Trends',
                        figsize: tuple = (12, 6)) -> None:
    """
    Plot rolling average trends for selected cities.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the trend data
    cities : List[str]
        List of cities to plot
    metric : str
        Column name for the metric to plot
    window : int
        Window size for rolling average
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    for city in cities:
        city_data = df[df['city'] == city].copy()
        city_data['rolling_avg'] = city_data[metric].rolling(window=window).mean()
        plt.plot(city_data['week'], 
                city_data['rolling_avg'], 
                label=city, 
                marker='o')
    
    plt.title(f'{title} (Window Size: {window} weeks)')
    plt.xlabel('Week')
    plt.ylabel(f'{metric.replace("_", " ").title()} (Rolling Average)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_metric_by_category(df: pd.DataFrame,
                          category_col: str,
                          metric: str = 'current_period',
                          title: str = 'Metric by Category',
                          figsize: tuple = (10, 6)) -> None:
    """
    Create a box plot showing metric distribution by category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the metric data
    category_col : str
        Column name for the category
    metric : str
        Column name for the metric to plot
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    sns.boxplot(data=df, x=category_col, y=metric)
    
    plt.title(title)
    plt.xlabel(category_col.replace('_', ' ').title())
    plt.ylabel(metric.replace('_', ' ').title())
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_metric_trends_by_category(df: pd.DataFrame,
                                 category_col: str,
                                 metric: str = 'current_period',
                                 title: str = 'Metric Trends by Category',
                                 figsize: tuple = (12, 6)) -> None:
    """
    Plot metric trends for each category over time.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the trend data
    category_col : str
        Column name for the category
    metric : str
        Column name for the metric to plot
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    for category in df[category_col].unique():
        category_data = df[df[category_col] == category]
        plt.plot(category_data['week'], 
                category_data[metric], 
                label=category, 
                marker='o')
    
    plt.title(title)
    plt.xlabel('Week')
    plt.ylabel(metric.replace('_', ' ').title())
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_metric_comparison(df: pd.DataFrame,
                         metrics: List[str],
                         title: str = 'Metric Comparison',
                         figsize: tuple = (12, 6)) -> None:
    """
    Create a line plot comparing multiple metrics over time.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the metrics
    metrics : List[str]
        List of metric columns to compare
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    for metric in metrics:
        plt.plot(df['week'], 
                df[metric], 
                label=metric.replace('_', ' ').title(), 
                marker='o')
    
    plt.title(title)
    plt.xlabel('Week')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
def plot_metric_heatmap(df: pd.DataFrame,
                       x_col: str,
                       y_col: str,
                       metric: str = 'current_period',
                       title: str = 'Metric Heatmap',
                       figsize: tuple = (10, 8)) -> None:
    """
    Create a heatmap showing metric values across two dimensions.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the metric data
    x_col : str
        Column name for x-axis categories
    y_col : str
        Column name for y-axis categories
    metric : str
        Column name for the metric to plot
    title : str
        Title for the plot
    figsize : tuple
        Figure size (width, height)
    """
    plt.figure(figsize=figsize)
    
    # Create pivot table
    pivot_df = df.pivot_table(
        values=metric,
        index=y_col,
        columns=x_col,
        aggfunc='mean'
    )
    
    # Create heatmap
    sns.heatmap(pivot_df, 
                annot=True, 
                cmap='YlOrRd', 
                fmt='.2f')
    
    plt.title(title)
    plt.tight_layout()
    plt.show()