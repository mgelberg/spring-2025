# %%
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# %%
# Function to load and combine all CSV files
def load_all_data():
    # Find all CSV files in the current directory
    csv_files = glob.glob('*_by_city_*.csv')
    
    # Load and combine all files
    all_data = []
    for file in csv_files:
        df = pd.read_csv(file)
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)

# %%
# Load the data
df = load_all_data()
print(f"Total rows: {len(df)}")
df.head()

# %%
# Basic statistics
print("\nSummary Statistics:")
print(df.describe())

# %%
# Top cities by plays
top_cities = df.groupby('City')['Current Period'].sum().sort_values(ascending=False).head(10)
print("\nTop 10 Cities by Plays:")
print(top_cities)

# %%
# Plot top cities
plt.figure(figsize=(12, 6))
top_cities.plot(kind='bar')
plt.title('Top 10 Cities by Plays')
plt.ylabel('Total Plays')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %%
# Growth analysis
df['Growth'] = (df['Current Period'] - df['Previous Period']) / df['Previous Period'] * 100
top_growth = df[df['Previous Period'] > 100].nlargest(10, 'Growth')
print("\nTop 10 Cities by Growth Rate:")
print(top_growth[['City', 'Growth', 'Current Period', 'Previous Period']])

# %%
# Plot growth
plt.figure(figsize=(12, 6))
top_growth.set_index('City')['Growth'].plot(kind='bar')
plt.title('Top 10 Cities by Growth Rate')
plt.ylabel('Growth Rate (%)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show() 