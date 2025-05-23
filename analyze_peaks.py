import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plot_utils import plot_city_trends, complete_timeseries_data
from datetime import datetime
from config import songs_to_scrape
from file_utils import (
    ensure_directory_exists,
    ANALYSIS_OUTPUT_DIR
)
from parsed_data_loader import load_and_prepare_data
import os
import numpy as np

def get_song_release_date(song_id):
    """Get the release date for a song from config."""
    # Convert song_id to string for comparison
    song_id = str(song_id)
    for song in songs_to_scrape:
        if song['id'] == song_id:
            return datetime.strptime(song['release_date'], '%Y%m%d')
    return None

def calculate_city_metrics(streams_data, listeners_data):
    """
    Calculate comprehensive city-level metrics including peak and adoption patterns.
    Only considers the first 12 weeks after release for each song.
    
    Parameters:
    -----------
    streams_data : pd.DataFrame
        DataFrame containing the streams data
    listeners_data : pd.DataFrame
        DataFrame containing the listeners data
    
    Returns:
    --------
    tuple
        (city_metrics, song_metrics) where:
        - city_metrics: DataFrame with aggregated city-level metrics
        - song_metrics: DataFrame with individual song-level metrics
    """
    # Initialize results lists
    city_metrics_list = []
    song_metrics_list = []
    
    for city in streams_data['city'].unique():
        if city == 'All Cities':  # Skip aggregate data
            continue
            
        # Get city-specific data
        city_streams = streams_data[streams_data['city'] == city]
        city_listeners = listeners_data[listeners_data['city'] == city]
        
        # Calculate weekly streams per listener for the city
        weekly_metrics = []
        for week in city_streams['week'].unique():
            week_data = city_streams[city_streams['week'] == week]
            week_streams = week_data['current_period'].sum()
            week_listeners = city_listeners[city_listeners['week'] == week]['current_period'].max()
            if week_listeners > 0:
                ratio = week_streams / week_listeners
                weekly_metrics.append(ratio)
        
        avg_weekly_streams_per_listener = sum(weekly_metrics) / len(weekly_metrics) if weekly_metrics else 0
        
        # Calculate metrics for each song
        time_to_peak_list = []
        first_week_peaks = 0
        total_songs = 0
        missing_release_date = 0
        still_growing = 0
        total_streams = 0
        total_listeners = 0
        active_weeks = 0
        total_weeks = 0
        
        for song in city_streams['song'].unique():
            # Create a proper copy of the song data
            song_data = city_streams[city_streams['song'] == song].copy()
            if not song_data.empty:
                total_songs += 1
                
                # Get song ID and release date
                song_id = song_data['song_id'].iloc[0]
                release_date = get_song_release_date(song_id)
                if release_date is None:
                    missing_release_date += 1
                    continue
                
                # Filter to only include first 12 weeks after release
                song_data = song_data[song_data['week'] <= release_date + pd.Timedelta(weeks=12)]
                if song_data.empty:
                    continue
                
                # Calculate peak metrics
                peak_date = song_data.loc[song_data['current_period'].idxmax()]['week']
                peak_streams = song_data['current_period'].max()
                latest_week = song_data['week'].max()
                
                # Only consider a song as still growing if:
                # 1. Peak is in the most recent week AND
                # 2. We're still within 12 weeks of release
                is_still_growing = (peak_date == latest_week) and (latest_week <= release_date + pd.Timedelta(weeks=12))
                weeks_to_peak = (peak_date - release_date).days / 7 if not is_still_growing else None
                
                # Calculate adoption metrics
                first_activity = song_data[song_data['current_period'] > 0]['week'].min()
                weeks_to_adopt = (first_activity - release_date).days / 7 if first_activity else None
                
                # Calculate engagement metrics
                song_streams = song_data['current_period'].sum()
                total_streams += song_streams
                
                # Get listener data
                artist_name = song.split(' - ')[0] if ' - ' in song else song
                song_listener_data = city_listeners[city_listeners['song'].str.contains(artist_name, case=False, na=False)]
                peak_listeners = song_listener_data['current_period'].max() if not song_listener_data.empty else 0
                total_listeners += peak_listeners
                
                # Calculate consistency metrics
                active_weeks += song_data[song_data['current_period'] > 0]['week'].nunique()
                total_weeks += song_data['week'].nunique()
                
                # Add to song metrics list
                song_metrics_list.append({
                    'city': city,
                    'song': song,
                    'song_id': song_id,
                    'release_date': release_date.strftime('%Y-%m-%d'),
                    'peak_date': peak_date.strftime('%Y-%m-%d'),
                    'peak_streams': peak_streams,
                    'peak_listeners': peak_listeners,
                    'weeks_to_peak': round(weeks_to_peak, 1) if weeks_to_peak is not None else None,
                    'weeks_to_adopt': round(weeks_to_adopt, 1) if weeks_to_adopt is not None else None,
                    'is_still_growing': is_still_growing,
                    'peaked_first_week': weeks_to_peak == 0 if weeks_to_peak is not None else False,
                    'total_streams': song_streams
                })
                
                if is_still_growing:
                    still_growing += 1
                elif weeks_to_peak == 0:
                    first_week_peaks += 1
                    time_to_peak_list.append(0)
                elif weeks_to_peak is not None and weeks_to_peak > 0:
                    time_to_peak_list.append(weeks_to_peak)
        
        # Calculate average metrics
        avg_time_to_peak = sum(time_to_peak_list) / len(time_to_peak_list) if time_to_peak_list else None
        avg_weeks_to_peak = round(avg_time_to_peak, 1) if avg_time_to_peak is not None else None
        consistency_score = (active_weeks / total_weeks * 100) if total_weeks > 0 else 0
        
        # Add to city metrics list
        city_metrics_list.append({
            'city': city,
            'avg_weeks_to_peak': avg_weeks_to_peak,
            'peak_streams': city_streams['current_period'].max() if not city_streams.empty else 0,
            'peak_weekly_listeners': city_listeners['current_period'].max() if not city_listeners.empty else 0,
            'songs_analyzed': total_songs,
            'songs_peaked_first_week': first_week_peaks,
            'pct_peaked_first_week': round((first_week_peaks / total_songs * 100) if total_songs > 0 else 0, 1),
            'songs_missing_release_date': missing_release_date,
            'songs_still_growing': still_growing,
            'total_streams': total_streams,
            'consistency_score': round(consistency_score, 1),
            'avg_weekly_streams_per_listener': round(avg_weekly_streams_per_listener, 1),
            'avg_weeks_to_adopt': round(sum(m['weeks_to_adopt'] for m in song_metrics_list if m['city'] == city and m['weeks_to_adopt'] is not None) / 
                                      sum(1 for m in song_metrics_list if m['city'] == city and m['weeks_to_adopt'] is not None), 1) 
                                      if any(m['city'] == city and m['weeks_to_adopt'] is not None for m in song_metrics_list) else None
        })
    
    # Create DataFrames from lists
    city_metrics = pd.DataFrame(city_metrics_list)
    song_metrics = pd.DataFrame(song_metrics_list)
    
    # Categorize cities based on adoption speed
    percentile_33 = city_metrics['avg_weeks_to_adopt'].quantile(0.33)
    percentile_67 = city_metrics['avg_weeks_to_adopt'].quantile(0.67)
    
    def categorize_city(row):
        if row['avg_weeks_to_adopt'] <= percentile_33:
            return 'Early Adopter'
        elif row['avg_weeks_to_adopt'] <= percentile_67:
            return 'Mid Adopter'
        else:
            return 'Late Bloomer'
    
    city_metrics['category'] = city_metrics.apply(categorize_city, axis=1)
    
    # Sort city metrics by peak streams in descending order
    city_metrics = city_metrics.sort_values('peak_streams', ascending=False)
    
    return city_metrics, song_metrics

def export_peak_metrics(city_metrics, song_metrics, output_dir=ANALYSIS_OUTPUT_DIR):
    """
    Export city and song peak metrics to CSV files.
    
    Parameters:
    -----------
    city_metrics : pd.DataFrame
        DataFrame containing city peak metrics
    song_metrics : pd.DataFrame
        DataFrame containing song-level metrics
    output_dir : str
        Directory to save the output files
    """
    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create directory if it doesn't exist
    if output_dir:
        ensure_directory_exists(os.path.join(output_dir, 'dummy.txt'))
    
    try:
        # Export city metrics
        city_filename = f'{output_dir}/city_peak_metrics_{timestamp}.csv'
        city_metrics.to_csv(city_filename, index=False)
        print(f"\n✅ City peak metrics exported to: {city_filename}")
        
        # Export song metrics
        song_filename = f'{output_dir}/song_peak_metrics_{timestamp}.csv'
        song_metrics.to_csv(song_filename, index=False)
        print(f"✅ Song peak metrics exported to: {song_filename}")
    except Exception as e:
        print(f"❌ Error exporting metrics: {str(e)}")

def prepare_weekly_song_data(df, include_artist_level=False):
    """
    Prepare data specifically for weekly song-level analysis.
    This ensures consistent data preparation for song velocity analysis.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw DataFrame containing the song velocity data
    include_artist_level : bool, default False
        Whether to include artist-level data in the analysis
        
    Returns:
    --------
    tuple
        (streams_data, listeners_data) where:
        - streams_data: DataFrame with plays data, properly formatted for weekly song analysis
        - listeners_data: DataFrame with listeners data, properly formatted for weekly song analysis
    """
    # Ensure all column names are lowercase
    df.columns = df.columns.str.lower()
    
    # Filter for weekly data only
    df = df[df['period_type'].str.lower() == 'weekly'].copy()
    
    # Base filter for song-level data
    song_filter = (
        (df['city'].str.lower() != 'all cities')
    )
    
    # Add artist level filter if needed
    if not include_artist_level:
        song_filter = song_filter & (~df['song'].str.lower().str.contains('artist level', case=False, na=False))
    
    # Get streams data
    streams_data = df[
        (df['measure'].str.lower() == 'plays') & 
        song_filter
    ].copy()
    
    # Get listeners data
    listeners_data = df[
        (df['measure'].str.lower() == 'listeners') & 
        song_filter
    ].copy()
    
    # Convert week columns to datetime
    streams_data['week'] = pd.to_datetime(streams_data['week'], format='%Y%m%d')
    listeners_data['week'] = pd.to_datetime(listeners_data['week'], format='%Y%m%d')
    
    return streams_data, listeners_data

def analyze_peaks(df=None, include_artist_level=False):
    """
    Analyze and visualize peak and adoption metrics for cities.
    Only considers the first 12 weeks after release for each song.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
    include_artist_level : bool, default False
        Whether to include artist-level data in the analysis
        
    Returns:
    --------
    tuple
        (city_metrics, song_metrics, category_metrics) where:
        - city_metrics: DataFrame with aggregated city-level metrics
        - song_metrics: DataFrame with individual song-level metrics
        - category_metrics: DataFrame with category-level summary statistics
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                print("ℹ️ Using existing DataFrame from notebook context")
                df = __main__.df
            else:
                print("ℹ️ Loading data from file...")
                df = load_and_prepare_data()
        except Exception:
            print("ℹ️ Loading data from file...")
            df = load_and_prepare_data()
    
    # Prepare data for analysis
    streams_data, listeners_data = prepare_weekly_song_data(df, include_artist_level)
    
    # Calculate city metrics
    city_metrics, song_metrics = calculate_city_metrics(streams_data, listeners_data)
    
    # Filter out cities with low engagement
    city_metrics = city_metrics[city_metrics['total_streams'] >= 50].copy()
    
    # Calculate category metrics
    category_metrics = city_metrics.groupby('category').agg({
        'total_streams': ['count', 'mean'],
        'consistency_score': 'mean',
        'avg_weeks_to_adopt': 'mean'
    }).round(1)
    category_metrics.columns = ['num_cities', 'avg_streams', 'avg_consistency', 'avg_weeks_to_adopt']
    category_metrics = category_metrics.reset_index()
    
    # Print the results
    print("\nCity Metrics Summary (First 12 Weeks After Release):")
    print("=" * 80)
    print(city_metrics.to_string(index=False))
    
    # Print interpretation of metrics
    print("\nInterpretation Notes:")
    print("- All metrics are calculated using only the first 12 weeks after release for each song")
    print("- peak_streams: Highest number of streams in a single week")
    print("- total_streams: Total streams in first 12 weeks")
    print("- peak_listeners: Highest number of listeners in any single week")
    print("- active_cities: Number of cities that have streamed the song")
    print("- avg_streams_per_city: Average streams per active city")
    print("- avg_streams_per_listener: Average streams per peak weekly listener")
    print("- peak_to_total_ratio: Percentage of total streams that occurred at peak")
    print("- retention_rate: Percentage of cities that streamed in last 4 weeks")
    print("- adoption_category: Song's adoption pattern (Quick Adopter, Mid Adopter, Slow Adopter)")
    
    print("\nAvailable DataFrames for Further Analysis:")
    print("- city_metrics: City-level aggregated metrics including adoption patterns and peak behavior")
    print("  • Contains: city name, adoption category, consistency scores, peak metrics, and engagement stats")
    print("- song_metrics: Song-level metrics for each city-song combination")
    print("  • Contains: individual song performance, adoption timing, and peak behavior for each city")
    print("- category_metrics: Summary statistics for each adoption category")
    print("  • Contains: average streams, number of cities, and other aggregated metrics by category")
    
    # Create interactive visualizations using Plotly
    # 1. Adoption Speed vs Consistency Plot
    fig = px.scatter(
        city_metrics,
        x='avg_weeks_to_adopt',
        y='consistency_score',
        color='total_streams',
        size='total_streams',
        hover_name='city',
        custom_data=['consistency_score', 'avg_weeks_to_adopt', 'total_streams', 'category'],
        size_max=30,
        color_continuous_scale=px.colors.sequential.Viridis,
        title='City Adoption Patterns: Speed vs Consistency<br>(Cities with 50+ Streams)'
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Average Weeks Until First Activity',
        yaxis_title='Consistency Score (%)',
        coloraxis_colorbar=dict(
            title='Total Streams',
            tickfont=dict(size=16),
            title_font=dict(size=18)
        ),
        height=800,
        showlegend=False,
        xaxis=dict(
            tickfont=dict(size=16),
            title_font=dict(size=18)
        ),
        yaxis=dict(
            tickfont=dict(size=16),
            title_font=dict(size=18)
        )
    )
    
    # Add hover template
    fig.update_traces(
        marker=dict(
            size=15,
            line=dict(width=1, color='white')
        ),
        hovertemplate="<b>%{hovertext}</b><br>" +
                     "Consistency: %{customdata[0]:.1f}%<br>" +
                     "Weeks to First Stream: %{customdata[1]:.1f}<br>" +
                     "Total Streams: %{customdata[2]:,.0f}<br>" +
                     "Category: %{customdata[3]}<extra></extra>"
    )
    
    # Show the plot
    fig.show()
    
    # 2. Category Distribution Plot
    fig2 = px.bar(
        category_metrics,
        x='category',
        y='num_cities',
        color='category',
        color_discrete_sequence=px.colors.qualitative.Set2,
        title='Distribution of Cities Across Categories<br>(Cities with 50+ Streams)',
        custom_data=['avg_streams']
    )
    
    # Update layout
    fig2.update_layout(
        xaxis_title='Category',
        yaxis_title='Number of Cities',
        showlegend=False,
        height=400,
        margin=dict(t=100),
        yaxis=dict(
            range=[0, category_metrics['num_cities'].max() * 1.2]
        )
    )
    
    # Add value labels and update hover template
    fig2.update_traces(
        texttemplate='%{y}',
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>" +
                     "Number of Cities: %{y}<br>" +
                     "Average Streams per City: %{customdata[0]:,.0f}<extra></extra>"
    )
    
    # Show the plot
    fig2.show()
    
    # Return the DataFrames without displaying them
    return city_metrics.copy(), song_metrics.copy(), category_metrics.copy()

def analyze_song_adoption(df=None, include_artist_level=False):
    """
    Analyze and visualize adoption patterns across all songs.
    Only considers the first 12 weeks after release for each song.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
    include_artist_level : bool, default False
        Whether to include artist-level data in the analysis
        
    Returns:
    --------
    pd.DataFrame
        song_adoption_metrics: DataFrame with song-level adoption metrics
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                print("ℹ️ Using existing DataFrame from notebook context")
                df = __main__.df
            else:
                print("ℹ️ Loading data from file...")
                df = load_and_prepare_data()
        except Exception:
            print("ℹ️ Loading data from file...")
            df = load_and_prepare_data()
    
    # Prepare data for analysis
    streams_data, listeners_data = prepare_weekly_song_data(df, include_artist_level)
    
    # Initialize results list
    song_adoption_list = []
    
    # Calculate metrics for each song
    for song in streams_data['song'].unique():
        song_data = streams_data[streams_data['song'] == song].copy()
        if song_data.empty:
            continue
            
        # Get song ID and release date
        song_id = song_data['song_id'].iloc[0]
        release_date = get_song_release_date(song_id)
        if release_date is None:
            continue
        
        # Filter to only include first 12 weeks after release
        song_data = song_data[song_data['week'] <= release_date + pd.Timedelta(weeks=12)]
        if song_data.empty:
            continue
        
        # Calculate peak metrics
        peak_date = song_data.loc[song_data['current_period'].idxmax()]['week']
        peak_streams = song_data['current_period'].max()
        latest_week = song_data['week'].max()
        
        # Calculate adoption metrics
        first_activity = song_data[song_data['current_period'] > 0]['week'].min()
        weeks_to_adopt = (first_activity - release_date).days / 7 if first_activity else None
        
        # Calculate engagement metrics
        total_streams = song_data['current_period'].sum()
        total_cities = song_data['city'].nunique()
        active_cities = song_data[song_data['current_period'] > 0]['city'].nunique()
        
        # Get listener data for this song
        song_listener_data = listeners_data[listeners_data['song'] == song].copy()
        # Filter listener data to same 12-week window
        song_listener_data = song_listener_data[song_listener_data['week'] <= release_date + pd.Timedelta(weeks=12)]
        peak_weekly_listeners = song_listener_data['current_period'].max() if not song_listener_data.empty else 0
        
        # Calculate average weekly streams per listener
        weekly_metrics = []
        weekly_listeners = []
        for week in song_data['week'].unique():
            week_data = song_data[song_data['week'] == week]
            week_streams = week_data['current_period'].sum()
            week_listeners = song_listener_data[song_listener_data['week'] == week]['current_period'].max()
            weekly_listeners.append(week_listeners)
            if week_listeners > 0:
                ratio = week_streams / week_listeners
                weekly_metrics.append(ratio)
        
        avg_weekly_streams_per_listener = sum(weekly_metrics) / len(weekly_metrics) if weekly_metrics else 0
        avg_weekly_listeners = sum(weekly_listeners) / len(weekly_listeners) if weekly_listeners else 0
        
        # Calculate peak to total ratio
        peak_to_total_ratio = (peak_streams / total_streams * 100) if total_streams > 0 else 0
        
        # Calculate retention rate (cities that streamed in last 4 weeks / cities that ever streamed)
        last_4_weeks = song_data[song_data['week'] >= latest_week - pd.Timedelta(weeks=4)]
        retained_cities = last_4_weeks[last_4_weeks['current_period'] > 0]['city'].nunique()
        retention_rate = (retained_cities / active_cities * 100) if active_cities > 0 else 0
        
        # Calculate average streams per active city
        avg_streams_per_city = total_streams / active_cities if active_cities > 0 else 0
        
        # Determine if still growing
        is_still_growing = (peak_date == latest_week) and (latest_week <= release_date + pd.Timedelta(weeks=12))
        weeks_to_peak = (peak_date - release_date).days / 7 if not is_still_growing else None
        
        # Add to song metrics list
        song_adoption_list.append({
            'song': song,
            'release_date': release_date.strftime('%Y-%m-%d'),
            'peak_date': peak_date.strftime('%Y-%m-%d'),
            'peak_streams': peak_streams,
            'weeks_to_peak': round(weeks_to_peak, 1) if weeks_to_peak is not None else None,
            'weeks_to_adopt': round(weeks_to_adopt, 1) if weeks_to_adopt is not None else None,
            'is_still_growing': is_still_growing,
            'peaked_first_week': weeks_to_peak == 0 if weeks_to_peak is not None else False,
            'total_streams': total_streams,
            'peak_weekly_listeners': peak_weekly_listeners,
            'avg_weekly_listeners': round(avg_weekly_listeners, 1),
            'avg_weekly_streams_per_listener': round(avg_weekly_streams_per_listener, 1),
            'total_cities': total_cities,
            'active_cities': active_cities,
            'avg_streams_per_city': round(avg_streams_per_city, 1),
            'peak_to_total_ratio': round(peak_to_total_ratio, 1),
            'retention_rate': round(retention_rate, 1)
        })
    
    # Create DataFrame from list
    song_adoption_metrics = pd.DataFrame(song_adoption_list)
    
    # Categorize songs based on adoption speed
    percentile_33 = song_adoption_metrics['weeks_to_adopt'].quantile(0.33)
    percentile_67 = song_adoption_metrics['weeks_to_adopt'].quantile(0.67)
    
    def categorize_song(row):
        if row['weeks_to_adopt'] <= percentile_33:
            return 'Quick Adopter'
        elif row['weeks_to_adopt'] <= percentile_67:
            return 'Mid Adopter'
        else:
            return 'Slow Adopter'
    
    song_adoption_metrics['adoption_category'] = song_adoption_metrics.apply(categorize_song, axis=1)
    
    # Print the results
    print("\nSong Performance Summary (First 12 Weeks After Release):")
    print("=" * 80)
    # Select and reorder columns for display
    display_columns = [
        'song', 'release_date', 'peak_date', 'peak_streams', 'total_streams',
        'active_cities', 'avg_streams_per_city', 'avg_weekly_streams_per_listener',
        'peak_to_total_ratio', 'retention_rate', 'adoption_category'
    ]
    print(song_adoption_metrics[display_columns].to_string(index=False))
    
    # Print interpretation of metrics
    print("\nInterpretation Notes:")
    print("- All metrics are calculated using only the first 12 weeks after release for each song")
    print("- peak_streams: Highest number of streams in a single week")
    print("- total_streams: Total streams in first 12 weeks")
    print("- peak_weekly_listeners: Highest number of listeners in any single week")
    print("- avg_weekly_listeners: Average number of listeners per week")
    print("- active_cities: Number of cities that have streamed the song")
    print("- avg_streams_per_city: Average streams per active city")
    print("- avg_weekly_streams_per_listener: Average of (streams/listeners) for each week")
    print("- peak_to_total_ratio: Percentage of total streams that occurred at peak")
    print("- retention_rate: Percentage of cities that streamed in last 4 weeks")
    print("- adoption_category: Song's adoption pattern (Quick Adopter, Mid Adopter, Slow Adopter)")
    
    print("\nAvailable DataFrame for Further Analysis:")
    print("- song_adoption_metrics: Song-level metrics including adoption patterns and peak behavior")
    print("  • Contains: song details, adoption timing, peak behavior, and engagement stats")
    
    # Add a log-transformed color column
    song_adoption_metrics['log_total_streams'] = np.log10(song_adoption_metrics['total_streams'] + 1)

    fig = px.scatter(
        song_adoption_metrics,
        x='retention_rate',
        y='avg_weekly_streams_per_listener',
        color='log_total_streams',
        hover_name='song',
        custom_data=['weeks_to_adopt', 'total_streams', 'adoption_category', 'active_cities', 'peak_to_total_ratio'],
        color_continuous_scale=px.colors.sequential.Viridis,
        title='Song Performance: Retention vs Listener Engagement'
    )

    # Set colorbar ticks to show original values
    fig.update_layout(
        coloraxis_colorbar=dict(
            title='Total Streams',
            tickvals=[np.log10(x) for x in [100, 1000, 10000, 100000]],
            ticktext=[f'{x:,}' for x in [100, 1000, 10000, 100000]],
            tickfont=dict(size=16),
            title_font=dict(size=18)
        ),
        xaxis_title='Retention Rate (%)',
        yaxis_title='Average Streams per Listener',
        height=800,
        showlegend=False,
        xaxis=dict(tickfont=dict(size=16), title_font=dict(size=18)),
        yaxis=dict(tickfont=dict(size=16), title_font=dict(size=18))
    )

    # Update marker size and style
    fig.update_traces(
        marker=dict(
            size=15,
            line=dict(width=1, color='white')
        )
    )

    # Add hover template
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" +
                     "Retention Rate: %{x:.1f}%<br>" +
                     "Avg Streams per Listener: %{y:.1f}<br>" +
                     "Total Streams: %{customdata[1]:,.0f}<br>" +
                     "Peak to Total Ratio: %{customdata[4]:.1f}%<br>" +
                     "Active Cities: %{customdata[3]}<br>" +
                     "Category: %{customdata[2]}<extra></extra>"
    )
    
    # Show the plot
    fig.show()
    
    # Return the DataFrame without displaying it
    return song_adoption_metrics.copy()

if __name__ == "__main__":
    analyze_peaks()
    analyze_song_adoption() 