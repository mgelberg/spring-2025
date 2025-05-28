import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plot_utils import (
    plot_city_trends,
    complete_timeseries_data,
    calculate_streams_per_listener
)
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
        
        # Calculate weekly streams per listener for the city using the standardized function
        city_data = pd.concat([city_streams, city_listeners])
        ratio_df = calculate_streams_per_listener(city_data, level='song')
        avg_weekly_streams_per_listener = ratio_df['streams_per_listener'].mean() if not ratio_df.empty else 0
        
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
    
    # Ensure measure values are lowercase
    df['measure'] = df['measure'].str.lower()
    
    # Filter for weekly data only
    weekly_mask = df['period_type'].str.lower() == 'weekly'
    df = df[weekly_mask].copy()
    
    # Convert week to datetime
    df['week'] = pd.to_datetime(df['week'].astype(str), format='%Y%m%d')
    
    # Base filter for song-level data only (no artist level)
    song_filter = (df['level'].str.lower() == 'song')
    
    # Get streams data
    streams_mask = (df['measure'] == 'plays') & song_filter
    streams_data = df[streams_mask].copy()
    
    # Get listeners data - ensure we're using song-level data only
    listeners_mask = (df['measure'] == 'listeners') & song_filter
    listeners_data = df[listeners_mask].copy()
    
    return streams_data, listeners_data

def analyze_peaks_by_city(df=None, include_artist_level=False):
    """
    Analyze and visualize peak and adoption metrics for individual cities.
    Only considers the first 12 weeks after release for each song.
    Excludes 'All Cities' aggregate data to focus on city-specific patterns.
    
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
        - song_metrics: DataFrame with individual song-level metrics per city
        - category_metrics: DataFrame with category-level summary statistics
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                df = __main__.df
            else:
                df = load_and_prepare_data()
        except Exception as e:
            df = load_and_prepare_data()
    
    # Prepare data for analysis
    streams_data, listeners_data = prepare_weekly_song_data(df, include_artist_level)
    
    # Filter out 'All Cities' data for city-specific analysis
    streams_data = streams_data[streams_data['city'].str.lower() != 'all cities'].copy()
    listeners_data = listeners_data[listeners_data['city'].str.lower() != 'all cities'].copy()
    
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
    
    # Print summary of metrics and their definitions
    print("\nCity Performance Summary (First 12 Weeks After Release):")
    print("=" * 80)
    print("\nKey Metrics:")
    print("- avg_weeks_to_peak: Average number of weeks until peak streaming activity")
    print("- peak_streams: Highest number of streams in a single week")
    print("- peak_weekly_listeners: Highest number of listeners in any single week")
    print("- songs_analyzed: Number of songs analyzed for this city")
    print("- songs_peaked_first_week: Number of songs that peaked in their first week")
    print("- pct_peaked_first_week: Percentage of songs that peaked in their first week")
    print("- songs_still_growing: Number of songs still growing after 12 weeks")
    print("- total_streams: Total streams across all songs")
    print("- consistency_score: Percentage of songs that were streamed in last 4 weeks")
    print("- avg_weekly_streams_per_listener: Average of (streams/listeners) for each week")
    print("- avg_weeks_to_adopt: Average number of weeks until first streaming activity")
    print("\nCity Categories:")
    print("- Early Adopter: Cities that start streaming within the first 33rd percentile of weeks")
    print("- Mid Adopter: Cities that start streaming between 33rd and 67th percentile of weeks")
    print("- Late Bloomer: Cities that start streaming after the 67th percentile of weeks")
    
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
    
    return city_metrics.copy(), song_metrics.copy(), category_metrics.copy()

def analyze_song_adoption_overall(df=None, include_artist_level=False):
    """
    Analyze and visualize overall song adoption patterns across all cities.
    Only considers the first 12 weeks after release for each song.
    Uses 'All Cities' aggregate data to understand overall song performance.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
    include_artist_level : bool, default False
        Whether to include artist-level data in the analysis
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with song-level adoption metrics
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                df = __main__.df
            else:
                df = load_and_prepare_data()
        except Exception as e:
            df = load_and_prepare_data()
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Prepare data for analysis
    streams_data, listeners_data = prepare_weekly_song_data(df, include_artist_level)
    
    if streams_data.empty:
        return pd.DataFrame()
    
    # Initialize list for song adoption metrics
    song_adoption_list = []
    
    # Calculate metrics for each song
    for song in streams_data['song'].unique():
        # Get data for all cities - ensure we're only getting song-level data
        all_cities_data = df[
            (df['song'] == song) & 
            (df['city'].str.lower() == 'all cities') & 
            (df['measure'] == 'plays') &
            (df['level'].str.lower() == 'song')  # Only song-level data
        ].copy()
        
        if all_cities_data.empty:
            continue
            
        # Get song ID and release date
        song_id = all_cities_data['song_id'].iloc[0]
        release_date = get_song_release_date(song_id)
        if release_date is None:
            continue
        
        # Filter to only include first 12 weeks after release
        all_cities_data['week'] = pd.to_datetime(all_cities_data['week'].astype(str), format='%Y%m%d')
        
        # Convert release_date to pandas Timestamp if it's not already
        if not isinstance(release_date, pd.Timestamp):
            release_date = pd.Timestamp(release_date)
        
        # Calculate the cutoff date
        cutoff_date = release_date + pd.Timedelta(weeks=12)
        
        # Filter data to only include first 12 weeks after release
        filtered_data = all_cities_data[all_cities_data['week'] <= cutoff_date]
        
        if filtered_data.empty:
            continue
        
        all_cities_data = filtered_data
        
        # Get listener data for this song (All Cities) - ensure song-level data only
        all_cities_listener_data = df[
            (df['song'] == song) & 
            (df['city'].str.lower() == 'all cities') & 
            (df['measure'] == 'listeners') &
            (df['level'].str.lower() == 'song')  # Only song-level data
        ].copy()
        all_cities_listener_data['week'] = pd.to_datetime(all_cities_listener_data['week'].astype(str), format='%Y%m%d')
        all_cities_listener_data = all_cities_listener_data[all_cities_listener_data['week'] <= cutoff_date]
        
        # Calculate peak metrics
        peak_date = all_cities_data.loc[all_cities_data['current_period'].idxmax()]['week']
        peak_streams = all_cities_data['current_period'].max()
        latest_week = all_cities_data['week'].max()
        
        # Calculate adoption metrics
        first_activity = all_cities_data[all_cities_data['current_period'] > 0]['week'].min()
        weeks_to_adopt = (first_activity - release_date).days / 7 if first_activity else None
        
        # Calculate engagement metrics
        total_streams = all_cities_data['current_period'].sum()
        avg_weekly_streams = total_streams / len(all_cities_data) if not all_cities_data.empty else 0
        
        # Get city-level data for reference
        city_data = streams_data[streams_data['song'] == song].copy()
        city_data = city_data[city_data['week'] <= release_date + pd.Timedelta(weeks=12)]
        total_cities = city_data['city'].nunique()
        active_cities = city_data[city_data['current_period'] > 0]['city'].nunique()
        
        # Get listener data for this song (All Cities)
        all_cities_listener_data = df[
            (df['song'] == song) & 
            (df['city'].str.lower() == 'all cities') & 
            (df['measure'] == 'listeners') &
            (df['level'].str.lower() == 'song')
        ].copy()
        all_cities_listener_data['week'] = pd.to_datetime(all_cities_listener_data['week'].astype(str), format='%Y%m%d')
        all_cities_listener_data = all_cities_listener_data[all_cities_listener_data['week'] <= release_date + pd.Timedelta(weeks=12)]
        peak_weekly_listeners = all_cities_listener_data['current_period'].max() if not all_cities_listener_data.empty else 0
        avg_weekly_listeners = all_cities_listener_data['current_period'].mean() if not all_cities_listener_data.empty else 0
        
        # Calculate weekly streams per listener
        weekly_streams_per_listener = []
        
        for week in all_cities_data['week'].unique():
            week_streams = all_cities_data[all_cities_data['week'] == week]['current_period'].iloc[0]
            week_listeners = 0
            
            # Check if we have listener data for this week
            listener_week_data = all_cities_listener_data[all_cities_listener_data['week'] == week]
            if not listener_week_data.empty:
                week_listeners = listener_week_data['current_period'].iloc[0]
            
            if week_listeners > 0:
                ratio = week_streams / week_listeners
                weekly_streams_per_listener.append(ratio)
        
        # Calculate average of weekly streams per listener
        avg_weekly_streams_per_listener = sum(weekly_streams_per_listener) / len(weekly_streams_per_listener) if weekly_streams_per_listener else 0
        
        # Calculate peak to total ratio
        peak_to_total_ratio = (peak_streams / total_streams * 100) if total_streams > 0 else 0
        
        # Calculate consistency score (cities that streamed in last 4 weeks / cities that ever streamed)
        last_4_weeks = city_data[city_data['week'] >= latest_week - pd.Timedelta(weeks=4)]
        retained_cities = last_4_weeks[last_4_weeks['current_period'] > 0]['city'].nunique()
        consistency_score = (retained_cities / active_cities * 100) if active_cities > 0 else 0
        
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
            'avg_weekly_streams': round(avg_weekly_streams, 1),
            'peak_weekly_listeners': peak_weekly_listeners,
            'avg_weekly_listeners': round(avg_weekly_listeners, 1),
            'avg_weekly_streams_per_listener': round(avg_weekly_streams_per_listener, 1),
            'total_cities': total_cities,
            'active_cities': active_cities,
            'avg_streams_per_city': round(avg_streams_per_city, 1),
            'peak_to_total_ratio': round(peak_to_total_ratio, 1),
            'consistency_score': round(consistency_score, 1)
        })
    
    # Create DataFrame from list
    song_adoption_metrics = pd.DataFrame(song_adoption_list)
    
    if song_adoption_metrics.empty:
        return song_adoption_metrics
    
    # Categorize songs based on adoption speed or consistency
    if 'weeks_to_adopt' in song_adoption_metrics.columns and not song_adoption_metrics['weeks_to_adopt'].isna().all():
        percentile_33 = song_adoption_metrics['weeks_to_adopt'].quantile(0.33)
        percentile_67 = song_adoption_metrics['weeks_to_adopt'].quantile(0.67)
        
        def categorize_song(row):
            if pd.isna(row['weeks_to_adopt']):
                return 'Unknown'
            if row['weeks_to_adopt'] <= percentile_33:
                return 'Early Adopter'
            elif row['weeks_to_adopt'] <= percentile_67:
                return 'Mid Adopter'
            else:
                return 'Late Bloomer'
        
        song_adoption_metrics['adoption_category'] = song_adoption_metrics.apply(categorize_song, axis=1)
    elif 'consistency_score' in song_adoption_metrics.columns and not song_adoption_metrics['consistency_score'].isna().all():
        percentile_33 = song_adoption_metrics['consistency_score'].quantile(0.33)
        percentile_67 = song_adoption_metrics['consistency_score'].quantile(0.67)
        
        def categorize_song(row):
            if pd.isna(row['consistency_score']):
                return 'Unknown'
            if row['consistency_score'] <= percentile_33:
                return 'Low Consistency'
            elif row['consistency_score'] <= percentile_67:
                return 'Medium Consistency'
            else:
                return 'High Consistency'
        
        song_adoption_metrics['adoption_category'] = song_adoption_metrics.apply(categorize_song, axis=1)
    else:
        # If neither metric is available, categorize based on total streams
        if 'total_streams' in song_adoption_metrics.columns:
            percentile_33 = song_adoption_metrics['total_streams'].quantile(0.33)
            percentile_67 = song_adoption_metrics['total_streams'].quantile(0.67)
            
            def categorize_song(row):
                if pd.isna(row['total_streams']):
                    return 'Unknown'
                if row['total_streams'] <= percentile_33:
                    return 'Low Volume'
                elif row['total_streams'] <= percentile_67:
                    return 'Medium Volume'
                else:
                    return 'High Volume'
            
            song_adoption_metrics['adoption_category'] = song_adoption_metrics.apply(categorize_song, axis=1)
        else:
            # If no metrics are available, set all to Unknown
            song_adoption_metrics['adoption_category'] = 'Unknown'
    
    # Print summary of metrics and their definitions
    print("\nSong Performance Summary (First 12 Weeks After Release):")
    print("=" * 80)
    print("\nKey Metrics:")
    print("- peak_streams: Highest number of streams in a single week")
    print("- total_streams: Total streams in first 12 weeks")
    print("- avg_weekly_streams: Average streams per week")
    print("- peak_weekly_listeners: Highest number of listeners in any single week")
    print("- avg_weekly_listeners: Average number of listeners per week")
    print("- active_cities: Number of cities that have streamed the song")
    print("- avg_streams_per_city: Average streams per active city")
    print("- avg_weekly_streams_per_listener: Average of (streams/listeners) for each week")
    print("- peak_to_total_ratio: Percentage of total streams that occurred at peak")
    print("- consistency_score: Percentage of cities that streamed in last 4 weeks")
    print("- weeks_to_peak: Number of weeks until peak streaming activity")
    print("- weeks_to_adopt: Number of weeks until first streaming activity")
    print("\nAdoption Categories:")
    print("- Early Adopter: Songs that start streaming within the first 33rd percentile of weeks")
    print("- Mid Adopter: Songs that start streaming between 33rd and 67th percentile of weeks")
    print("- Late Bloomer: Songs that start streaming after the 67th percentile of weeks")
    print("\nConsistency Categories:")
    print("- High Consistency: Songs with consistency scores above the 67th percentile")
    print("- Medium Consistency: Songs with consistency scores between 33rd and 67th percentile")
    print("- Low Consistency: Songs with consistency scores below the 33rd percentile")
    print("\nVolume Categories:")
    print("- High Volume: Songs with total streams above the 67th percentile")
    print("- Medium Volume: Songs with total streams between 33rd and 67th percentile")
    print("- Low Volume: Songs with total streams below the 33rd percentile")
    
    # Add a log-transformed color column if total_streams exists
    if 'total_streams' in song_adoption_metrics.columns:
        song_adoption_metrics['log_total_streams'] = np.log10(song_adoption_metrics['total_streams'] + 1)
        
        # Only create the plot if we have the required columns
        if all(col in song_adoption_metrics.columns for col in ['consistency_score', 'avg_weekly_streams_per_listener']):
            # Calculate weeks since release for each song
            current_date = pd.Timestamp.now()
            song_adoption_metrics['weeks_since_release'] = song_adoption_metrics.apply(
                lambda row: (current_date - pd.Timestamp(row['release_date'])).days / 7, 
                axis=1
            ).round(1)
            
            fig = px.scatter(
                song_adoption_metrics,
                x='consistency_score',
                y='avg_weekly_streams_per_listener',
                color='log_total_streams',
                hover_name='song',
                custom_data=['weeks_since_release', 'total_streams', 'adoption_category', 'active_cities', 'peak_to_total_ratio'],
                color_continuous_scale=px.colors.sequential.Viridis,
                title='Song Performance: Consistency vs Listener Engagement'
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
                xaxis_title='Consistency Score (%)',
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
                             "Consistency Score: %{x:.1f}%<br>" +
                             "Avg Weekly Streams per Listener: %{y:.1f}<br>" +
                             "Total Streams: %{customdata[1]:,.0f}<br>" +
                             "Peak to Total Ratio: %{customdata[4]:.1f}%<br>" +
                             "Active Cities: %{customdata[3]}<br>" +
                             "Weeks Since Release: %{customdata[0]:.1f}<br>" +
                             "Category: %{customdata[2]}<extra></extra>"
            )
            
            # Show the plot
            fig.show()
    
    return song_adoption_metrics.copy()

def calculate_stickiness_metrics(df=None, min_streams_threshold=1):
    """
    Calculate stickiness metrics (WAU/MAU) for songs over time.
    Focuses exclusively on unique listeners (not streams).
    Only considers first 12 weeks after release and excludes incomplete months.
    
    Stickiness is defined as:
    - WAU: Number of unique listeners in a given week
    - MAU: Number of unique listeners in the month containing that week
    - Stickiness Ratio: (WAU/MAU) * 100
    
    A higher stickiness ratio indicates better retention, as it means a larger portion
    of monthly listeners are also active in the current week.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
    min_streams_threshold : int, default 1
        Minimum number of streams required to count a user as active (not used, kept for compatibility)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with stickiness metrics over time (listeners only)
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                df = __main__.df
            else:
                df = load_and_prepare_data()
        except Exception as e:
            df = load_and_prepare_data()
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Ensure all column names are lowercase
    df.columns = df.columns.str.lower()
    
    # Determine top 5 cities by avg monthly listeners at the ARTIST level
    if df is not None:
        # Filter for artist-level monthly listeners data
        artist_monthly_df = df[
            (df['level'].str.lower() == 'artist') &
            (df['measure'].str.lower() == 'listeners') &
            (df['period_type'].str.lower() == 'monthly') &
            (df['city'].str.lower() != 'all cities')
        ].copy()
        
        # Calculate average monthly listeners per city
        city_avg_mau = (
            artist_monthly_df
            .groupby('city')['current_period']
            .mean()
            .sort_values(ascending=False)
        )
        
        # Get top 5 cities
        top_cities = city_avg_mau.head(5).index.tolist()
        print("\nTop 5 Cities by Average Monthly Listeners (Artist Level):")
        for city, avg in city_avg_mau.head(5).items():
            print(f"- {city}: {avg:.0f} listeners")
    else:
        top_cities = []
    
    city_options = ['All Cities'] + top_cities
    print(f"\nCity options for dropdown: {city_options}")
    
    # Filter for song level only
    song_mask = df['level'].str.lower() == 'song'
    df = df[song_mask].copy()
    
    # Convert week to datetime
    df['week'] = pd.to_datetime(df['week'].astype(str), format='%Y%m%d')
    
    # Get current date and first day of current month
    current_date = pd.Timestamp.now()
    current_month_start = current_date.replace(day=1)
    
    # Initialize results list
    stickiness_list = []
    
    # Calculate metrics for each song
    for song in df['song'].unique():
        song_data = df[df['song'] == song].copy()
        # Get song ID and release date
        song_id = song_data['song_id'].iloc[0]
        release_date = get_song_release_date(song_id)
        if release_date is None:
            continue
        # Calculate cutoff date (12 weeks after release)
        cutoff_date = release_date + pd.Timedelta(weeks=12)
        # Get weekly data for this song
        weekly_data = song_data[
            (song_data['period_type'].str.lower() == 'weekly') & 
            (song_data['week'] >= release_date) &
            (song_data['week'] <= cutoff_date)
        ].copy()
        # Get monthly data for this song (do NOT filter by release_date)
        monthly_data = song_data[
            (song_data['period_type'].str.lower() == 'monthly')
        ].copy()
        if weekly_data.empty or monthly_data.empty:
            continue
        # Calculate metrics for each week
        for week in weekly_data['week'].unique():
            # Get the month containing this week
            month_start = week.replace(day=1)
            month_end = (month_start + pd.offsets.MonthEnd(0))
            # Skip if this month is incomplete (current month)
            if month_start >= current_month_start:
                continue
            # Get WAU data for this week
            wau_data = weekly_data[weekly_data['week'] == week]
            # Get MAU data for the month containing this week (match by year and month)
            mau_data = monthly_data[
                (monthly_data['week'].dt.year == week.year) &
                (monthly_data['week'].dt.month == week.month)
            ]
            if wau_data.empty or mau_data.empty:
                continue
            # Calculate metrics for each city (including 'All Cities')
            for city in wau_data['city'].unique():
                # Get city WAU data
                city_wau_data = wau_data[wau_data['city'] == city]
                city_wau_listeners = city_wau_data[city_wau_data['measure'] == 'listeners']['current_period'].sum()
                # Get city MAU data (always include the month containing the week, even if release is mid-month)
                city_mau_data = mau_data[mau_data['city'] == city]
                city_mau_listeners = city_mau_data[city_mau_data['measure'] == 'listeners']['current_period'].sum()
                # Calculate stickiness ratio
                stickiness_ratio = (city_wau_listeners / city_mau_listeners * 100) if city_mau_listeners > 0 else 0
                # Add to stickiness list
                stickiness_list.append({
                    'song': song,
                    'city': city,
                    'week': week,
                    'wau_listeners': city_wau_listeners,
                    'mau_listeners': city_mau_listeners,
                    'stickiness_ratio': round(stickiness_ratio, 1),
                    'release_date': release_date.strftime('%Y-%m-%d'),
                    'weeks_since_release': round((week - release_date).days / 7, 1)
                })
    
    # Create DataFrame from list
    stickiness_df = pd.DataFrame(stickiness_list)
    
    if stickiness_df.empty:
        return stickiness_df
    
    # Print summary of metrics
    print("\nStickiness Metrics Summary (First 12 Weeks After Release):")
    print("=" * 80)
    print("\nKey Metrics:")
    print("- WAU (Weekly Active Users): Number of unique listeners in a given week")
    print("- MAU (Monthly Active Users): Number of unique listeners in the month containing that week")
    print("- Stickiness Ratio: (WAU/MAU) * 100 - Higher ratio indicates better retention")
    print("  (e.g., 50% means half of monthly listeners were active in the current week)")
    print("\nNote: Analysis limited to first 12 weeks after release and excludes incomplete months")
    
    # --- HEATMAP VISUALIZATION ---
    all_weeks = np.arange(1, 13)
    all_songs = stickiness_df['song'].unique()
    
    # Prepare heatmap data for each city option
    heatmap_data_dict = {}
    for city in city_options:
        city_df = stickiness_df[stickiness_df['city'] == city]
        heatmap_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='stickiness_ratio',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        # Also store WAU/MAU for hover
        wau_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='wau_listeners',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        mau_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='mau_listeners',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        heatmap_data_dict[city] = (heatmap_data, wau_data, mau_data)
    # Default to 'All Cities'
    default_city = 'All Cities'
    z = heatmap_data_dict[default_city][0].values
    customdata = np.stack([
        heatmap_data_dict[default_city][1].values,  # WAU
        heatmap_data_dict[default_city][2].values   # MAU
    ], axis=-1)
    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=z,
            x=all_weeks,
            y=all_songs,
            customdata=customdata,
            colorscale='Viridis',
            colorbar=dict(title='Stickiness Ratio (%)'),
            hovertemplate=(
                'Song: %{y}<br>'
                'Weeks Since Release: %{x}<br>'
                'WAU: %{customdata[0]:.0f}<br>'
                'MAU: %{customdata[1]:.0f}<br>'
                'Stickiness Ratio: %{z:.1f}%<extra></extra>'
            )
        )
    )
    # Add dropdown for city selection
    buttons = []
    for city in city_options:
        z = heatmap_data_dict[city][0].values
        customdata = np.stack([
            heatmap_data_dict[city][1].values,
            heatmap_data_dict[city][2].values
        ], axis=-1)
        buttons.append(dict(
            label=city,
            method='restyle',
            args=[{'z': [z], 'customdata': [customdata]}]
        ))
    fig_heatmap.update_layout(
        updatemenus=[dict(
            buttons=buttons,
            direction='down',
            showactive=True,
            x=1.15,
            xanchor='left',
            y=1,
            yanchor='top',
            pad={'r': 10, 't': 10}
        )],
        xaxis_title='Weeks Since Release',
        yaxis_title='Song',
        height=600,
        title='Stickiness Ratio Heatmap (Song vs. Weeks Since Release)'
    )
    fig_heatmap.show()

    # --- SUMMARY STATISTICS TABLE ---
    summary_stats = (
        stickiness_df.groupby('song')['stickiness_ratio']
        .agg(['mean', 'median', 'min', 'max', 'std'])
        .round(2)
        .reset_index()
    )
    table_fig = go.Figure(
        data=[go.Table(
            header=dict(values=list(summary_stats.columns), fill_color='paleturquoise', align='left'),
            cells=dict(values=[summary_stats[col] for col in summary_stats.columns], fill_color='lavender', align='left')
        )]
    )
    table_fig.update_layout(title='Stickiness Ratio Summary Statistics (First 12 Weeks)')
    table_fig.show()

    return stickiness_df.copy()

def calculate_song_to_artist_ratio(df=None):
    """
    Calculate and visualize the percentage of artist-level listeners that are listening to each song.
    Shows what portion of the artist's total audience is engaging with each song on a weekly basis.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with song-to-artist listener ratios over time
    """
    # Check if we already have a DataFrame in the notebook context
    if df is None:
        try:
            import __main__
            if hasattr(__main__, 'df') and isinstance(__main__.df, pd.DataFrame):
                df = __main__.df
            else:
                df = load_and_prepare_data()
        except Exception as e:
            df = load_and_prepare_data()
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Ensure all column names are lowercase
    df.columns = df.columns.str.lower()
    
    # Determine top 5 cities by avg monthly listeners at the ARTIST level
    if df is not None:
        # Filter for artist-level monthly listeners data
        artist_monthly_df = df[
            (df['level'].str.lower() == 'artist') &
            (df['measure'].str.lower() == 'listeners') &
            (df['period_type'].str.lower() == 'monthly') &
            (df['city'].str.lower() != 'all cities')
        ].copy()
        
        # Calculate average monthly listeners per city
        city_avg_mau = (
            artist_monthly_df
            .groupby('city')['current_period']
            .mean()
            .sort_values(ascending=False)
        )
        
        # Get top 5 cities
        top_cities = city_avg_mau.head(5).index.tolist()
        print("\nTop 5 Cities by Average Monthly Listeners (Artist Level):")
        for city, avg in city_avg_mau.head(5).items():
            print(f"- {city}: {avg:.0f} listeners")
    else:
        top_cities = []
    
    city_options = ['All Cities'] + top_cities
    print(f"\nCity options for dropdown: {city_options}")

    # Convert week to datetime
    df['week'] = pd.to_datetime(df['week'].astype(str), format='%Y%m%d')
    
    # Initialize results list
    ratio_list = []
    
    # Get unique songs (song level only)
    songs = df[df['level'].str.lower() == 'song']['song'].unique()
    print(f"\nFound {len(songs)} unique songs")
    
    # Ensure week column is datetime (already in ISO format)
    df['week'] = pd.to_datetime(df['week'])
    print("\nDate range in data:")
    print(f"Earliest date: {df['week'].min()}")
    print(f"Latest date: {df['week'].max()}")
    
    # Calculate metrics for each song
    for song in songs:
        song_data = df[df['song'] == song].copy()
        # Get song ID and release date
        song_id = song_data['song_id'].iloc[0]
        release_date = get_song_release_date(song_id)
        if release_date is None:
            print(f"Skipping {song} - no release date found")
            continue
            
        # Convert release_date to pandas Timestamp if it's not already
        if not isinstance(release_date, pd.Timestamp):
            release_date = pd.Timestamp(release_date)
            
        # Calculate cutoff date (12 weeks after release)
        cutoff_date = release_date + pd.Timedelta(weeks=12)
        
        print(f"\nProcessing {song}")
        print(f"Release date: {release_date}")
        print(f"Cutoff date: {cutoff_date}")
        
        # Get weekly data for this song
        weekly_song_data = song_data[
            (song_data['period_type'].str.lower() == 'weekly') & 
            (song_data['measure'].str.lower() == 'listeners') &
            (song_data['level'].str.lower() == 'song') &
            (song_data['week'] >= release_date) &
            (song_data['week'] <= cutoff_date)
        ].copy()
        
        # Get weekly artist data for the same period
        print(f"\nProcessing {song}")
        print(f"Release date: {release_date}")
        print(f"Cutoff date: {cutoff_date}")
        
        weekly_artist_data = df[
            (df['period_type'].str.lower() == 'weekly') & 
            (df['measure'].str.lower() == 'listeners') &
            (df['level'].str.lower() == 'artist') &
            (df['week'] >= release_date) &
            (df['week'] <= cutoff_date)
        ].copy()
        
        print(f"Found {len(weekly_song_data)} song data points")
        print(f"Found {len(weekly_artist_data)} artist data points")
        
        if weekly_song_data.empty or weekly_artist_data.empty:
            print(f"Skipping {song} - missing song or artist data")
            continue
            
        # Calculate metrics for each week
        for week in weekly_song_data['week'].unique():
            # Get song listeners for this week
            week_song_data = weekly_song_data[weekly_song_data['week'] == week]
            
            # Get artist listeners for this week
            week_artist_data = weekly_artist_data[weekly_artist_data['week'] == week]
            
            if week_song_data.empty or week_artist_data.empty:
                continue
                
            # Calculate ratio for each city
            for city in week_song_data['city'].unique():
                # Get city song listeners
                city_song_data = week_song_data[week_song_data['city'] == city]
                song_listeners = city_song_data['current_period'].sum()
                
                # Get city artist listeners
                city_artist_data = week_artist_data[week_artist_data['city'] == city]
                artist_listeners = city_artist_data['current_period'].sum()
                
                # Calculate ratio
                listener_ratio = (song_listeners / artist_listeners * 100) if artist_listeners > 0 else 0
                
                # Add to ratio list
                ratio_list.append({
                    'song': song,
                    'city': city,
                    'week': week,
                    'song_listeners': song_listeners,
                    'artist_listeners': artist_listeners,
                    'listener_ratio': round(listener_ratio, 1),
                    'release_date': release_date.strftime('%Y-%m-%d'),
                    'weeks_since_release': round((week - release_date).days / 7, 1)
                })
    
    # Create DataFrame from list
    ratio_df = pd.DataFrame(ratio_list)
    
    if ratio_df.empty:
        return ratio_df
    
    # Print summary of metrics
    print("\nSong-to-Artist Listener Ratio Summary (First 12 Weeks After Release):")
    print("=" * 80)
    print("\nKey Metrics:")
    print("- Song Listeners: Number of unique listeners for the song in a given week")
    print("- Artist Listeners: Number of unique listeners for the artist in that week")
    print("- Listener Ratio: (Song Listeners / Artist Listeners) * 100")
    print("  (e.g., 50% means half of the artist's listeners are listening to this song)")
    
    # --- HEATMAP VISUALIZATION ---
    all_weeks = np.arange(1, 13)
    all_songs = ratio_df['song'].unique()
    
    # Prepare heatmap data for each city option
    heatmap_data_dict = {}
    for city in city_options:
        city_df = ratio_df[ratio_df['city'] == city]
        heatmap_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='listener_ratio',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        # Also store song/artist listeners for hover
        song_listeners_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='song_listeners',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        artist_listeners_data = city_df.pivot_table(
            index='song',
            columns='weeks_since_release',
            values='artist_listeners',
            aggfunc='mean'
        ).reindex(index=all_songs, columns=all_weeks)
        heatmap_data_dict[city] = (heatmap_data, song_listeners_data, artist_listeners_data)
    
    # Default to 'All Cities'
    default_city = 'All Cities'
    z = heatmap_data_dict[default_city][0].values
    customdata = np.stack([
        heatmap_data_dict[default_city][1].values,  # Song Listeners
        heatmap_data_dict[default_city][2].values   # Artist Listeners
    ], axis=-1)
    
    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=z,
            x=all_weeks,
            y=all_songs,
            customdata=customdata,
            colorscale='Viridis',
            colorbar=dict(title='Listener Ratio (%)'),
            hovertemplate=(
                'Song: %{y}<br>'
                'Weeks Since Release: %{x}<br>'
                'Song Listeners: %{customdata[0]:.0f}<br>'
                'Artist Listeners: %{customdata[1]:.0f}<br>'
                'Listener Ratio: %{z:.1f}%<extra></extra>'
            )
        )
    )
    
    # Add dropdown for city selection
    buttons = []
    for city in city_options:
        z = heatmap_data_dict[city][0].values
        customdata = np.stack([
            heatmap_data_dict[city][1].values,
            heatmap_data_dict[city][2].values
        ], axis=-1)
        buttons.append(dict(
            label=city,
            method='restyle',
            args=[{'z': [z], 'customdata': [customdata]}]
        ))
    
    fig_heatmap.update_layout(
        updatemenus=[dict(
            buttons=buttons,
            direction='down',
            showactive=True,
            x=1.15,
            xanchor='left',
            y=1,
            yanchor='top',
            pad={'r': 10, 't': 10}
        )],
        xaxis_title='Weeks Since Release',
        yaxis_title='Song',
        height=600,
        title='Song-to-Artist Listener Ratio Heatmap'
    )
    
    fig_heatmap.show()
    
    # --- SUMMARY STATISTICS TABLE ---
    summary_stats = (
        ratio_df.groupby('song')['listener_ratio']
        .agg(['mean', 'median', 'min', 'max', 'std'])
        .round(2)
        .reset_index()
    )
    
    table_fig = go.Figure(
        data=[go.Table(
            header=dict(values=list(summary_stats.columns), fill_color='paleturquoise', align='left'),
            cells=dict(values=[summary_stats[col] for col in summary_stats.columns], fill_color='lavender', align='left')
        )]
    )
    table_fig.update_layout(title='Song-to-Artist Listener Ratio Summary Statistics (First 12 Weeks)')
    table_fig.show()
    
    return ratio_df.copy()

if __name__ == "__main__":
    analyze_peaks_by_city()
    analyze_song_adoption_overall()
    calculate_stickiness_metrics()
    calculate_song_to_artist_ratio() 