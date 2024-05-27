from flask import Flask, render_template_string
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Initialize Flask app
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Function to read and analyze web server log data
def analyze_logs():
    # Read web server log data from CSV file
    log_data = pd.read_csv('web_server_logs_updated.csv')

    # Ensure necessary columns are present
    required_columns = ['Timestamp', 'IP', 'Request', 'Status', 'Age', 'Gender', 'Country', 'City', 'Sport','Count']
    if not all(column in log_data.columns for column in required_columns):
        raise ValueError("Missing required columns in the log data.")

    # Filter out rows with missing data
    log_data.dropna(subset=required_columns, inplace=True)

    return log_data

# Analyze logs
log_data = analyze_logs()

# Calculate required metrics
total_visits = len(log_data)
unique_visitors = log_data['IP'].nunique()
demographics = log_data.groupby(['Age', 'Gender']).size().reset_index(name='Count')
geographic_distribution = log_data.groupby(['Country', 'City']).size().reset_index(name='Count')
sport_popularity = log_data['Sport'].value_counts()

# Create the Dash layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("PARIS METRICS 2024-Fun Olympic Games", className="text-left"), className="mb-5 mt-5")
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='status-chart'), width=6),
        dbc.Col(dcc.Graph(id='country-chart'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='sport-chart'), width=6),
        dbc.Col(dcc.Graph(id='gender-chart'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='age-chart'), width=6),
        dbc.Col(dcc.Graph(id='continent-chart'), width=6)
    ]),
    
], fluid=True)

# Define the callbacks for interactive charts
@app.callback(
    [Output('status-chart', 'figure'),
     Output('country-chart', 'figure'),
     Output('sport-chart', 'figure'),
     Output('gender-chart', 'figure'),
     Output('age-chart', 'figure'),
     Output('continent-chart', 'figure')],
    [Input('status-chart', 'id')]
)
def update_charts(_):
    status_counts = log_data['Status'].value_counts()
    country_counts = log_data['Country'].value_counts()
    sport_counts = log_data['Sport'].value_counts()
    gender_counts = log_data['Gender'].value_counts()
    age_counts = log_data['Age'].value_counts()

    # Group by continent (using Country as a proxy, you may need to map countries to continents)
    log_data['Continent'] = log_data['Country'].map({
        'USA': 'North America',
        'Canada': 'North America',
        'Brazil': 'South America',
        'UK': 'Europe',
        'Germany': 'Europe',
        'China': 'Asia',
        'India': 'Asia',
        'Australia': 'Australia',
        'South Africa': 'Africa'
        # Add more mappings as needed
    })

    # Recreate continent_counts to ensure 'Count' column exists
    continent_counts = log_data.groupby('Continent').size().reset_index(name='Count')

    # Create figures
    status_chart = px.pie(values=status_counts.values, names=status_counts.index, title='Status Code Distribution')
    country_chart = px.bar(x=country_counts.index, y=country_counts.values, title='Visits by Country')
    sport_chart = px.bar(x=sport_counts.index, y=sport_counts.values, title='Sport Popularity')
    gender_chart = px.pie(values=gender_counts.values, names=gender_counts.index, title='Gender Distribution')
    age_chart = px.bar(x=age_counts.index, y=age_counts.values, title='Age Demographics')

    # Use the new continent_counts DataFrame for the scatter_geo plot
    continent_chart = px.scatter_geo(log_data, locations="Country", locationmode='country names', 
                                     size="Count", color="Continent", hover_name="City",
                                     title='Geographic Distribution by Continent',
                                     projection='natural earth')
    

    return status_chart, country_chart, sport_chart, gender_chart, age_chart, continent_chart,

# Define route to render index.html with Dash
@server.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>PARIS METRICS 2024-Fun Olympic Games</title>
            <link rel="stylesheet" href="style.css">
        </head>
        <body>
            <div class="container">
                <h1 class="text-center mt-5 mb-5">PARIS METRICS 2024-Fun Olympic Games</h1>
                <div id="dash-container"></div>
            </div>
            <!-- Include Dash assets -->
            {% for css in dash_assets_css %}
                <link rel="stylesheet" href="{{ css }}">
            {% endfor %}
            {% for js in dash_assets_js %}
                <script src="{{ js }}"></script>
            {% endfor %}
            {% for js in dash_scripts %}
                <script src="{{ js }}"></script>
            {% endfor %}
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run_server(debug=True)
