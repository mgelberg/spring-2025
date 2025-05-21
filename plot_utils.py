import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Union, Dict
from datetime import datetime

__all__ = [
    'plot_city_trends',
    'calculate_streams_per_listener',
    'complete_timeseries_data',
    'analyze_adoption_patterns',
    'display_adoption_results'
]

def plot_city_trends(
    data: pd.DataFrame,
    y_column: str,
    title: str = None,
    y_label: str = None,
    cities: Optional[List[str]] = None,
    date_column: str = 'week',
    song_column: str = 'song',
    city_column: str = 'city',
    style: str = 'Solarize_Light2',
    figure_size: Dict[str, float] = {'height': 5, 'aspect': 2.5},
    annotation_offset: Dict[str, int] = {'x': 150, 'y': -40},
    date_tick_interval: int = 8,
    peak_annotation_format: Optional[str] = None
) -> None:
    """
    Create trend line plots for each city showing song performance over time.
    
    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame containing the time series data
    y_column : str
        Column name for the metric to plot (e.g., 'total_streams', 'listeners')
    title : str, optional
        Main title for the plot
    y_label : str, optional
        Label for y-axis (defaults to y_column if not provided)
    cities : List[str], optional
        List of cities to include (defaults to all cities if not provided)
    date_column : str, default='week'
        Column name containing dates
    song_column : str, default='song'
        Column name containing song names
    city_column : str, default='city'
        Column name containing city names
    style : str, default='Solarize_Light2'
        Matplotlib style to use
    figure_size : Dict[str, float]
        Dictionary with 'height' and 'aspect' ratio for the plot
    annotation_offset : Dict[str, int]
        Dictionary with 'x' and 'y' offset for peak annotations
    date_tick_interval : int, default=8
        Interval for x-axis date ticks
    peak_annotation_format : str, optional
        Custom format string for peak annotations. Use {song}, {date}, and {value}
        placeholders. Default: "{song}\\n{date}\\n{value:,.0f} {metric}"
    
    Returns:
    --------
    None
        Displays the plot using plt.show()
    """
    # Filter cities if specified
    if cities:
        data = data[data[city_column].isin(cities)]
    
    plt.style.use(style)

    # Create FacetGrid (reverted to original)
    g = sns.FacetGrid(
        data,
        col=city_column,
        col_wrap=1,
        height=figure_size['height'],
        aspect=figure_size['aspect'],
        sharey=False
    )
    
    # Plot the data using sns.lineplot (reverted to original)
    g.map_dataframe(
        sns.lineplot,
        x=date_column,
        y=y_column,
        hue=song_column,
        markers=True # Original had markers=True
    )
    
    # Set labels
    g.set_axis_labels(date_column.capitalize(), y_label or y_column.replace('_', ' ').title())
    g.set_titles('{col_name}') # This sets the city name as the title for each subplot
    
    # Set main title
    if title:
        plt.suptitle(title, y=1.02, fontsize=20)
    
    # Get unique dates and select intervals (reverted to simpler version)
    unique_dates = sorted(data[date_column].dropna().unique())
    if not unique_dates: # Handle case with no valid dates for ticks
        selected_dates = []
    else:
        # Ensure date_tick_interval is at least 1 and not out of bounds
        actual_interval = max(1, date_tick_interval)
        if len(unique_dates) <= actual_interval: # If too few dates, show all of them or just the first
            selected_dates = unique_dates
        else:
            selected_dates = unique_dates[::actual_interval]
            # Optionally, ensure the last date is included if the interval skips it and there are multiple ticks
            if len(selected_dates) > 1 and selected_dates[-1] != unique_dates[-1] and unique_dates[-1] not in selected_dates:
                selected_dates.append(unique_dates[-1])
            selected_dates = sorted(list(set(selected_dates))) # Ensure uniqueness and order if last was added

    # Default peak annotation format if not provided
    if not peak_annotation_format:
        peak_annotation_format = "{song}\\n{date}\\n{value:,.0f} {metric}"
    
    # Format each subplot
    for ax in g.axes.flat:
        city_title = ax.get_title() # Get city from FacetGrid title (e.g. "city = New York")
        # If FacetGrid sets title like "city_column = value", extract value:
        if '=' in city_title:
            city = city_title.split('=', 1)[1].strip()
        else:
            city = city_title # Fallback if title is just the city name
        ax.set_title(city) # Set the clean city name

        if selected_dates:
            ax.set_xticks(selected_dates)
            try:
                formatted_dates = [pd.to_datetime(date).strftime('%Y-%m-%d') for date in selected_dates]
                ax.set_xticklabels(formatted_dates, rotation=45, ha='right')
            except Exception as e:
                # print(f"Warning: Could not format dates for x-axis labels in city {city}: {e}")
                ax.set_xticklabels([]) 
        else:
            ax.set_xticks([]) # No dates, no ticks
            ax.set_xticklabels([])

        ax.grid(True, alpha=0.3)
        
        # Annotation logic
        current_city_data = data[data[city_column] == city]
        if not current_city_data.empty and not current_city_data[y_column].dropna().empty:
            peak_idx = current_city_data[y_column].idxmax()
            highest_peak_info = current_city_data.loc[peak_idx]
            
            annotation_text = peak_annotation_format.format(
                song=highest_peak_info.get(song_column, 'N/A'),
                date=pd.to_datetime(highest_peak_info[date_column]).strftime('%Y-%m-%d'),
                value=highest_peak_info[y_column],
                metric=y_column.replace('_', ' ')
            )
            
            ax.annotate(
                annotation_text,
                xy=(highest_peak_info[date_column], highest_peak_info[y_column]),
                xytext=(annotation_offset['x'], annotation_offset['y']),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='-', color='gray', lw=1.5, alpha=0.7)
            )
    
    g.add_legend(title=song_column.replace('_', ' ').title(), bbox_to_anchor=(1.02, 0.5), loc='center left')
    plt.tight_layout(rect=[0, 0, 0.9, 1]) # Keep adjusted rect for legend if it helps
    plt.show()

def calculate_streams_per_listener(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate streams per listener metric from the data.
    
    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame containing 'streams' and 'listeners' columns
    
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with new 'streams_per_listener' column
    """
    result = data.copy()
    result['streams_per_listener'] = result['streams'] / result['listeners']
    return result

def complete_timeseries_data(
    data: pd.DataFrame,
    date_column: str,
    value_columns: Union[str, List[str]],
    grouping_columns: List[str],
    fill_value: Union[int, float, Dict[str, Union[int, float]]] = 0
) -> pd.DataFrame:
    """
    Complete a timeseries dataset by filling in missing combinations with a specified value.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Input DataFrame containing the timeseries data
    date_column : str
        Name of the column containing dates/timestamps
    value_columns : Union[str, List[str]]
        Column(s) containing the values to be filled. Can be a single column name
        or a list of column names
    grouping_columns : List[str]
        List of columns to group by (e.g., ['song', 'city'])
    fill_value : Union[int, float, Dict[str, Union[int, float]]], default=0
        Value to use for filling missing data. Can be:
        - A single value (applied to all value_columns)
        - A dictionary mapping column names to fill values
    
    Returns:
    --------
    pd.DataFrame
        Completed DataFrame with all combinations and filled values
    
    Example:
    --------
    >>> df = complete_timeseries_data(
    ...     data=result,
    ...     date_column='week',
    ...     value_columns=['total_streams', 'listeners'],
    ...     grouping_columns=['song', 'city'],
    ...     fill_value={'total_streams': 0, 'listeners': 0}
    ... )
    """
    # Convert value_columns to list if it's a string
    if isinstance(value_columns, str):
        value_columns = [value_columns]
    
    # Standardize fill_value to a dictionary
    if not isinstance(fill_value, dict):
        fill_value = {col: fill_value for col in value_columns}
    
    # Get all unique values for each dimension
    unique_values = {
        date_column: sorted(data[date_column].unique()),
        **{col: sorted(data[col].unique()) for col in grouping_columns}
    }
    
    # Create a complete index with all combinations
    complete_index = pd.MultiIndex.from_product(
        [unique_values[col] for col in [date_column] + grouping_columns],
        names=[date_column] + grouping_columns
    )
    
    # Set the index, reindex with all combinations, and fill missing values
    result = data.set_index([date_column] + grouping_columns).copy()
    
    # Reindex and fill each value column with its specified fill value
    for col in value_columns:
        result[col] = result[col].reindex(complete_index).fillna(fill_value.get(col, 0))
    
    # Reset the index to get back to a regular dataframe
    result = result.reset_index()
    
    return result

# Example usage (commented out):
'''
# Basic usage with default parameters
plot_city_trends(
    data=df,
    y_column='total_streams',
    title='Streams over Time in Top Cities'
)

# Custom usage with specific cities and formatting
plot_city_trends(
    data=df,
    y_column='streams_per_listener',
    title='Engagement by City',
    y_label='Average Streams per Listener',
    cities=['New York', 'Los Angeles', 'Chicago'],
    peak_annotation_format="{song}\n{date}\nPeak: {value:.2f} streams/listener"
)
'''

def analyze_adoption_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyze adoption patterns for songs across cities.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the song data with columns:
        - city: str
        - previous_period: float
        - current_period: float
        - %_change: float
        - week: datetime
        - song: str
        - song_id: str
        - measure: str ('plays' or 'listeners')
        - level: str
        - grouping: str
        - period_type: str
    
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary containing:
        - 'city_adoption': Detailed adoption data for each city-song combination
        - 'city_summary': Summary metrics for each city
        - 'category_metrics': Summary metrics for each adoption category
    """
    # Debug print to see actual columns
    print("DataFrame columns:", df.columns.tolist())
    
    # Filter out monthly and artist-level data
    df = df[~df['song'].str.contains('artist level', case=False, na=False)]
    df = df[df['grouping'] == 'city']
    
    # Convert week to datetime if not already
    df['week'] = pd.to_datetime(df['week'])
    
    # Initialize DataFrame to store city adoption metrics
    city_adoption = pd.DataFrame()
    
    # Get first activity date for each song (this will be treated as release date)
    song_release_dates = df[df['current_period'] > 0].groupby('song')['week'].min()
    
    print(f"\nAnalyzing {len(song_release_dates)} songs")
    print("\nSongs being analyzed:")
    for song in song_release_dates.index:
        print(f"- {song}")
    
    for city in df['city'].unique():
        if city == 'All Cities':  # Skip aggregate data
            continue
            
        city_data = df[df['city'] == city]
        
        # Analyze adoption for each song
        for song in df['song'].unique():
            song_city_data = city_data[city_data['song'] == song]
            
            if song_city_data.empty:
                continue
                
            release_date = song_release_dates[song]
            
            # Find first activity for this city and song
            song_city_activity = song_city_data[song_city_data['current_period'] > 0]
            if song_city_activity.empty:
                continue
                
            first_activity = song_city_activity['week'].min()
            last_activity = song_city_activity['week'].max()
            
            # Calculate weeks from release to first activity
            weeks_to_adopt = (first_activity - release_date).days / 7
            
            # Calculate active weeks and total weeks since adoption
            active_weeks = song_city_activity['week'].nunique()
            total_weeks = (last_activity - first_activity).days / 7 + 1 if first_activity else 0
            
            # Calculate engagement metrics
            total_streams = song_city_data[song_city_data['measure'].str.lower() == 'plays']['current_period'].sum()
            total_listeners = song_city_data[song_city_data['measure'].str.lower() == 'listeners']['current_period'].sum()
            
            # Calculate consistency score
            consistency = (active_weeks / total_weeks) * 100 if total_weeks > 0 else 0
            
            # Add to city_adoption DataFrame
            city_adoption = pd.concat([city_adoption, pd.DataFrame({
                'city': [city],
                'song': [song],
                'release_date': [release_date],
                'first_activity': [first_activity],
                'weeks_to_adopt': [weeks_to_adopt],
                'total_streams': [total_streams],
                'total_listeners': [total_listeners],
                'active_weeks': [active_weeks],
                'consistency_score': [consistency]
            })], ignore_index=True)
    
    # Calculate average adoption speed and consistency for each city across all songs
    city_summary = city_adoption.groupby('city').agg({
        'weeks_to_adopt': 'mean',
        'consistency_score': 'mean',
        'total_streams': 'sum',
        'total_listeners': 'sum',
        'song': 'count'  # Count how many songs each city engaged with
    }).reset_index()
    
    # Rename the song count column
    city_summary = city_summary.rename(columns={'song': 'songs_engaged'})
    
    # Categorize cities based on average adoption speed
    percentile_33 = city_summary['weeks_to_adopt'].quantile(0.33)
    percentile_67 = city_summary['weeks_to_adopt'].quantile(0.67)
    
    def categorize_city(row):
        if row['weeks_to_adopt'] <= percentile_33:
            return 'Early Adopter'
        elif row['weeks_to_adopt'] <= percentile_67:
            return 'Mid Adopter'
        else:
            return 'Late Bloomer'
    
    city_summary['category'] = city_summary.apply(categorize_city, axis=1)
    
    # Calculate category metrics
    category_metrics = city_summary.groupby('category').agg({
        'total_streams': 'mean',
        'total_listeners': 'mean',
        'consistency_score': 'mean',
        'weeks_to_adopt': 'mean',
        'songs_engaged': 'mean',
        'city': 'count'
    }).round(2)
    
    return {
        'city_adoption': city_adoption,
        'city_summary': city_summary,
        'category_metrics': category_metrics
    }

def display_adoption_results(results: Dict[str, pd.DataFrame]) -> None:
    """
    Display the results from analyze_adoption_patterns in a clear, formatted way.
    
    Parameters:
    -----------
    results : Dict[str, pd.DataFrame]
        Dictionary containing:
        - 'city_adoption': Detailed adoption data for each city-song combination
        - 'city_summary': Summary metrics for each city
        - 'category_metrics': Summary metrics for each adoption category
    """
    # Filter out cities with less than 100 lifetime streams
    city_summary = results['city_summary'][results['city_summary']['total_streams'] >= 50].copy()
    
    # Recalculate category metrics with filtered data
    category_metrics = city_summary.groupby('category').agg({
        'total_streams': 'mean',
        'total_listeners': 'mean',
        'consistency_score': 'mean',
        'weeks_to_adopt': 'mean',
        'songs_engaged': 'mean',
        'city': 'count'
    }).round(2)
    
    # 1. Display Metric Explanations
    print("\n=== Metric Explanations ===")
    print("\nConsistency Score:")
    print("• Calculated as: (Number of Active Weeks / Total Weeks Since First Activity) × 100")
    print("• Active Week: A week where the song had any streams")
    print("• Higher scores indicate more consistent engagement over time")
    print("• Example: A score of 75% means the city was active 75% of the weeks since they first played the song")
    
    print("\nWeeks to Adopt:")
    print("• Measures how quickly a city starts playing a song after its release")
    print("• Calculated as: (First Activity Date - Song Release Date) in weeks")
    print("• Lower numbers indicate faster adoption")
    print("• Example: 2.5 weeks means the city started playing the song 2.5 weeks after release")
    
    print("\nNote: Analysis excludes cities with fewer than 50 lifetime streams")
    
    # 2. Display Category Overview
    print("\n=== City Categories Overview ===")
    
    # Format the metrics for better readability
    formatted_metrics = category_metrics.copy()
    formatted_metrics['total_streams'] = formatted_metrics['total_streams'].apply(lambda x: f"{x:,.0f}")
    formatted_metrics['total_listeners'] = formatted_metrics['total_listeners'].apply(lambda x: f"{x:,.0f}")
    formatted_metrics['consistency_score'] = formatted_metrics['consistency_score'].apply(lambda x: f"{x:.1f}%")
    formatted_metrics['weeks_to_adopt'] = formatted_metrics['weeks_to_adopt'].apply(lambda x: f"{x:.1f}")
    formatted_metrics['songs_engaged'] = formatted_metrics['songs_engaged'].apply(lambda x: f"{x:.1f}")
    formatted_metrics['city'] = formatted_metrics['city'].apply(lambda x: f"{x:.0f}")
    
    print("\nCategory Statistics:")
    print(formatted_metrics)
    
    # 3. Display Top Cities by Category
    print("\n=== Top Cities by Category ===")
    
    for category in ['Early Adopter', 'Mid Adopter', 'Late Bloomer']:
        category_cities = city_summary[city_summary['category'] == category]
        top_cities = category_cities.nlargest(3, 'consistency_score')
        
        print(f"\nTop {category} Cities:")
        for _, city in top_cities.iterrows():
            print(f"- {city['city']}:")
            print(f"  • Consistency Score: {city['consistency_score']:.1f}%")
            print(f"  • Average Weeks to Adopt: {city['weeks_to_adopt']:.1f}")
            print(f"  • Total Songs Engaged: {city['songs_engaged']:.0f}")
            print(f"  • Total Streams: {city['total_streams']:,.0f}")
    
    # 4. Create visualizations
    plt.figure(figsize=(15, 10))
    
    # 4.1 Adoption Speed vs Consistency Plot
    plt.subplot(2, 1, 1)
    sns.scatterplot(data=city_summary, 
                    x='weeks_to_adopt',
                    y='consistency_score',
                    hue='category',
                    size='songs_engaged',
                    sizes=(50, 400),
                    alpha=0.6)
    
    plt.title('City Adoption Patterns: Speed vs Consistency\n(Cities with 50+ Streams)')
    plt.xlabel('Average Weeks Until First Activity')
    plt.ylabel('Consistency Score (%)')
    
    # Add city labels for points with high engagement
    for idx, row in city_summary[city_summary['songs_engaged'] >= city_summary['songs_engaged'].quantile(0.75)].iterrows():
        plt.annotate(row['city'], 
                    (row['weeks_to_adopt'], row['consistency_score']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.7)
    
    # 4.2 Category Distribution Plot
    plt.subplot(2, 1, 2)
    category_counts = city_summary['category'].value_counts()
    sns.barplot(x=category_counts.index, y=category_counts.values)
    plt.title('Distribution of Cities Across Categories\n(Cities with 50+ Streams)')
    plt.xlabel('Category')
    plt.ylabel('Number of Cities')
    
    # Add value labels on top of bars
    for i, v in enumerate(category_counts.values):
        plt.text(i, v, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()
    
    # 5. Display Song Adoption Stats
    print("\n=== Song Adoption Statistics ===")
    # Filter city_adoption to match filtered city_summary
    active_cities = city_summary['city'].unique()
    filtered_city_adoption = results['city_adoption'][
        results['city_adoption']['city'].isin(active_cities)
    ]
    
    song_stats = filtered_city_adoption.groupby('song').agg({
        'weeks_to_adopt': 'mean',
        'consistency_score': 'mean',
        'city': 'count'
    }).round(2)
    
    song_stats = song_stats.rename(columns={
        'weeks_to_adopt': 'avg_weeks_to_adopt',
        'consistency_score': 'avg_consistency',
        'city': 'num_cities'
    })
    
    # Sort by number of cities and average consistency
    top_songs = song_stats.sort_values(['num_cities', 'avg_consistency'], ascending=[False, False]).head(5)
    
    print("\nTop 5 Most Widely Adopted Songs (In Cities with 50+ Streams):")
    if not top_songs.empty:
        # Prepare DataFrame for table display
        display_top_songs = top_songs.copy()
        display_top_songs['avg_consistency'] = display_top_songs['avg_consistency'].apply(lambda x: f"{x:.1f}%")
        # Reset index to make 'song' a column for better display with to_string()
        print(display_top_songs.reset_index().to_string(index=False))
    else:
        print("  No songs found matching the criteria for top adopted songs.")