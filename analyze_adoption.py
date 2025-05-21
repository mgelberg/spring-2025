import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def load_data():
    # Load and filter the data
    df = pd.read_csv('data/song_velocity_table.csv')
    
    # Filter out monthly data (filenames with 'monthly' in them)
    df = df[~df['Song'].str.contains('artist level', case=False, na=False)]
    
    # Filter out artist level data
    df = df[df['Grouping'] == 'city']
    
    return df

def analyze_adoption_patterns():
    # Load the data
    df = load_data()
    
    # Convert Week to datetime
    df['Week'] = pd.to_datetime(df['Week'])
    
    # Initialize DataFrame to store city adoption metrics
    city_adoption = pd.DataFrame()
    
    # Get first activity date for each song (this will be treated as release date)
    song_release_dates = df[df['Current Period'] > 0].groupby('Song')['Week'].min()
    
    print(f"\nAnalyzing {len(song_release_dates)} songs")
    print("\nSongs being analyzed:")
    for song in song_release_dates.index:
        print(f"- {song}")
    
    for city in df['City'].unique():
        if city == 'All Cities':  # Skip aggregate data
            continue
            
        city_data = df[df['City'] == city]
        
        # Analyze adoption for each song
        for song in df['Song'].unique():
            song_city_data = city_data[city_data['Song'] == song]
            
            if song_city_data.empty:
                continue
                
            release_date = song_release_dates[song]
            
            # Find first activity for this city and song
            song_city_activity = song_city_data[song_city_data['Current Period'] > 0]
            if song_city_activity.empty:
                continue
                
            first_activity = song_city_activity['Week'].min()
            last_activity = song_city_activity['Week'].max()
            
            # Calculate weeks from release to first activity
            weeks_to_adopt = (first_activity - release_date).days / 7
            
            # Calculate active weeks and total weeks since adoption
            active_weeks = song_city_activity['Week'].nunique()
            total_weeks = (last_activity - first_activity).days / 7 + 1 if first_activity else 0
            
            # Calculate engagement metrics
            total_streams = song_city_data[song_city_data['Measure'].str.lower() == 'plays']['Current Period'].sum()
            total_listeners = song_city_data[song_city_data['Measure'].str.lower() == 'listeners']['Current Period'].sum()
            
            # Calculate consistency score
            consistency = (active_weeks / total_weeks) * 100 if total_weeks > 0 else 0
            
            # Add to city_adoption DataFrame
            city_adoption = pd.concat([city_adoption, pd.DataFrame({
                'City': [city],
                'Song': [song],
                'Release Date': [release_date],
                'First Activity': [first_activity],
                'Weeks to Adopt': [weeks_to_adopt],
                'Total Streams': [total_streams],
                'Total Listeners': [total_listeners],
                'Active Weeks': [active_weeks],
                'Consistency Score': [consistency]
            })], ignore_index=True)
    
    # Calculate average adoption speed and consistency for each city across all songs
    city_summary = city_adoption.groupby('City').agg({
        'Weeks to Adopt': 'mean',
        'Consistency Score': 'mean',
        'Total Streams': 'sum',
        'Total Listeners': 'sum',
        'Song': 'count'  # Count how many songs each city engaged with
    }).reset_index()
    
    # Rename the song count column
    city_summary = city_summary.rename(columns={'Song': 'Songs Engaged'})
    
    # Categorize cities based on average adoption speed
    percentile_33 = city_summary['Weeks to Adopt'].quantile(0.33)
    percentile_67 = city_summary['Weeks to Adopt'].quantile(0.67)
    
    def categorize_city(row):
        if row['Weeks to Adopt'] <= percentile_33:
            return 'Early Adopter'
        elif row['Weeks to Adopt'] <= percentile_67:
            return 'Mid Adopter'
        else:
            return 'Late Bloomer'
    
    city_summary['Category'] = city_summary.apply(categorize_city, axis=1)
    
    # Create visualization
    plt.figure(figsize=(15, 8))
    
    # Create scatter plot
    scatter = sns.scatterplot(data=city_summary, 
                   x='Weeks to Adopt', 
                   y='Consistency Score',
                   hue='Category',
                   size='Songs Engaged',  # Changed from Total Streams to Songs Engaged
                   sizes=(50, 400),
                   alpha=0.6)
    
    plt.title('City Adoption Patterns: Average Time to Adopt vs Consistency')
    plt.xlabel('Average Weeks Until First Activity (After Song Release)')
    plt.ylabel('Average Consistency Score (%)')
    plt.legend(title='Adoption Category', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add city labels for points with high engagement
    for idx, row in city_summary[city_summary['Songs Engaged'] >= city_summary['Songs Engaged'].quantile(0.75)].iterrows():
        scatter.text(row['Weeks to Adopt'], row['Consistency Score'], row['City'], 
                    fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\nAdoption Pattern Analysis (Relative to Song Release Dates)")
    print("=" * 80)
    
    # Print song release dates first
    print("\nSong Release Dates:")
    print("-" * 40)
    for song, release_date in song_release_dates.items():
        print(f"{song}: {release_date.strftime('%Y-%m-%d')}")
    
    for category in ['Early Adopter', 'Mid Adopter', 'Late Bloomer']:
        category_cities = city_summary[city_summary['Category'] == category]
        print(f"\n{category} Cities:")
        print("-" * 40)
        
        # Sort by combination of song engagement and consistency
        category_cities['Overall Score'] = (
            category_cities['Songs Engaged'] * 0.5 + 
            category_cities['Consistency Score'] * 0.5
        )
        top_cities = category_cities.nlargest(5, 'Overall Score')
        
        for _, city in top_cities.iterrows():
            print(f"\nCity: {city['City']}")
            print(f"Songs Engaged With: {city['Songs Engaged']}")
            print(f"Average Weeks to Adopt: {city['Weeks to Adopt']:.1f}")
            print(f"Average Consistency Score: {city['Consistency Score']:.1f}%")
            print(f"Total Streams: {city['Total Streams']}")
            print(f"Total Listeners: {city['Total Listeners']}")
            
            # Show song-specific adoption patterns for this city
            city_songs = city_adoption[city_adoption['City'] == city['City']]
            print("\nSong-specific adoption:")
            for _, song_data in city_songs.iterrows():
                print(f"  {song_data['Song']}: {song_data['Weeks to Adopt']:.1f} weeks after release")
    
    # Additional insights
    print("\nKey Insights:")
    print("-" * 40)
    
    # Calculate average metrics by category
    category_metrics = city_summary.groupby('Category').agg({
        'Total Streams': 'mean',
        'Total Listeners': 'mean',
        'Consistency Score': 'mean',
        'Weeks to Adopt': 'mean',
        'Songs Engaged': 'mean',
        'City': 'count'
    }).round(2)
    
    for category in ['Early Adopter', 'Mid Adopter', 'Late Bloomer']:
        metrics = category_metrics.loc[category]
        print(f"\n{category}s ({metrics['City']} cities):")
        print(f"Average Songs Engaged: {metrics['Songs Engaged']:.1f}")
        print(f"Average Weeks to Adopt: {metrics['Weeks to Adopt']:.1f}")
        print(f"Average Streams: {metrics['Total Streams']:.1f}")
        print(f"Average Listeners: {metrics['Total Listeners']:.1f}")
        print(f"Average Consistency: {metrics['Consistency Score']:.1f}%")

if __name__ == "__main__":
    analyze_adoption_patterns() 